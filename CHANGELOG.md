# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2025-08-20
- Backend:
  - Added migrations and models for `personas`, `transcript_chunks`, `qa_entries`, and `interview_infos`.
  - Implemented API endpoints in `AiController`: `GET /api/personas`, `POST /api/transcripts`, `POST /api/generate-answer` (persona + interview context), `GET|POST /api/interview-info`.
  - `OpenAIService::generateAnswer()` now accepts an optional custom system prompt; falls back to HTTP if SDK is missing.
  - Seeded default personas via `PersonaSeeder` and wired into `DatabaseSeeder`.
  - Switched docs and default setup to MySQL (SQLite still supported).
- Frontend:
  - Added persona dropdown and interview info inputs (Company, Role, Notes) with Save in `app/main.py`.
  - Extended `services/backend_client.py` with personas and interview info methods; requests include `session_id` and `persona_id`.
  - Improved transcriber to stop instantly using interruptible wait loop in `services/transcriber.py`.
- Docs:
  - Updated `README.md` to MySQL-by-default, current data model, accurate run commands, and instant-stop note.

## [0.1.1] - 2025-08-20
- Frontend: removed system tray icon and stealth mode; window remains always-on-top.
- Frontend: added clean shutdown of transcriber thread on window close to prevent QThread warning.
- Docs: updated README to remove tray/stealth references, clarify env usage (backend `OPENAI_API_KEY`), and note simulation stop behavior.

## [0.1.0] - 2025-08-20
- Project scaffolding: docs and Python frontend skeleton
- Planned Laravel 11 backend with SQLite and OpenAI integration
- Added README with setup instructions
