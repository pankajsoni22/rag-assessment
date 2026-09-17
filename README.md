# RAG Assessment

A Retrieval-Augmented Generation (RAG) application, built as a modular monolith with an eye toward a future distributed deployment. See [`architecture/architecture.md`](architecture/architecture.md) for the tier layout and [`architecture/tech-stack.md`](architecture/tech-stack.md) for technology choices and rationale.

## Status
In development — the `project/` tiers (backend, storage, frontend) are not yet scaffolded. This README is kept up to date as the application takes shape; the sections below reflect what's actually runnable today.

## Tech Stack (summary)
Python + FastAPI backend, LlamaIndex orchestration, Google Gemini embeddings, Groq LLM, Chroma vector store, Streamlit frontend. All model calls go through free-tier cloud APIs — no local model inference. Full details in [`architecture/tech-stack.md`](architecture/tech-stack.md).

## Prerequisites
- Python 3.x (version will be pinned here once the backend is scaffolded)
- A free Groq API key
- A free Google AI Studio (Gemini) API key

## Configuration
1. Copy `.env.example` to `.env`.
2. Fill in your keys:
   - `GROQ_API_KEY` — get one at https://console.groq.com/keys
   - `GOOGLE_API_KEY` — get one at https://aistudio.google.com/apikey
3. `.env` is gitignored — never commit it.

## Running the Application
Not available yet. This section will be filled in with exact setup/run commands once the backend, storage, and frontend tiers exist.

## Project Structure
- `project/backend/` — FastAPI app and RAG pipeline (planned)
- `project/storage/` — Chroma persistence (planned)
- `project/frontend/` — Streamlit UI (planned)
- `architecture/` — architecture and tech-stack documentation
- `specs/` — planning documents, one per feature

## Testing
To be added once backend/frontend code exists — unit tests are required for both per `CLAUDE.md`.
