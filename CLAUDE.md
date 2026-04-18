# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this app is

Hebrew-language adaptive math practice app for kids (טום, אדם, בן). Kids pick a profile, choose a topic (currently arithmetic only), answer 10 problems per session, and see a summary. Difficulty adjusts automatically via an ELO-like engine (scale 1–20).

## Commands

### Backend
```bash
uv sync                        # install dependencies
uv run uvicorn backend.main:app --reload --port 8000  # dev server
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # Vite dev server on :5173
npm run build    # tsc + vite build
npm run lint     # eslint
```

### Docker (full stack)
```bash
docker compose up --build      # requires external 'infra' network for nginx routing
docker network create infra    # create it once if missing
```

## Architecture

**Flow:** KidSelect → TopicSelect → Session (10 problems) → Summary

- `frontend/src/App.tsx` — single-file router using a `Page` discriminated union; no router library
- `frontend/src/api.ts` — all API calls in one `api` object; all requests go to `/api/` (proxied by nginx to backend port 8000)
- `frontend/src/strings.ts` — all UI text in Hebrew, exported as `S`; edit here for any copy changes
- `frontend/src/pages/` — one component per page, pure props-based (no global state)

**Backend layout:**
- `backend/main.py` — FastAPI app; CORS allows `:5173` for local dev
- `backend/models.py` — SQLAlchemy models: `Kid`, `KidTopicLevel`, `Session`, `SessionProblem`
- `backend/database.py` — SQLite at `data/math_tutor.db`; seeds 3 kids on first run
- `backend/adaptive.py` — ELO engine: correct+fast → +2, correct+slow → +1, wrong → −2; promotes at +6, demotes at −4
- `backend/routers/problems.py` — `GET /problems/next/{session_id}` and `POST /problems/submit`; difficulty update happens on submit
- `backend/routers/sessions.py` — `POST /sessions/start`, `GET /sessions/{id}/summary`
- `backend/generators/arithmetic.py` — pure algorithmic generator; difficulty 1–20 maps to specific problem types (see file docstring)

**Nginx** strips `/api/` prefix when proxying to backend, so backend routes don't include `/api`.

**No tests exist yet.**
