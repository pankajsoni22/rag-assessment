# Phase 7: Frontend — API Client & Set/Document Manager UI

Plan and record for Phase 7 of `specs/002-master-development-plan.md`: the API Client (the frontend's sole HTTP bridge to the backend) and the Set & Document Manager UI, wired to Phase 4's ingestion endpoints.

**Status: implemented as described below**, with "Delete set" using a two-step confirm (click "Delete this set" → warning + Confirm/Cancel), resolving the Open Item. `uv run --package rag-frontend pytest` — 14 passed (`test_api_client.py` via `httpx.MockTransport`, `test_set_manager_page.py` via `AppTest` with a faked `ApiClient`). Live smoke test: real backend + real frontend started together, `/health` responded and the frontend served the navigation shell at `http://127.0.0.1:8502` with no errors in either log.

## Decisions (confirmed with the user)

- **`pydantic-settings`** for frontend config (`BACKEND_URL`), matching the pattern already used in `backend/config.py` — consistent across tiers, no new library to learn since it's already a backend dependency.
- **Streamlit multi-page structure set up now**, via `st.navigation`/`st.Page` (the current recommended API, not the legacy implicit `pages/` directory auto-discovery) — even though Chat (Phase 8) is still a placeholder, so Phase 8 only adds real content to an existing page rather than restructuring navigation.

## File Layout

```
project/frontend/src/frontend/
    app.py              # navigation entrypoint: st.navigation([...]).run()
    config.py            # Settings (pydantic-settings): BACKEND_URL, default http://127.0.0.1:8000
    api_client.py         # ApiClient — sole module speaking HTTP to the backend
    models.py              # frontend-local view dataclasses (DocumentSetView, DocumentView)
    session_state.py        # thin st.session_state helpers: session_id (generated once), selected_set_id
    pages/
        set_manager.py       # Set & Document Manager UI — real content, this phase
        chat.py                # placeholder page (Phase 1-style "coming soon"), real content in Phase 8
```

`models.py` mirrors backend's `DocumentSetResponse`/`DocumentResponse` shapes but is defined independently — frontend has zero dependency on backend code (per `architecture.md`), so it needs its own lightweight types, not a shared import.

`session_state.py` generates `session_id` once (needed by Phase 8's Chat, but logical to set up app-wide at this phase since multi-page nav already exists) and tracks `selected_set_id` (needed by this phase's own Set Manager page).

## ApiClient

`frontend/api_client.py`. Wraps an `httpx.Client(base_url=settings.backend_url)`. Methods, each raising on HTTP error (`response.raise_for_status()`) and parsing JSON into a `models.py` dataclass:

- `create_set(name: str) -> DocumentSetView`
- `list_sets() -> list[DocumentSetView]`
- `delete_set(set_id: str) -> None`
- `list_documents(set_id: str | None = None) -> list[DocumentView]`
- `upload_document(set_id: str, filename: str, content: bytes) -> DocumentView`
- `remove_document(document_id: str) -> None`

A `get_api_client()` provider, decorated with `st.cache_resource`, gives pages a singleton instance per app session rather than reconstructing an `httpx.Client` on every Streamlit rerun.

## Set & Document Manager UI

`frontend/pages/set_manager.py`.

- List existing sets (`api_client.list_sets()`); a small form to create a new one (text input + submit → `api_client.create_set`).
- Select a set (updates `session_state.selected_set_id`); once selected, list its documents (`api_client.list_documents(set_id=...)`) with filename/format/status.
- `st.file_uploader` + "Upload" button → `api_client.upload_document(...)`.
- "Remove" per document → `api_client.remove_document(document_id)`; "Delete set" → `api_client.delete_set(set_id)`.
- Every `api_client` call wrapped in `try/except`, failures shown via `st.error(str(exc))` — no broader error-handling framework, matching the minimal-necessary stance from earlier phases.

## New Dependency

`pydantic-settings` added to `project/frontend/pyproject.toml` (already a backend dependency).

## Configuration

`BACKEND_URL` added to root `.env.example`, default `http://127.0.0.1:8000`.

## Testing Plan (to be written when this phase is implemented)

- `ApiClient` — unit tests using `httpx.MockTransport` (no real server needed) to verify request shapes and response parsing per method — the frontend's equivalent of faking the one true external dependency (the network), same principle as backend's fake `EmbeddingClient`/`GenerationClient`.
- `set_manager.py` — `streamlit.testing.v1.AppTest` (already used in Phase 1's placeholder test), with `get_api_client` swapped for a fake via monkeypatching, asserting rendered widgets/values and that user actions (create set, upload, remove) call the fake with the right arguments.

## Open Items

- Exact table/layout styling for documents and sets is a UI-polish detail to settle during implementation, not fixed here.
- Whether "Delete set" needs a confirmation step (destructive action) is worth a quick decision at implementation time — not architectural, but worth not overlooking.
