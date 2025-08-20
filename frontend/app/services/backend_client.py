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
            # Placeholder until backend endpoint exists
            # Future: POST /api/sessions to create one, store id
            self.session_id = "local-dev"
        return self.session_id

    def post_transcript(self, text: str) -> None:
        self.ensure_session()
        # Placeholder for POST /api/transcripts
        # requests.post(f"{self.base_url}/api/transcripts", json={"session_id": self.session_id, "text": text})
        return None

    def generate_answer(self, prompt: str, persona_id: Optional[int]) -> str:
        self.ensure_session()
        # Placeholder for POST /api/generate-answer
        # r = requests.post(f"{self.base_url}/api/generate-answer", json={"session_id": self.session_id, "persona_id": persona_id, "prompt": prompt}, timeout=60)
        # r.raise_for_status()
        # return r.json().get("answer", "")
        return "[Simulated] Thanks! Backend API will return a styled answer here."
