# RAG Assessment

A Retrieval-Augmented Generation (RAG) application, built as a modular monolith with an eye toward a future distributed deployment. See [`architecture/architecture.md`](architecture/architecture.md) for the tier layout and [`architecture/tech-stack.md`](architecture/tech-stack.md) for technology choices and rationale.

## Status
In development — the `project/` tiers are scaffolded (Phase 1 of `specs/002-master-development-plan.md`) with a health-check backend and a placeholder frontend; the actual RAG pipeline (ingestion, retrieval, generation) hasn't been built yet. This README is kept up to date as the application takes shape.

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
3. `.env` is gitignored — never commit it.

## Running the Application
From the repo root:

```sh
uv sync --all-packages   # installs all three tiers' dependencies once

# Backend (FastAPI) — http://127.0.0.1:8000
uv run --package rag-backend uvicorn backend.main:app --app-dir project/backend/src --reload

# Frontend (Streamlit) — separate terminal
uv run --package rag-frontend streamlit run project/frontend/src/frontend/app.py
```

The backend currently only exposes `GET /health`; the frontend currently only shows a placeholder page. Both will grow as later phases land.

## Project Structure
- `project/backend/` — FastAPI app and RAG pipeline (`rag-backend` package)
- `project/storage/` — Chroma persistence (`rag-storage` package)
- `project/frontend/` — Streamlit UI (`rag-frontend` package)
- `architecture/` — architecture and tech-stack documentation
- `specs/` — planning documents, one per feature/phase

## Testing
Each tier is tested independently with `pytest`:

```sh
uv run --package rag-backend pytest
uv run --package rag-storage pytest
uv run --package rag-frontend pytest
```
