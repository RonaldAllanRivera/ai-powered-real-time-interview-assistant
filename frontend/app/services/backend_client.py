import os
import time
from typing import Optional

import requests


class BackendClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session_id: Optional[str] = None

    def ensure_session(self):
        if not self.session_id:
            # TODO: switch to POST /api/sessions when implemented
            self.session_id = "local-dev"
        return self.session_id

    def post_transcript(self, text: str) -> None:
        sid = self.ensure_session()
        try:
            requests.post(
                f"{self.base_url}/api/transcripts",
                json={"session_id": sid, "text": text, "source": "system"},
                timeout=10,
            )
        except Exception:
            pass

    def generate_answer(self, prompt: str, persona_id: Optional[int]) -> str:
        sid = self.ensure_session()
        try:
            r = requests.post(
                f"{self.base_url}/api/generate-answer",
                json={"session_id": sid, "persona_id": persona_id, "prompt": prompt},
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("answer", "") or ""
        except Exception:
            return ""
