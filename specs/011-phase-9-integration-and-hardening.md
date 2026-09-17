# Phase 9: Integration & Hardening

Plan and record for Phase 9 of `specs/002-master-development-plan.md`, the final phase: cross-tier end-to-end verification of both vertical slices through the real UI, plus a pass against the non-functional requirements in `specs/001-rag-generator-requirements.md`, before the MVP is considered complete.

This plan is grounded in a full re-read of `specs/001-rag-generator-requirements.md` (functional A1–A5, non-functional B1–B8), cross-checked against the implemented Phase 2–8 code, which surfaced five concrete, fixable gaps (below) rather than staying at the level of abstract categories.

## Decision (confirmed with the user)

**Automated Playwright E2E tests**, not a manual checklist — a new `playwright` + `pytest-playwright` dependency, driving a real browser against the real running frontend and backend.

## Status

**Hardening fixes 1–5: implemented and tested** (`uv run --package rag-backend pytest` — 61 passed, up from 58 after Phase 6; `uv run --package rag-frontend pytest` — still 21 passed).

**NFR checklist: reviewed, all items satisfied** — see below, with what was actually checked (not just asserted).

**E2E test harness and all 3 test cases: written, but not executable in this sandboxed environment.** `uv run --package rag-e2e playwright install chromium` downloads the browser binary fine, but launching it fails —
```
error while loading shared libraries: libnspr4.so: cannot open shared object file: No such file or directory
```
`playwright install --with-deps chromium` (which would apt-install the missing system libraries) requires `sudo`, and this environment has no passwordless sudo and no interactive terminal for a password prompt — confirmed (`sudo -n true` fails; no browser, no NSS/NSPR libs found anywhere on the system via `find`/`dpkg -l`). This is an environment limitation, not a code issue: the `conftest.py` fixtures (`backend_url`, `frontend_url`) were verified working by manually driving them outside pytest — the real FastAPI app started, `/health` and a real `POST /sets` call succeeded, and the real Streamlit frontend started pointed at that backend and served `200`. Running the actual test files under `pytest` confirms this too: all 4 tests collect and reach browser-launch setup with no fixture/import errors — the only failure is the browser launch itself.

**To actually run the E2E suite**, on a machine with normal sudo access:
```sh
uv run --package rag-e2e playwright install --with-deps chromium
uv run --package rag-e2e pytest tests/e2e
```
Since the Playwright selectors in the test files (ARIA roles, `data-testid`s) were written from Streamlit's documented conventions rather than verified against a live browser, minor selector fixes may be needed the first time they're actually run.

## E2E Test Harness Design

New workspace member `tests/e2e/` (sibling to `project/`, not itself an application tier — `[tool.uv] package = false`, added to the root `pyproject.toml`'s `[tool.uv.workspace] members`).

- `tests/e2e/conftest.py`:
  - `backend_url` (session-scoped) — starts the real FastAPI app (`backend.main.app`) via `uvicorn.Server` on a background thread, bound to a free local port, with `get_document_set_service`/`get_ingestion_service`/`get_rag_orchestrator` overridden (via `app.dependency_overrides`, same mechanism as the Phase 4/6 route tests) to real services wired to a real temp-dir `ChromaVectorStore` but fake `EmbeddingClient`/`GenerationClient` — deterministic, fast, no real API keys needed, while still exercising the real FastAPI app, routing, `ChromaVectorStore`, loaders, and chunking.
  - `frontend_url` (session-scoped) — starts the real Streamlit app as a subprocess, pointed (`BACKEND_URL` env var) at `backend_url`'s port.
- Both fixtures are **session-scoped and shared** across all 3 test files for speed (not restarting a real server per test). This surfaced a real determinism bug while writing the tests: the fake embedding client returns an identical vector for every text, so an *unscoped* "search everything" query's top-k results aren't guaranteed to include a given test's own just-uploaded chunk once other tests have populated the same shared store. Fixed by having `test_qa_flow.py` and `test_not_found_flow.py` scope their chat queries to a set created within that test (an empty one for the not-found case), rather than relying on "search everything" ever being empty or containing only that test's data.

**Stays manual, not covered by this automated suite** (since it deliberately fakes Gemini/Groq): a short one-time sanity check with real API keys, verifying the actual embedding/generation calls work — the same "manual verification once a real key is available" note already carried since Phases 3/5.

### E2E Test Cases (written)
- `test_ingestion_flow.py` — create a set, upload a document via the real UI, see it listed as `ready`; remove a document and see it disappear.
- `test_qa_flow.py` — with a document ingested into its own set, ask a question scoped to that set via Chat, see a grounded answer with citations rendered.
- `test_not_found_flow.py` — ask a question scoped to a freshly created, never-populated set, see the distinct "not found" state.

## Hardening Fixes (implemented)

1. **Empty documents silently succeed** (violated A1.4's "clearly when it was not [added]... empty file"). Fixed: `IngestionService.ingest()` now raises `EmptyDocumentError` when chunking produces zero chunks, instead of marking the document `READY`.
2. **Ingestion failures surfaced as opaque `500`s** (violated A5.22, B4.7). Fixed: `document_routes.py`'s `upload_document` now catches `EmptyDocumentError` and any other ingestion failure, returning `422` with a plain-language `detail` — verified (test) that the message never leaks raw exception class names or stack details, satisfying B6 too.
3. **No startup-time secrets check** (B4.7). Fixed: `main.py` now has a FastAPI `lifespan` handler that calls `get_settings()` once at startup and logs a warning (not a hard crash) on failure — confirmed existing tests (which run without a real `.env`) are unaffected.
4. **No loading indicators** (A4.20). Fixed: `st.spinner` wraps the upload call in `set_manager.py` and the ask call in `chat.py`.
5. **LLM response consistency** (B1.2). Fixed: `GroqClient` pins `temperature=0`.

## Non-Functional Requirements Checklist (all reviewed)

- **B1** Correctness — fix #5 (temperature=0) plus the existing "not found" grounding pre-check (Phase 5).
- **B2** Works with any document set — reviewed: no document-specific logic exists anywhere in loaders/chunking/embedding/generation; all operate generically on whatever text/chunks they're given.
- **B3** Responsiveness — timing pass with a ~4KB text document via the real (fake-client) pipeline: upload+ingest ~0.5s, list ~0.01s. Confirms no pipeline-level overhead; real-world latency is dominated by actual Gemini/Groq round-trips, not measurable without real keys.
- **B4** Reliability — fixes #1–#3; also confirmed empirically that `chromadb.PersistentClient` auto-creates its persist directory when it doesn't exist yet.
- **B5** Growth — reviewed: `DocumentSetService`'s dict-based bookkeeping and Chroma's collection are both straightforward to scale within the single-user/single-process design; nothing assumes a fixed small scale.
- **B6** Privacy — verified (test) the generic-ingestion-failure message never leaks internals; confirmed via `grep` that `.env`/secrets are never logged (the startup warning logs pydantic's "field required" message, which never echoes actual secret values); deletion endpoints purge Chroma data, covered by existing Phase 4 tests.
- **B7** Clarity — Phase 8's distinct "Not found in the documents." `st.info` state, covered by `test_not_found_answer_renders_distinct_info_state` (unit-level) and `test_not_found_flow.py` (E2E, not yet executed — see Status).
- **B8** Maintainability — verified via `grep` across the whole `project/` tree: `storage` has zero imports of `backend`, `frontend` has zero imports of `backend`/`storage`, and backend's only production-code import of `storage` is in the composition root (`api/dependencies.py`) — the tier boundaries established since Phase 1 actually hold, not just in principle. Confirmed the `DocumentLoader` registry needs exactly one new class + one registration line + one enum member to add a format, by inspection of `loaders/registry.py`.

## New Dependency

`playwright` + `pytest-playwright` added to `tests/e2e/pyproject.toml`. Requires a one-time `playwright install --with-deps chromium` (browser binary + OS-level dependencies, needs `sudo`) as an execution-time setup step, separate from `uv sync`.
