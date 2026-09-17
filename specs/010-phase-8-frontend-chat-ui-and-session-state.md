# Phase 8: Frontend — Chat UI & Session State (Plan)

Plan for Phase 8 of `specs/002-master-development-plan.md`: the Chat UI, wired to Phase 6's query endpoint. Completes the full user-facing product. **Not yet implemented** — this document describes the intended design for review before any code is written.

This phase extends files Phase 7 already plans to create (`api_client.py`, `models.py`, `session_state.py`, `pages/chat.py`'s placeholder) rather than creating a parallel set — see `specs/009-phase-7-frontend-api-client-and-set-document-manager-ui.md`.

## Decision (confirmed with the user)

- **Chat gets its own independent set-scope selector**, separate from the Set Manager page's `selected_set_id` (Phase 7). Defaults to `None` ("search everything," per spec A2.8). Browsing/uploading-to-a-set and scoping-a-question are different intents — e.g. browsing Set A's documents while asking a question across everything shouldn't silently change based on the other page's state.

## Session State Additions

`frontend/session_state.py` (extending Phase 7's module, not replacing it):
- `chat_set_id: str | None` — the new independent chat-scope selector.
- `messages: list[ChatMessageView]` — a **local, transient display buffer** for the current browser session. There's no `GET` history endpoint on the backend (Phase 6's API is `POST /query` only, which returns just the new answer, not the full transcript) — the backend's `ConversationService` is still the authority used for grounding future answers, but the frontend keeps its own copy purely to render the conversation. A hard page refresh resets both `session_id` (Phase 7) and `messages` together — the old backend-side session becomes orphaned but harmless, the same "restart loses in-memory state, user just continues" tradeoff already accepted elsewhere (e.g. Phase 4's ingestion status).

## Domain Additions (`frontend/models.py`)

- `CitationView` — `document_id`, `filename`, `chunk_id` (mirrors backend's `Citation`, independently defined per the frontend's zero-backend-dependency rule).
- `AnswerView` — `answer`, `citations: list[CitationView]`, `grounded: bool` (mirrors `AnswerResult`).
- `ChatMessageView` — `role` ("user"/"assistant"), `content`, `citations: list[CitationView] | None`, `grounded: bool | None` — what `messages` actually stores, covering both user questions and assistant answers in one shape.

## ApiClient Addition

`frontend/api_client.py` gets one new method:
- `ask(question: str, set_id: str | None, session_id: str) -> AnswerView` — `POST /query`, same raise-on-error/parse-into-dataclass pattern as Phase 7's other methods.

## Chat UI

`frontend/pages/chat.py` — replaces Phase 7's placeholder with real content.

- Set-scope selector (`chat_set_id`) at the top of the page — a dropdown of existing sets (via `api_client.list_sets()`) plus a "Search everything" option mapping to `None`.
- Render `session_state.messages` using Streamlit's native chat primitives (`st.chat_message("user")` / `st.chat_message("assistant")`), citations listed under each assistant answer, and a distinct visual treatment (e.g. `st.info`) when `grounded is False` for the explicit "not found in documents" state required by spec A4.18/B7.12.
- `st.chat_input` for the question box.
- On submit: append the user's message to `session_state.messages` immediately (so it renders before the backend responds), call `api_client.ask(...)`, append the assistant's response (or an error bubble on failure — same try/except-then-`st.error`-equivalent pattern as Phase 7, adapted to a chat bubble instead of a page-level banner) to `session_state.messages`, rerender.

## Testing Plan (to be written when this phase is implemented)

- `ApiClient.ask` — unit test via `httpx.MockTransport`, same pattern as Phase 7's other `ApiClient` methods.
- `chat.py` — `AppTest`-based tests with `get_api_client` swapped for a fake: submitting a question renders both the user and assistant bubbles, citations render when present, the "not found" state renders distinctly when `grounded=False`, and the independent `chat_set_id` selector doesn't affect/get affected by `selected_set_id` from the Set Manager page.

## Open Items

- Whether the chat transcript should be capped/scrollable for very long sessions is a UI-polish concern for implementation time, not decided here — mirrors the "no history cap" deferral already made for `ConversationService` in the Phase 6 plan.
