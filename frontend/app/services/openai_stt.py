import os
from typing import Optional

try:
    from openai import OpenAI
    from openai.types.audio import Transcription
except Exception:  # pragma: no cover - optional at start
    OpenAI = None  # type: ignore
    Transcription = None  # type: ignore


def transcribe_wav_bytes(wav_bytes: bytes) -> str:
    """Send audio bytes to OpenAI Whisper and return text. Requires OPENAI_API_KEY.
    This is a thin stub; real-time chunking handled elsewhere.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not OpenAI:
        return ""
    client = OpenAI(api_key=api_key)
    try:
        # Using the new API signature with InputFile is recommended, but keeping it simple here
        from openai import Audio
        # Fallback path: the SDK may change; keeping a minimal safe path
        # This call may need updating depending on SDK version.
        result = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=("chunk.wav", wav_bytes, "audio/wav"),
        )
        # result.text for newer SDKs
        text = getattr(result, "text", None)
        if isinstance(text, str):
            return text
        # Some versions return a dict-like
        return str(result)
    except Exception:
        return ""
