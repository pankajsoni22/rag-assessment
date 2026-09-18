# Containerization

Plan and record for containerizing the application with Docker: one image
per deployable tier, orchestrated with Docker Compose, per the top-level
project goal of being "structured so it can later be split into a
distributed deployment."

## Decision (confirmed with the user)

**Chroma is split into its own container**, not kept embedded inside the
backend process. This was an explicit choice between two options presented
to the user:
1. Keep Chroma embedded in the backend container (2 containers total,
   zero backend code changes, matches `tech-stack.md` as it stood).
2. Split Chroma into its own container, backend talks to it over HTTP
   (3 containers, requires a real code change).

The user chose option 2 — this is the first tier actually pulled out of the
backend process, not just packaged alongside it.

## What changed in the code

- `project/storage/src/storage/_chroma_collection.py` (new) — the
  upsert/query/delete logic shared by both Chroma-backed `VectorStore`
  implementations, extracted so adding the second implementation didn't
  duplicate it.
- `project/storage/src/storage/chroma_vector_store.py` — `ChromaVectorStore`
  (embedded, `PersistentClient`) now built on the shared base; behavior
  unchanged, all existing tests pass unmodified.
- `project/storage/src/storage/chroma_http_vector_store.py` (new) —
  `ChromaHttpVectorStore`, same interface, backed by `chromadb.HttpClient`.
- `backend/config.py` — two new optional settings, `chroma_host` (default
  `""`) and `chroma_port` (default `8000`).
- `backend/api/dependencies.py` — `get_vector_store()` now branches: empty
  `chroma_host` (the default, and every existing `.env`) keeps using the
  embedded `ChromaVectorStore` exactly as before; a non-empty `chroma_host`
  switches to `ChromaHttpVectorStore`. **No existing behavior changes** for
  anyone not running via Docker Compose.
- `.env.example` — documents `CHROMA_HOST`/`CHROMA_PORT` and that
  `docker/docker-compose.yml` overrides them (and `BACKEND_URL`) with
  container-network addresses.

## What's in `docker/`

- `docker/backend/Dockerfile`, `docker/frontend/Dockerfile` — each `FROM
  python:3.12-slim`, installs `uv` (copied from the official
  `ghcr.io/astral-sh/uv` image rather than pip-installed, avoiding a second
  installer), then `uv sync --package <rag-backend|rag-frontend> --frozen`.
  Build context is the repo root (not `docker/`) because this is a uv
  workspace — resolving either package needs the root `pyproject.toml` /
  `uv.lock` plus every declared workspace member's `pyproject.toml` to
  exist on disk (uv validates the whole workspace, not just the package
  being synced), so each Dockerfile copies the whole `project/` and
  `tests/` trees rather than cherry-picking files.
- `docker/docker-compose.yml` — three services:
  - `chroma` — official `chromadb/chroma:1.5.9` image (pinned to match the
    `chromadb` client version resolved in `uv.lock`, since Chroma's wire
    protocol isn't guaranteed stable across major versions), `IS_PERSISTENT`
    on, data on a named volume (`chroma-data:/data`). No host port
    published — only other containers reach it.
  - `backend` — built image, `CHROMA_HOST=chroma` override, health-checked
    via `/health`, publishes `:8000`.
  - `frontend` — built image, `BACKEND_URL=http://backend:8000` override,
    waits on backend's healthcheck, publishes `:8501`.
  - Secrets (`GROQ_API_KEY`, `GOOGLE_API_KEY`) still come from the
    repo-root `.env` via each service's `env_file:` — never baked into an
    image or written into the compose file itself.
- `.dockerignore` (repo root, not inside `docker/`) — has to live at the
  build context root for Docker to find it automatically; keeps `.git`,
  `.venv`, caches, and — importantly — `.env` itself out of the build
  context, so no secret can end up in an image layer even by accident.

## Verification status

**Cannot be built or run in this sandbox.** Docker isn't installed here
(`docker`/`docker compose` commands not found) and installing it needs
`sudo`, which requires an interactive password this environment doesn't
have (`sudo -n true` fails) — the same limitation already recorded for the
Playwright browser install in
[`011-phase-9-integration-and-hardening.md`](011-phase-9-integration-and-hardening.md).

What **was** verified without Docker:
- All existing backend/storage/frontend test suites still pass unmodified
  after the `ChromaVectorStore` refactor (91 backend, 10 storage, 26
  frontend at time of writing) — the embedded path is provably unchanged.
- `ChromaHttpVectorStore` has its own unit tests
  (`project/storage/tests/test_chroma_http_vector_store.py`), mocking
  `chromadb.HttpClient` to check it connects with the given host/port and
  correctly delegates upsert/query/delete — this cannot exercise a real
  server round-trip without one running.
- `get_vector_store()`'s branching logic (empty vs. set `chroma_host`) has
  direct unit tests (`project/backend/tests/test_dependencies.py`).
- The `chromadb/chroma:1.5.9` image tag, its `/data` persist-directory
  convention, `IS_PERSISTENT` env var, and lack of `curl`/`wget` (hence the
  bash `/dev/tcp` healthcheck) were confirmed against the project's own
  `docker-compose.yml` and current documentation, not assumed.

**To actually verify**, once Docker is available:
```sh
cd docker
docker compose up --build
```
Then open `http://localhost:8501` and confirm upload → chat works, and
`http://localhost:8000/health` returns `{"status": "ok"}`. Since none of
this has run yet, expect the first real run to surface something minor —
most likely around the compose healthcheck timing or the uv workspace
copy step — worth a quick pass before treating this as done.
