# AI-Powered Real-Time Interview Assistant

A fast, local-first interview assistant with:
- Live transcript from system audio (Zoom, Google Meet, YouTube, etc.)
- One-click AI answer suggestions in your saved style/persona
- Always-on-top window (no tray icon, no stealth mode)
- One-click copy
- Learns from corrections
- Persistent Q&A + transcripts (SQLite by default)

Tech stack:
- Backend: Laravel (API, SQLite, OpenAI gateway)
- Frontend: Python (PySide6 desktop app)
- Storage: SQLite (optionally MySQL if needed later for scale)

## Architecture
- `backend/` Laravel API: personas, style profiles, sessions, transcripts, Q&A, corrections. Calls OpenAI for answer generation.
- `frontend/` Python desktop app: captures system audio, transcribes in near real-time, displays an always-on-top window (no tray icon/stealth overlay), calls backend APIs, stores corrections.

Data model (initial cut):
- `personas`: name, description, style_profile_id
- `style_profiles`: tone, writing_guidelines, few_shot_examples (JSON)
- `sessions`: id, started_at, ended_at
- `transcript_chunks`: session_id, text, started_at, ended_at, source
- `qa_entries`: session_id, persona_id, question, ai_answer, final_answer, created_at
- `corrections`: qa_entry_id, before_text, after_text, notes

## Prerequisites
- Windows (Laragon friendly)
- PHP 8.2+, Composer
- Python 3.10+
- OpenAI API key

## Fast setup

1) Backend (Laravel)
- We’ll install Laravel into `backend/`, configure SQLite, and add an `OPENAI_API_KEY` placeholder.
- Approve the install command when prompted.

2) Frontend (Python)
- A virtualenv will be created in `frontend/.venv` and dependencies installed from `frontend/requirements.txt`.

3) Environment
- Backend: set `OPENAI_API_KEY` in `backend/.env`.
- Frontend: copy `frontend/.env.example` to `frontend/.env` and set `BACKEND_BASE_URL`.

## Commands

Backend (Proposed; will prompt for approval):
- composer create-project laravel/laravel:^12 backend
- Copy .env, key:generate, create SQLite file, set DB_CONNECTION=sqlite

Start backend dev server:
```powershell
php backend\artisan serve --host 127.0.0.1 --port 8000
```

Frontend (Proposed; will prompt for approval):
```powershell
# Create venv
if (Get-Command py -ErrorAction SilentlyContinue) { py -3 -m venv frontend\.venv } else { python -m venv frontend\.venv }

# Upgrade pip and install deps
frontend\.venv\Scripts\python -m pip install -U pip
frontend\.venv\Scripts\pip install -r frontend\requirements.txt

# Run the app
frontend\.venv\Scripts\python frontend\app\main.py
```

## Usage
- Start the backend server.
- Run the desktop app. Choose a persona, start live transcript, and press Submit to request an AI answer.
- Copy answer with one click.
- The window stays on top; no tray icon or stealth overlay.
- In simulation mode, lines keep coming until you press Stop or close the app.

## Notes on audio capture
- The frontend will attempt WASAPI loopback on Windows to capture system audio. If not available or packages missing, it falls back to a simulation so the UI still works. Install the dependencies to enable real capture.
  - In simulation mode, stop is checked roughly every 1.2s, so you may see one extra line after pressing Stop.

## Security
- The backend reads `OPENAI_API_KEY` from `backend/.env`. Keep it server-side. The frontend does not require an OpenAI key.

## Roadmap (next steps)
- Implement real-time chunk transcription via OpenAI Whisper or local faster-whisper with VAD.
- Backend APIs: personas CRUD, transcripts ingest, generate answer, corrections.
- Learning loop: aggregate corrections to update style profile and system prompt automatically.
- Optional MySQL migration for scale.

## Contributing
- PRs welcome. Please follow conventional commits in messages (we’ll add commit templates later).
