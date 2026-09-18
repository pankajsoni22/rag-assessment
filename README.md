# RAG Assessment

A Retrieval-Augmented Generation (RAG) application, built as a modular monolith with an eye toward a future distributed deployment. See [`architecture/architecture.md`](architecture/architecture.md) for the tier layout and [`architecture/tech-stack.md`](architecture/tech-stack.md) for technology choices and rationale.

## Status
All 9 phases of `specs/002-master-development-plan.md` are implemented: document ingestion (PDF/Word/text/Markdown), sets, multi-turn Q&A with citations, and a Streamlit UI for both. See `specs/003`–`011` for what each phase built.

## Tech Stack (summary)
Python + FastAPI backend, LlamaIndex orchestration, Google Gemini embeddings, Groq LLM, Chroma vector store, Streamlit frontend. All model calls go through free-tier cloud APIs — no local model inference. Full details in [`architecture/tech-stack.md`](architecture/tech-stack.md).

## Prerequisites
- [`uv`](https://docs.astral.sh/uv/) — manages the Python toolchain and per-tier dependencies; installs its own Python 3.12, no separate Python install needed.
- A free Groq API key
- A free Google AI Studio (Gemini) API key

## Configuration
1. Copy `.env.example` to `.env`.
2. Fill in your keys:
   - `GROQ_API_KEY` — get one at https://console.groq.com/keys
   - `GOOGLE_API_KEY` — get one at https://aistudio.google.com/apikey
   - `CHROMA_PERSIST_DIR` — local directory Chroma persists to; the default value in `.env.example` works as-is.
   - `CHROMA_HOST` / `CHROMA_PORT`, `BACKEND_URL` — leave these as the `.env.example` defaults for direct `uv run` use (Option B below). Docker Compose overrides them itself for container-to-container addressing — you don't need to change `.env` to use Docker.
3. `.env` is gitignored — never commit it.

## Running the Application

### Option A: Docker Compose (recommended)
Runs all three containers (frontend, backend, and Chroma as its own
service) with one command — see
[`architecture/architecture.md`](architecture/architecture.md)'s
*Deployment* section and [`specs/012-containerization.md`](specs/012-containerization.md)
for why Chroma gets its own container.

Prerequisite: Docker with the Compose plugin (`docker compose version`).

```sh
cd docker
docker compose up --build
```

- Frontend: http://localhost:8501
- Backend: http://localhost:8000 (docs at `/docs`, health at `/health`)
- Chroma isn't exposed to the host — only the backend container talks to it.

`docker compose down` stops everything; add `-v` to also delete the
`chroma-data` volume (wipes all uploaded documents).

### Option B: Run each tier directly with uv
From the repo root:

```sh
uv sync --all-packages   # installs all tiers' dependencies once

# Backend (FastAPI) — http://127.0.0.1:8000
uv run --package rag-backend uvicorn backend.main:app --app-dir project/backend/src --reload

# Frontend (Streamlit) — separate terminal
uv run --package rag-frontend streamlit run project/frontend/src/frontend/app.py
```

Open the frontend URL Streamlit prints (typically `http://localhost:8501`). "Sets & Documents" lets you create a set and upload PDF/Word/text/Markdown files; "Chat" lets you ask questions, optionally scoped to one set, with grounded answers and citations.

**Use small files.** Both external APIs are free-tier and rate-limited (see `architecture/tech-stack.md`) — a large document produces many chunks, and each chunk needs its own embedding call, so big or scanned documents commonly hit a rate limit or fail with "no readable text content" before finishing. Prefer small, text-based PDFs or plain text files (see `data/` for ready-made samples in every supported format). There's a UI-level upload size sanity limit (`.streamlit/config.toml`) — not a guarantee that any file under it will process cleanly on the free tier.

## Project Structure
- `project/backend/` — FastAPI app and RAG pipeline (`rag-backend` package)
- `project/storage/` — Chroma persistence (`rag-storage` package)
- `project/frontend/` — Streamlit UI (`rag-frontend` package)
- `tests/e2e/` — cross-tier Playwright end-to-end tests (`rag-e2e`, not installed as an application tier)
- `docker/` — Dockerfiles per tier and the Compose file (see *Running the Application* above)
- `data/` — small sample documents (one per supported format) for manual upload testing
- `architecture/` — architecture and tech-stack documentation
- `specs/` — planning documents, one per feature/phase

## Testing
Each tier is tested independently with `pytest`. Run from the repo root with an explicit path (bare `pytest` from the root also picks up `tests/e2e`, which needs the Playwright browser installed — see below):

```sh
uv run --package rag-backend pytest project/backend/tests
uv run --package rag-storage pytest project/storage/tests
uv run --package rag-frontend pytest project/frontend/tests
```

End-to-end tests drive a real browser against the real frontend + backend (with only the Gemini/Groq calls faked — everything else is real, including Chroma). They need Playwright's browser binary and OS-level dependencies installed once (requires `sudo`):

```sh
uv run --package rag-e2e playwright install --with-deps chromium
uv run --package rag-e2e pytest tests/e2e
```

Real Gemini/Groq integration isn't covered by any automated test (both are faked everywhere for determinism/cost) — verify manually with real API keys before relying on it.
