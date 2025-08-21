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

# Optional local STT and VAD (recommended)
# Use prebuilt wheels to avoid MSVC toolchain on Windows
frontend\.venv\Scripts\pip install faster-whisper webrtcvad-wheels

# Run the app
frontend\.venv\Scripts\python -m frontend.app.main
```

## Usage
- Start the backend server.
- Run the desktop app. Choose a persona, start live transcript, and press Submit to request an AI answer.
- Copy answer with one click.
- The window stays on top; no tray icon or stealth overlay.
- In simulation mode, lines keep coming until you press Stop or close the app (stop is instant).

### Live transcript controls
- **Start/Stop Transcript**: begins/stops capturing system audio.
- **Capture Device**: pick the WASAPI loopback device (e.g., your speakers or meeting app). Use the reload icon to refresh.
- **Reset Transcript**: clears only the visible transcript (DB history remains). This also resets the prompt dedupe.
- **Clear after answer**: if checked (default), the transcript view auto-clears after an AI answer is returned.

## Personas
- Direct & Technical (Truthful): Focused, honest, and technical. States what you have and haven’t done; mentions close alternatives you’ve actually used.
- Structured & Example-Driven: Organizes into clear points and cites specific projects/outcomes.
- Polished & Professional: Confident, client-facing tone; closes with alignment to role/company values.

The persona help icon next to the selector shows each persona’s description and the exact AI prompt used.

## Audio capture and transcription
- The frontend uses **WASAPI loopback** via `soundcard` to capture system audio (Zoom/Meet/YouTube/etc.).
- Optional **VAD** using `webrtcvad` (aggressiveness 0–3; default 2). If `webrtcvad` isn't installed, an energy-based fallback is used.
- Optional on-device **STT** using `faster-whisper`. If not installed, segments are emitted with timestamps as placeholders.

- Probes multiple input sample rates (device default, 48000, 44100, 32000, 16000) and resamples to 16 kHz for VAD/STT.
- On start, the transcript shows a status line like: `[Audio] Capturing from 'Speakers (Realtek…)'
  (loopback=True) @ 48000 Hz | VAD: WebRTC(2) | STT: faster-whisper`.
- Includes a built-in compatibility shim for NumPy 2.x to transparently redirect deprecated binary `np.fromstring` calls to `np.frombuffer` inside dependencies.
- First run of STT may download the Whisper model specified by `WHISPER_MODEL` (e.g., `tiny.en`).

### Dependencies
- Required: `soundcard`, `numpy` (already listed in `frontend/requirements.txt`).
- Optional: `webrtcvad` (may require MSVC on Windows), `faster-whisper`.
  - To enable local STT, install `faster-whisper` and set `WHISPER_MODEL` (e.g., `tiny.en`).

### Device selection
- Use the "Capture Device" dropdown to choose a loopback device. If none appear, click refresh.
- If no devices are found, the app shows a status message. The simulator is used only when audio dependencies are missing.

__System audio vs app-specific audio__
- Loopback captures everything routed to the chosen output device. To capture "all system audio", set that device as Windows default output or route apps in Settings → System → Sound → App volume and device preferences.
- To mix multiple outputs, use a virtual mixer (e.g., VB-Audio VoiceMeeter) and select its loopback.

__List available devices (PowerShell)__
```powershell
frontend\.venv\Scripts\python -c "import soundcard as sc, sys; m=sc.all_microphones(include_loopback=True); [sys.stdout.write('[{}] {} | loopback={} | default_sr={}\n'.format(i,d.name,getattr(d,'isloopback',None),getattr(d,'default_samplerate',None))) for i,d in enumerate(m)]"
```

If your preferred loopback isn’t defaulted, select it manually in the dropdown and press Start again.

### Troubleshooting
- __NumPy 2.x ‘fromstring’ error__: We ship a shim that redirects binary `np.fromstring` calls to `np.frombuffer` inside dependencies (e.g., `soundcard`). If you still see it, restart the app. As a fallback, `pip install -U soundcard`. Avoid downgrading NumPy to 1.x on Windows unless wheels exist; building from source requires MSVC.
- __VAD install fails__: Use `webrtcvad-wheels` (prebuilt) instead of `webrtcvad` source builds on Windows.
- __No transcript__: Ensure Zoom/Meet/YouTube are routed to the selected loopback device (Windows Sound settings). Try another loopback (e.g., Speakers vs Digital Output).
- __STT disabled__: Without `faster-whisper`, you’ll see placeholder segments like `[Audio segment ~Ns]`. Install `faster-whisper` and set `WHISPER_MODEL` (e.g., `tiny.en`) in `frontend/.env`.

## Security
- The backend reads `OPENAI_API_KEY` from `backend/.env`. Keep it server-side. The frontend does not require an OpenAI key.

## AI model
 - Default: `gpt-4o-mini` (fast and cost-efficient).
 - UI: Use the Model dropdown to choose `gpt-4o-mini (fast)` or `gpt-4o (higher quality)`. Hover for tooltips; click the help icon for pros/cons.
 - Backend: `POST /api/generate-answer` accepts an optional `model`; `OpenAIService` falls back to `OPENAI_MODEL` in `backend/.env` when the UI doesn’t specify.
 - Config: set `OPENAI_MODEL` in `backend/.env` to change the default.

## Interview notes limits
 - Stored as LONGTEXT in DB (`interview_infos.context`). The practical cap is the model’s context window per request.
 - UI shows a live counter with a soft limit (default 10,000 chars). Configure via `INTERVIEW_NOTES_SOFT_LIMIT` in `frontend/.env`.
 - Backend enforces the same soft limit and, if exceeded, includes head + tail with a truncation marker for performance. Configure via `INTERVIEW_NOTES_SOFT_LIMIT` in `backend/.env`.
 - Keep interview notes focused. Extremely long notes can increase latency and reduce answer quality.

## Roadmap (next steps)
- Personas CRUD; corrections capture and learning loop to adapt prompts.
- Streamed responses; retry/backoff and better error UX.
- Automated tests for API and UI.

## Contributing
- PRs welcome. Please follow conventional commits in messages (we’ll add commit templates later).
