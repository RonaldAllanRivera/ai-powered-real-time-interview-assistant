import os
import threading
import time
from typing import Optional, List

import numpy as np
from PySide6.QtCore import QThread, Signal

# NumPy 2.x compatibility: some dependencies still call np.fromstring in binary mode,
# which was removed in NumPy 2.x. Patch to transparently use frombuffer for bytes.
try:
    _np_fromstring_orig = np.fromstring  # type: ignore[attr-defined]
    def _np_fromstring_compat(string, dtype=float, count=-1, sep=""):
        try:
            return _np_fromstring_orig(string, dtype=dtype, count=count, sep=sep)
        except ValueError as ex:
            # NumPy 2.x removed binary mode; transparently use frombuffer when possible
            msg = str(ex).lower()
            if "fromstring" in msg and "frombuffer" in msg and (sep == "" or sep is None):
                try:
                    # Works for any object exposing the buffer protocol (bytes, bytearray,
                    # memoryview, cffi buffers, etc.)
                    return np.frombuffer(string, dtype=dtype, count=count)
                except Exception:
                    # Try via memoryview (some buffer-like objects prefer explicit view)
                    try:
                        mv = memoryview(string)
                        return np.frombuffer(mv, dtype=dtype, count=count)
                    except Exception:
                        # As a last resort, materialize to bytes (extra copy, but robust)
                        try:
                            b = bytes(string)
                            return np.frombuffer(b, dtype=dtype, count=count)
                        except Exception:
                            pass
            raise
    np.fromstring = _np_fromstring_compat  # type: ignore[assignment]
except Exception:
    pass


def _downsample_mono_48k_to_16k(x: np.ndarray) -> np.ndarray:
    """Downsample 48k float32 mono [-1,1] to 16k float32 by simple decimation.
    Assumes len divisible by 3; otherwise trims the remainder.
    """
    if x.ndim > 1:
        x = x.mean(axis=1)
    n = (x.shape[0] // 3) * 3
    if n <= 0:
        return np.empty((0,), dtype=np.float32)
    y = x[:n].reshape(-1, 3).mean(axis=1)
    return y.astype(np.float32, copy=False)


def _float32_to_pcm16(x: np.ndarray) -> bytes:
    x = np.clip(x, -1.0, 1.0)
    x = (x * 32767.0).astype(np.int16)
    return x.tobytes()


def _resample_linear(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    """Simple linear resampler to sr_out. x is 1D float32 in [-1,1]."""
    if sr_in == sr_out or x.size == 0:
        return x.astype(np.float32, copy=False)
    # Generate output time indices
    duration = x.shape[0] / float(sr_in)
    n_out = max(1, int(round(duration * sr_out)))
    xp = np.linspace(0.0, duration, num=x.shape[0], endpoint=False, dtype=np.float64)
    fp = x.astype(np.float32, copy=False)
    x_new = np.linspace(0.0, duration, num=n_out, endpoint=False, dtype=np.float64)
    y = np.interp(x_new, xp, fp).astype(np.float32, copy=False)
    return y


class _WhisperSTT:
    def __init__(self):
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except Exception:
            self.model = None
            return
        # Choose a small, fast, free model
        model_name = os.getenv("WHISPER_MODEL", "tiny.en")
        try:
            # Use CPU-friendly compute type
            self.model = WhisperModel(model_name, device="cpu", compute_type="int8")
        except Exception:
            self.model = None

    def available(self) -> bool:
        return self.model is not None

    def transcribe(self, audio_16k_f32: np.ndarray) -> str:
        if not self.model or audio_16k_f32.size == 0:
            return ""
        try:
            segments, _ = self.model.transcribe(audio_16k_f32, language="en")
            texts: List[str] = []
            for seg in segments:
                t = getattr(seg, "text", "")
                if t:
                    texts.append(t.strip())
            return " ".join(texts).strip()
        except Exception:
            return ""


class TranscriberThread(QThread):
    transcriptReady = Signal(str)

    def __init__(self, device_name: Optional[str] = None, vad_level: int = 2):
        super().__init__()
        self._stop = threading.Event()
        self.device_name = device_name
        self.vad_level = max(0, min(3, int(vad_level)))

    def stop(self):
        self._stop.set()

    def _wait_interruptible(self, seconds: float) -> bool:
        """Wait up to `seconds` but return early if stop is set.
        Returns True if stop was requested; False otherwise.
        """
        remaining = max(0.0, float(seconds))
        tick = 0.1
        while remaining > 0:
            if self._stop.wait(min(tick, remaining)):
                return True
            remaining -= tick
        return False

    def run(self):
        # Imports guarded to keep app runnable without extra deps
        try:
            import soundcard as sc
        except Exception:
            sc = None  # type: ignore
        try:
            import webrtcvad  # type: ignore
        except Exception:
            webrtcvad = None  # type: ignore

        # If no audio lib, keep legacy simulation so app still works
        if sc is None:
            samples = [
                "[Simulated] Interviewer: Tell me about yourself.",
                "[Simulated] Interviewer: How do you handle tight deadlines?",
                "[Simulated] Interviewer: Describe a challenging project.",
            ]
            i = 0
            while not self._stop.is_set():
                self.transcriptReady.emit(samples[i % len(samples)])
                i += 1
                if self._wait_interruptible(1.2):
                    return
            return

        # Resolve device (loopback microphone)
        mic = None
        try:
            mics = sc.all_microphones(include_loopback=True)
            if self.device_name:
                dn = self.device_name.lower()
                for m in mics:
                    if dn in m.name.lower() or m.name.lower() in dn:
                        mic = m
                        break
            if mic is None and mics:
                loopbacks = [m for m in mics if getattr(m, "isloopback", False)]
                mic = (loopbacks[0] if loopbacks else mics[0])
        except Exception:
            mic = None

        if mic is None:
            # Audio libs present but no device found
            while not self._stop.is_set():
                self.transcriptReady.emit("[Audio Ready] No loopback device found. Check device selection.")
                if self._wait_interruptible(1.0):
                    return
            return

        # Initialize optional VAD and STT
        vad = None
        if webrtcvad is not None:
            try:
                vad = webrtcvad.Vad(self.vad_level)
            except Exception:
                vad = None
        stt = _WhisperSTT()

        # Capture and segment to speech chunks at 16 kHz
        frame_ms = 30  # 30ms frames for VAD
        sr_target = 16000
        seg_active = False
        speech_frames_16k: List[np.ndarray] = []
        non_speech_count = 0
        start_speech_margin = 3  # ~90ms
        end_speech_margin = 8    # ~240ms
        consecutive_speech = 0

        try:
            # Try multiple samplerates for compatibility
            candidates = []
            try:
                default_sr = int(getattr(mic, "default_samplerate", 0))
            except Exception:
                default_sr = 0
            if default_sr:
                candidates.append(default_sr)
            candidates += [48000, 44100, 32000, 16000]
            # dedupe while preserving order
            sr_candidates: List[int] = []
            for s in candidates:
                if s and s not in sr_candidates:
                    sr_candidates.append(s)
            last_err = None
            opened = False
            for sr_in in sr_candidates:
                try:
                    with mic.recorder(samplerate=sr_in) as rec:
                        samples_per_chunk = int(sr_in * (frame_ms / 1000.0))
                        # Announce capture start and capabilities
                        vad_mode = f"WebRTC({self.vad_level})" if vad is not None else "energy"
                        stt_mode = "faster-whisper" if stt.available() else "(no STT)"
                        is_lb = getattr(mic, "isloopback", None)
                        self.transcriptReady.emit(f"[Audio] Capturing from '{mic.name}' (loopback={is_lb}) @ {sr_in} Hz | VAD: {vad_mode} | STT: {stt_mode}")
                        while not self._stop.is_set():
                            block = rec.record(samples_per_chunk)  # typically shape (N, C)
                            if block.size == 0:
                                continue
                            # Mix to mono robustly (handle 1D or 2D input), then downsample/resample to 16k
                            if getattr(block, "ndim", 1) == 1:
                                mono_48k = block.astype(np.float32, copy=False)
                            else:
                                mono_48k = block.mean(axis=1).astype(np.float32, copy=False)
                            if sr_in == 48000:
                                mono_16k = _downsample_mono_48k_to_16k(mono_48k)
                            else:
                                mono_16k = _resample_linear(mono_48k, sr_in=sr_in, sr_out=sr_target)
                            if mono_16k.size == 0:
                                continue
                            
                            # VAD decision
                            is_speech = False
                            if vad is not None:
                                pcm = _float32_to_pcm16(mono_16k)
                                # 30ms at 16k is 480 samples
                                # mono_16k may be 480 samples due to decimation of a 30ms 48k block -> 10ms; to keep logic simple, we group to ~30ms by buffering 3 frames
                                # Here, operate per-block as approximation
                                try:
                                    is_speech = vad.is_speech(pcm, 16000)
                                except Exception:
                                    is_speech = False
                            else:
                                # Simple energy-based fallback
                                rms = float(np.sqrt(np.mean(mono_16k**2)))
                                is_speech = rms > 0.01
                            
                            if is_speech:
                                consecutive_speech += 1
                                non_speech_count = 0
                                if not seg_active and consecutive_speech >= start_speech_margin:
                                    seg_active = True
                                    speech_frames_16k = []
                                if seg_active:
                                    speech_frames_16k.append(mono_16k)
                            else:
                                consecutive_speech = 0
                                if seg_active:
                                    non_speech_count += 1
                                    if non_speech_count >= end_speech_margin:
                                        # finalize segment
                                        seg_active = False
                                        non_speech_count = 0
                                        audio = np.concatenate(speech_frames_16k) if speech_frames_16k else np.empty((0,), dtype=np.float32)
                                        text = ""
                                        if stt.available():
                                            text = stt.transcribe(audio)
                                        if not text:
                                            dur = audio.shape[0] / 16000.0 if audio.size else 0.0
                                            text = f"[Audio segment ~{dur:.1f}s]"
                                        self.transcriptReady.emit(text)
                                        speech_frames_16k = []
                        opened = True
                    break
                except Exception as e_open:
                    last_err = e_open
                    continue
            if not opened:
                raise last_err or RuntimeError("No supported samplerate for recorder")
        except Exception as e:
            # Log details to console to aid debugging, and show the error class/message in UI
            try:
                import sys, traceback
                print("[Transcriber] Audio capture error:", repr(e), file=sys.stderr)
                traceback.print_exc()
            except Exception:
                pass
            while not self._stop.is_set():
                self.transcriptReady.emit(f"[Audio capture error] {e.__class__.__name__}: {e}")
                if self._wait_interruptible(2.0):
                    return
