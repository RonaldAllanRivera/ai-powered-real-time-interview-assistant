# AI-Powered Real-Time Interview Assistant

A fast, local-first interview assistant with:
- Live transcript from system audio (Zoom, Google Meet, YouTube, etc.)
- One-click AI answer suggestions in your saved style/persona
- Always-on-top window (no tray icon, no stealth mode)
- One-click copy
- Learns from corrections
- Persistent Q&A + transcripts (MySQL by default; SQLite supported)

Tech stack:
- Backend: Laravel (API, OpenAI gateway)
- Frontend: Python (PySide6 desktop app)
- Storage: MySQL (SQLite optional)

## Architecture
- `backend/` Laravel API: personas, style profiles, sessions, transcripts, Q&A, corrections. Calls OpenAI for answer generation.
- `frontend/` Python desktop app: captures system audio, transcribes in near real-time, displays an always-on-top window (no tray icon/stealth overlay), calls backend APIs, stores corrections.

Data model (current):
- `personas`: name, description, system_prompt
- `transcript_chunks`: session_id (indexed), text, source, timestamps
- `qa_entries`: session_id (indexed), persona_id (indexed, nullable), question, ai_answer, final_answer, timestamps
- `interview_infos`: session_id (unique), company, role, context, timestamps

## Prerequisites
- Windows (Laragon friendly)
- PHP 8.2+, Composer
- Python 3.10+
- OpenAI API key

## Fast setup

1) Backend (Laravel + MySQL)
- Copy `backend/.env.example` to `backend/.env` and set:
  - `DB_CONNECTION=mysql`
  - `DB_HOST=127.0.0.1`
  - `DB_PORT=3306`
  - `DB_DATABASE=your_db`
  - `DB_USERNAME=your_user`
  - `DB_PASSWORD=your_pass`
- Also set `OPENAI_API_KEY`.
- From `backend/` run:
  - `composer install`
  - `php artisan key:generate`
  - `php artisan migrate --seed`

2) Frontend (Python)
- Create a venv in `frontend/.venv` and install deps from `frontend/requirements.txt`.
- Copy `frontend/.env.example` to `frontend/.env` and set `BACKEND_BASE_URL` (default `http://127.0.0.1:8000`).

## Commands
Backend
```powershell
cd backend
php artisan serve --host 127.0.0.1 --port 8000
```

Frontend
```powershell
# Create venv
if (Get-Command py -ErrorAction SilentlyContinue) { py -3 -m venv frontend\.venv } else { python -m venv frontend\.venv }

# Upgrade pip and install deps
frontend\.venv\Scripts\python -m pip install -U pip
frontend\.venv\Scripts\pip install -r frontend\requirements.txt

# Run the app
frontend\.venv\Scripts\python -m frontend.app.main
```

## Usage
- Start the backend server.
- Run the desktop app. Choose a persona, start live transcript, and press Submit to request an AI answer.
- Copy answer with one click.
- The window stays on top; no tray icon or stealth overlay.
- In simulation mode, lines keep coming until you press Stop or close the app (stop is instant).

## Personas
- Direct & Technical (Truthful): Focused, honest, and technical. States what you have and haven’t done; mentions close alternatives you’ve actually used.
- Structured & Example-Driven: Organizes into clear points and cites specific projects/outcomes.
- Polished & Professional: Confident, client-facing tone; closes with alignment to role/company values.

The persona help icon next to the selector shows each persona’s description and the exact AI prompt used.

## Notes on audio capture
- The frontend will attempt WASAPI loopback on Windows to capture system audio. If not available or packages missing, it falls back to a simulation so the UI still works. Install the dependencies to enable real capture.
  - The simulator now stops immediately when you press Stop.

## Security
- The backend reads `OPENAI_API_KEY` from `backend/.env`. Keep it server-side. The frontend does not require an OpenAI key.

## AI model
- Default: `gpt-4o-mini` (fast and cost-efficient).
- Change it in `backend/app/Services/OpenAIService.php` in `generateAnswer()` (both the SDK and HTTP paths).
- Optional future improvement: make it configurable via `OPENAI_MODEL` env.

## Roadmap (next steps)
- Implement real-time transcription via Whisper or faster-whisper with VAD.
- Personas CRUD; corrections capture and learning loop to adapt prompts.
- Streamed responses; retry/backoff and better error UX.
- Automated tests for API and UI.

## Contributing
- PRs welcome. Please follow conventional commits in messages (we’ll add commit templates later).
