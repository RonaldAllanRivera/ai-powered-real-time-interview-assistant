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

    def generate_answer(self, prompt: str, persona_id: Optional[int], model: Optional[str] = None) -> str:
        sid = self.ensure_session()
        try:
            r = requests.post(
                f"{self.base_url}/api/generate-answer",
                json={"session_id": sid, "persona_id": persona_id, "prompt": prompt, "model": model},
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("answer", "") or ""
        except Exception:
            return ""

    # Personas
    def get_personas(self):
        try:
            r = requests.get(f"{self.base_url}/api/personas", timeout=10)
            r.raise_for_status()
            return r.json().get("personas", [])
        except Exception:
            return []

    # Interview info
    def get_interview_info(self):
        sid = self.ensure_session()
        try:
            r = requests.get(f"{self.base_url}/api/interview-info", params={"session_id": sid}, timeout=10)
            r.raise_for_status()
            return r.json().get("interview_info")
        except Exception:
            return None

    def upsert_interview_info(self, company: Optional[str], role: Optional[str], context: Optional[str]):
        sid = self.ensure_session()
        try:
            r = requests.post(
                f"{self.base_url}/api/interview-info",
                json={
                    "session_id": sid,
                    "company": company or None,
                    "role": role or None,
                    "context": context or None,
                },
                timeout=15,
            )
            r.raise_for_status()
            return True
        except Exception:
            return False
