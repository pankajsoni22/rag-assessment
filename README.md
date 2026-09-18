# RAG Assessment

A Retrieval-Augmented Generation (RAG) application, built as a modular monolith with an eye toward a future distributed deployment. See [`architecture/architecture.md`](architecture/architecture.md) for the tier layout and [`architecture/tech-stack.md`](architecture/tech-stack.md) for technology choices and rationale.

## Status
All 9 phases of `specs/002-master-development-plan.md` are implemented: document ingestion (PDF/Word/text/Markdown), sets, multi-turn Q&A with citations, and a Streamlit UI for both. See `specs/003`–`011` for what each phase built.

## About & Assumptions
See [`ABOUT.md`](ABOUT.md) for the assumptions this application deliberately makes (scope, technology, data handling, defaults), its known limitations, and open questions.

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

### Option A: Docker (recommended)
Runs all three containers — frontend, backend, and Chroma as its own
service — with one command. See
[`architecture/architecture.md`](architecture/architecture.md)'s *Deployment*
section and [`specs/012-containerization.md`](specs/012-containerization.md)
for why Chroma gets its own container.

**Prerequisites:** Docker with the Compose plugin (`docker compose version`
should work) and a running Docker daemon. You do *not* need `uv` for this
option.

**Steps**

1. Configure your keys (once) — see *Configuration* above. In short:
   ```sh
   cp .env.example .env      # then put your GROQ_API_KEY and GOOGLE_API_KEY in .env
   ```
2. Start everything, from the repo root:
   ```sh
   ./docker/rag.sh up
   ```
   The first run builds the images and takes a few minutes; later runs are
   fast. The command returns once every container reports healthy.
3. Open the frontend at http://localhost:8501 and click **Start With RAG Assessment Project**.
   The backend API is at http://localhost:8000 (interactive docs at `/docs`,
   health at `/health`). Chroma isn't exposed to the host — only the backend
   container talks to it.
4. Stop everything:
   ```sh
   ./docker/rag.sh down
   ```

**`docker/rag.sh` commands**

| Command | What it does |
|---|---|
| `./docker/rag.sh up` | Builds images if needed, starts all containers, waits until they're healthy, prints the URLs. Checks Docker is available and that `.env` exists with both API keys filled in (creating `.env` from `.env.example` if it's missing) — and tells you exactly what to fix if not. |
| `./docker/rag.sh down` | Stops and removes the containers. **Sets and the document list are held in backend memory, so they are empty after the next `up`** — you re-create sets and re-upload. Old vectors stay in the `chroma-data` volume (see *Known limitation* below). |
| `./docker/rag.sh down --purge` | Same, but also deletes the volume — **every stored document vector**. Asks you to type `yes` first. Use this for a genuinely clean slate. |
| `./docker/rag.sh restart` | `down` then `up`. |
| `./docker/rag.sh status` | Shows container state and health. |
| `./docker/rag.sh logs [service]` | Follows logs; `service` is `frontend`, `backend` or `chroma` (default: all). |
| `./docker/rag.sh help` | Prints usage. |

Containers restart automatically (`unless-stopped`) if Docker or the machine
restarts, until you run `down`. After changing code, run `./docker/rag.sh up`
again — it rebuilds. After changing `.env`, run `./docker/rag.sh restart`.

The script is a thin wrapper; the equivalent raw commands are
`docker compose -f docker/docker-compose.yml up --build -d --wait` and
`docker compose -f docker/docker-compose.yml down`.

**Known limitation — restarts.** By design (see [`ABOUT.md`](ABOUT.md)), the list of sets and documents lives in backend memory, while the vectors live in Chroma's volume. After *any* backend restart the UI shows no sets, but previously stored vectors are still searchable under "Search everything" and can't be removed from the UI. Run `./docker/rag.sh down --purge` before a fresh session or demo to avoid answers from documents you can no longer see.

**Troubleshooting**

- *"these are empty in .env"* — fill in `GROQ_API_KEY` / `GOOGLE_API_KEY`, then rerun.
- *"cannot reach the Docker daemon"* — start Docker (Docker Desktop, or `sudo systemctl start docker`), and make sure your user may run `docker` (e.g. is in the `docker` group).
- *Port 8501 or 8000 already in use* — stop whatever holds it (e.g. a Option B run) and retry.
- *A container is unhealthy* — `./docker/rag.sh logs backend` (or `frontend` / `chroma`).
- *Uploads or chat fail with rate-limit errors* — the free-tier APIs are limited; use small files (see below).

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

## Security & Secrets
- API keys live only in `.env` (gitignored). `.env.example` holds empty placeholders and is the only env file committed.
- `.env` is excluded from Docker images (`.dockerignore`), and the containers receive keys at runtime through `env_file:` — no key is baked into an image layer.
- `project_transcripts/` is committed, so **never paste a key, token or private key into a session you intend to export**, and read exported transcripts before committing them. Error output can leak partial keys (a pydantic validation error once printed the first and last characters of both API keys — since redacted). If a real key ever reaches git, rotate it at the provider; deleting it from a later commit does not remove it from history.
- Full audit record: [`specs/014-secrets-audit-and-docker-tooling.md`](specs/014-secrets-audit-and-docker-tooling.md).

## Project Structure
- `project/backend/` — FastAPI app and RAG pipeline (`rag-backend` package)
- `project/storage/` — Chroma persistence (`rag-storage` package)
- `project/frontend/` — Streamlit UI (`rag-frontend` package)
- `tests/e2e/` — cross-tier Playwright end-to-end tests (`rag-e2e`, not installed as an application tier)
- `docker/` — Dockerfiles per tier, the Compose file, and `rag.sh` (start/stop script; see *Running the Application* above)
- `data/` — small sample documents (one per supported format) for manual upload testing
- `ABOUT.md` — assumptions, defaults, known limitations, open questions
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
