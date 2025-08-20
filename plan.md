# 4-hour Sprint Plan – AI-Powered Real-Time Interview Assistant

Date: 2025-08-20 (local)

## Goals (MVP for main functionality)
- End-to-end flow: live transcript (sim), submit prompt, get fast AI answer via backend using your OpenAI key.
- Persona selection affects answer style.
- Persist transcript chunks and Q&A to SQLite.
- Clean, always-on-top window. No tray icon. No stealth mode.

## Scope
- In: Personas (basic), transcripts, Q&A storage, API glue, frontend persona dropdown, instant-stop improvement.
- Out (for now): Real audio capture, corrections learning loop, history UI, MySQL.

## Deliverables
- Backend migrations, models, seeders for: `personas`, `sessions`, `transcript_chunks`, `qa_entries`.
- API endpoints:
  - GET `/api/personas` → list personas
  - POST `/api/transcripts` → store transcript chunk
  - POST `/api/generate-answer` → generate + store Q&A
- Frontend: persona dropdown, pass `persona_id` to generate, instant-stop for simulator.
- Updated docs (README + CHANGELOG done; persona usage note if needed).

## Timeline (target ~4 hours)
1) Backend DB + seed (45–60 min)
- Create migrations and Eloquent models for `personas`, `sessions`, `transcript_chunks`, `qa_entries`.
- Seeder for 3 default personas (Concise Pro, Friendly Explainer, Data-Driven Analyst) with system prompts.
- Migrate + seed.

2) Backend endpoints (35–45 min)
- GET `/api/personas` (controller + route).
- Update `AiController@storeTranscript` to persist chunk (use session_id or default "local-dev").
- Update `AiController@generate` to:
  - Load persona by `persona_id`, build system prompt, call OpenAI.
  - Store Q&A row (question, ai_answer, persona_id, session_id).

3) Frontend integration (40–55 min)
- `BackendClient.get_personas()`.
- Add persona dropdown in `MainWindow` and wire `self.persona_id`.
- Pass `persona_id` to `generate_answer` (already supported in client call).

4) UX reliability (20–30 min)
- Instant stop for simulation: replace `time.sleep()` with `Event.wait(0.1)` loop in `transcriber.py`.
- Minor status/disable/enable polish.

5) QA + polish (20–30 min)
- Manual E2E test: start transcript → submit → verify answer → DB rows written.
- Quick docs touch-up if needed.

## API contracts (current/target)
- GET `/api/personas`
  - 200: `{ personas: [{ id, name }, ...] }` (can include `system_prompt` server-side only)
- POST `/api/transcripts` JSON: `{ session_id?, text, source? }`
  - 200: `{ ok: true }`
- POST `/api/generate-answer` JSON: `{ session_id?, persona_id?, prompt }`
  - 200: `{ answer: string }`

## Data model (lean)
- personas: id, name (string), system_prompt (text), timestamps
- sessions: id (uuid or string), title nullable, started_at, ended_at nullable, timestamps
- transcript_chunks: id, session_id (string), text (text), source (string), created_at
- qa_entries: id, session_id (string), persona_id (int), question (text), ai_answer (text), final_answer nullable, created_at

## Risks & fallback
- Time risk on migrations/controllers: Keep schema minimal (above). Skip sessions table if time-constrained; use simple string `session_id` only.
- Persona influence minimal: start with basic system prompts; refine later.

## Acceptance criteria
- Persona list loads in frontend; user can choose one.
- Submit generates an answer that reflects persona.
- SQLite has rows in `transcript_chunks` and `qa_entries` after usage.
- App closes cleanly without QThread warnings; no tray/stealth.

## Nice-to-haves (if time remains)
- Past Q&A viewer (simple list endpoint + frontend panel).
- Real audio capture on Windows (WASAPI loopback + VAD).
