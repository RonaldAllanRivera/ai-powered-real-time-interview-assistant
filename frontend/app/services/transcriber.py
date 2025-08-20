import os
import threading
import time
from typing import Optional

from PySide6.QtCore import QThread, Signal


class TranscriberThread(QThread):
    transcriptReady = Signal(str)

    def __init__(self):
        super().__init__()
        self._stop = threading.Event()

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
        """Minimal simulation so the app is runnable even without audio deps.
        Replace with real WASAPI loopback capture + VAD in a follow-up.
        """
        try:
            # Attempt to load optional deps (won't be used in this stub)
            import soundcard  # noqa: F401
            import webrtcvad   # noqa: F401
            have_audio = True
        except Exception:
            have_audio = False

        if not have_audio:
            # Simulate transcript lines every second
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

        # Placeholder: if audio deps present, still simulate for now
        while not self._stop.is_set():
            self.transcriptReady.emit("[Audio Ready] Implement capture in next step.")
            if self._wait_interruptible(1.0):
                return
