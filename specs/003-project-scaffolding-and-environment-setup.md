# Phase 1: Project Scaffolding & Environment Setup

Technical spec for Phase 1 of `specs/002-master-development-plan.md`: create the `project/backend`, `project/storage`, `project/frontend` tier directories, wire up environment/secrets loading, set up dependency manifests, and add base test scaffolding, so every later phase has somewhere to add code and tests from day one.

## Decisions

- **uv** for dependency/environment management across all three tiers. Chosen over Poetry (no native multi-package workspace — would need manual path dependencies) and plain pip+requirements.txt (no lockfile, no workspace support).
- **Multi-package workspace**: `project/backend`, `project/storage`, `project/frontend` are each their own installable package with their own `pyproject.toml`, tied together by a root `pyproject.toml` uv workspace. This matches CLAUDE.md's "split apart later without a rewrite" goal more directly than one shared environment would.
- **Python 3.12**, pinned via a root `.python-version`. uv manages its own 3.12 toolchain independent of the system Python.
- **Dependency direction**, extending the "tiers talk through interfaces" principle in `architecture/architecture.md` down to packaging:
  - `storage` has zero dependency on `backend`.
  - `frontend` has zero dependency on `backend`/`storage` code — HTTP only, via its own API Client (built in Phase 7).
  - `backend` depends on `storage` *only* for its composition root (`src/backend/main.py`, where the concrete `ChromaVectorStore` will be constructed at startup in a later phase) — business-logic modules depend only on the `VectorStore` interface (a `typing.Protocol`, to be added in `backend`'s `interfaces/` package in Phase 2), so `storage`'s implementation satisfies it structurally without importing `backend` at all.
- **pytest** as the test runner for all three tiers. Frontend additionally uses Streamlit's built-in `streamlit.testing.v1.AppTest` for UI smoke tests — no extra dependency.
- **pydantic-settings** for the backend's `Settings`/env-var loading — idiomatic alongside FastAPI/pydantic, gives typed env var validation for free. Lighter alternative considered and rejected: `python-dotenv` + manual `os.environ` reads, which pushes validation into hand-written code.
- Linting/formatting tooling (ruff, mypy, etc.) is out of scope for this phase.
- The subpackages named in `architecture/backend-low-level-design.md` (`domain/`, `interfaces/`, `loaders/`, `services/`, `clients/`, `api/` under backend; the Chroma module under storage; `ui/` under frontend) were **not** created empty in this phase. Each gets created by the phase that first adds real content to it.

## What Was Created

### Workspace root
- `pyproject.toml` — uv workspace: `members = ["project/backend", "project/storage", "project/frontend"]`.
- `.python-version` — `3.12`.
- `.gitignore` — added `.venv/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`, and the local Chroma persistence directory. `uv.lock` is committed (workspace lockfile).
- `.env.example` — added `CHROMA_PERSIST_DIR`.

### `project/backend/`
- `pyproject.toml` — package `rag-backend`; deps `fastapi`, `uvicorn[standard]`, `pydantic-settings`, workspace dependency on `rag-storage`; dev deps `pytest`, `httpx`.
- `src/backend/main.py` — FastAPI app with `/health`. Composition root for later phases.
- `src/backend/config.py` — `Settings` (pydantic-settings), reading `GROQ_API_KEY`, `GOOGLE_API_KEY`, `CHROMA_PERSIST_DIR` from the repo-root `.env`.
- `tests/test_health.py` — smoke test via `TestClient`.

### `project/storage/`
- `pyproject.toml` — package `rag-storage`; deps `chromadb`; dev deps `pytest`.
- `tests/test_placeholder.py` — trivial passing test; real Chroma-backed tests land in Phase 2.

### `project/frontend/`
- `pyproject.toml` — package `rag-frontend`; deps `streamlit`, `httpx`; dev deps `pytest`.
- `src/frontend/app.py` — placeholder Streamlit entrypoint.
- `tests/test_app.py` — smoke test via `streamlit.testing.v1.AppTest`.

### Documentation
- `README.md` updated: Prerequisites, Configuration, Running the Application, Project Structure, Testing.

## Verification (all passed)

- `uv sync --all-packages` — installs all three packages into one workspace virtualenv without error.
- `uv run --package rag-backend pytest`, `uv run --package rag-storage pytest`, `uv run --package rag-frontend pytest` — all green.
- `uvicorn backend.main:app` started and `/health` returned `{"status": "ok"}`.
- `streamlit run project/frontend/src/frontend/app.py --server.headless true` started and served HTTP 200.
