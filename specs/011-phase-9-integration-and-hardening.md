# Phase 9: Integration & Hardening (Plan)

Plan for Phase 9 of `specs/002-master-development-plan.md`, the final phase: cross-tier end-to-end verification of both vertical slices through the real UI, plus a pass against the non-functional requirements in `specs/001-rag-generator-requirements.md`, before the MVP is considered complete. **Not yet implemented** — depends on Phases 5–8, none of which are implemented yet either, so this describes what Phase 9 will do once they are.

This plan is grounded in a full re-read of `specs/001-rag-generator-requirements.md` (functional A1–A5, non-functional B1–B8), cross-checked against the already-implemented Phase 2–4 code and the Phase 5–8 plans, which surfaced five concrete, fixable gaps (below) rather than staying at the level of abstract categories.

## Decision (confirmed with the user)

**Automated Playwright E2E tests**, not a manual checklist — a new `playwright` + `pytest-playwright` dependency, driving a real browser against the real running frontend and backend.

## E2E Test Harness Design

New workspace member `tests/e2e/` (sibling to `project/`, not itself an application tier — added to the root `pyproject.toml`'s `[tool.uv.workspace] members`).

- `tests/e2e/conftest.py` fixtures:
  - `running_backend` — starts the real FastAPI app (`backend.main.app`) via `uvicorn.Server` on a background thread, bound to a free local port, with `GeminiEmbeddingClient`/`GroqClient` swapped for fakes via `app.dependency_overrides` (same mechanism already used in Phase 4/6 route tests) and a temp-dir `CHROMA_PERSIST_DIR`. Keeps the suite deterministic/fast/free of real API keys, while still exercising the *real* FastAPI app, routing, `ChromaVectorStore`, loaders, and chunking — everything except the two paid LLM calls, the same "fake only the true external boundary" principle used in every backend phase so far.
  - `running_frontend` — starts the real Streamlit app as a subprocess, pointed (`BACKEND_URL`) at `running_backend`'s port.
- Tests use Playwright's `page` fixture to drive an actual browser against the running frontend.

**Stays manual, not covered by this automated suite** (since it deliberately fakes Gemini/Groq): a short one-time sanity check with real API keys, verifying the actual embedding/generation calls work — the same "manual verification once a real key is available" note already carried since Phases 3/5.

### Planned E2E Test Cases
- Upload flow: create a set, upload a document via the real UI, see it listed as `ready`.
- Q&A flow: with a document ingested, ask a question via Chat, see a grounded answer with citations rendered.
- Not-found flow: ask a question with no matching/ingested documents, see the distinct "not found" state.

## Concrete Hardening Fixes Found This Session

1. **Empty documents silently succeed** (violates A1.4's "clearly when it was not [added]... empty file"). `IngestionService.ingest()` (Phase 4, already implemented) currently marks a document `READY` even when chunking produces zero chunks (e.g. an empty `.txt` file) — nothing is stored, but no error is shown. Fix: if `len(chunks) == 0`, treat it as a failure (`mark_error`, raise a clear error) instead of `mark_ready`.
2. **Ingestion failures surface as opaque `500`s** (violates A5.22's "plain language, not technical error codes" and B4.7's "fail gracefully with a clear message"). `backend/api/document_routes.py`'s `upload_document` only special-cases `SetNotFoundError`; any other ingestion failure (corrupt PDF, the empty-file case above) bubbles to FastAPI's default `500` with no detail. Fix: catch ingestion failures explicitly, return `422` with a plain-language `detail`.
3. **No startup-time secrets check** (relevant to B4.7 reliability). `Settings()` is only constructed lazily on first request (deliberately, per Phase 4's design, so tests don't need a real `.env`) — but that means a misconfigured `.env` in a real deployment fails silently until a user's first action. Fix: a FastAPI `lifespan` handler that calls `get_settings()` once at startup and logs a clear warning (not a hard crash, so `TestClient` usage without a `.env` stays unaffected) if it fails.
4. **No loading indicators planned for upload/ask** (A4.20: "not left wondering if it's stuck"). The Phase 7/8 plans don't currently call out `st.spinner` for the upload and ask actions. Fix: add them when those pages are implemented.
5. **LLM response consistency not addressed** (B1.2: "same question against the same documents should give a consistent, dependable answer"). The Phase 5 plan doesn't pin a temperature. Fix: `GroqClient` defaults to `temperature=0` (or another low fixed value) rather than the API default.

## Non-Functional Requirements Checklist

- **B1** Correctness — covered by fix #5 plus the existing "not found" grounding pre-check (Phase 5 plan).
- **B2** Works with any document set — review pass: confirm nothing in the pipeline is hardcoded to specific content (should already be true; no document-specific logic exists anywhere in the design).
- **B3** Responsiveness — manual timing pass with a few representative documents; no hard SLA, just a sanity check.
- **B4** Reliability — covered by fixes #1–#3; also verify `chromadb.PersistentClient` auto-creates its persist directory on first run.
- **B5** Growth — review pass: nothing in the design assumes a fixed small scale (already true by construction).
- **B6** Privacy — verify `.env`/API keys never appear in error responses or logs (worth an explicit check once fix #2's custom error handling exists); confirm deletion endpoints (Phase 4, already implemented and tested) actually purge Chroma data — already covered by existing tests.
- **B7** Clarity — covered by Phase 8's distinct "not found" visual treatment; verify in the E2E not-found test case.
- **B8** Maintainability — review pass, not new code: confirm the tier/interface boundaries established across Phases 1–8 actually hold (no accidental cross-tier imports), and that the `DocumentLoader` registry genuinely only needs one new class + one registration line to add a format.

## New Dependency

`playwright` + `pytest-playwright` added to `tests/e2e/pyproject.toml`. Requires a one-time `playwright install chromium` (browser binary download) as an execution-time setup step, separate from `uv sync`.
