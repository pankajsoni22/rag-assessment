# Phase 6: Conversation Service, RAG Orchestrator & Query API

Plan and record for Phase 6 of `specs/002-master-development-plan.md`: the Conversation Service, the RAG Orchestrator tying Conversation/Retrieval/Generation together, and the FastAPI query endpoint. Completes the question-answering vertical slice end-to-end.

**Status: implemented as described below**, with `top_k` defaulted to `5` (placeholder, per the Open Items tuning deferral). `uv run --package rag-backend pytest` — 58 passed (up from 46 after Phase 5), including `test_conversation_service.py`, `test_rag_orchestrator.py`, and `test_query_routes.py`. The composition root (`backend/api/dependencies.py`) was refactored to share a single cached `EmbeddingService` between ingestion and retrieval rather than constructing a `GeminiEmbeddingClient` twice.

This design builds directly on `architecture/backend-low-level-design.md` and the (also not-yet-implemented) Phase 5 plan, `specs/007-phase-5-retrieval-and-generation-services.md`, which already defines the domain types (`RetrievedChunk`, `ConversationTurn`, `Role`, `Citation`, `AnswerResult`) and the `RetrievalService`/`GenerationService` signatures this phase's `RAGOrchestrator` will call.

## Domain Model

No new types needed — `ConversationTurn`/`Role`, added in the Phase 5 plan, are exactly what `ConversationService` stores and returns.

## ConversationService

`backend/services/conversation_service.py`. Pure in-memory, no dependencies — `dict[str, list[ConversationTurn]]` keyed by `session_id`, per `architecture.md`'s "in-flight... conversation history live in backend process memory" decision (restart-tolerant, matches the single-user/no-accounts scope). No cap on history length planned for this phase — flagged as a future tuning concern (same stance as chunk size in Phase 3), not an architectural one.

- `get_history(session_id: str) -> list[ConversationTurn]` — returns `[]` for an unseen session, not an error.
- `append_turn(session_id: str, turn: ConversationTurn) -> None`.

## RAGOrchestrator

`backend/services/rag_orchestrator.py`. Depends on `ConversationService`, `RetrievalService`, `GenerationService` — the only module aware of the full question-answering sequence (Orchestrator pattern), matching `architecture.md`'s sequence diagram.

`answer_question(session_id: str, question: str, set_id: str | None) -> AnswerResult`:
1. `history = conversation_service.get_history(session_id)`
2. `chunks = retrieval_service.retrieve(question, set_id, top_k=...)`
3. `result = generation_service.generate(question, history, chunks)`
4. Append both the user's question and the assistant's answer as `ConversationTurn`s — appended regardless of whether the answer was grounded, so "not found" exchanges still count as history.
5. Return `result`.

## Query API

`backend/api/query_routes.py` + an addition to `backend/api/schemas.py`.

- `POST /query` — request DTO `{question: str, set_id: str | None, session_id: str}`; response DTO mirrors `AnswerResult` (`answer`, `citations`, `grounded`).
- `session_id` is required in the request, not server-generated — per `architecture.md`'s Session State module (owned by the frontend, Phases 7–8), which creates and holds it client-side. This phase's own tests will generate a UUID themselves, the same way a real frontend eventually will.
- If `set_id` is provided and doesn't match an existing set (via `DocumentSetService.get_set`), return `404` — the same expected-error-gets-a-4xx pattern established in Phase 4 for uploads, for consistency.
- Composition root: extend `backend/api/dependencies.py` with lazy, cached providers for `ConversationService` and `RAGOrchestrator`, following the exact pattern already used for `DocumentSetService`/`IngestionService`.

## Testing Plan (to be written when this phase is implemented)

- `ConversationService` — plain unit tests (get/append, unseen session returns `[]`).
- `RAGOrchestrator` — unit tests using fakes for `RetrievalService`/`GenerationService` (isolating orchestration logic from already-tested collaborators) plus a real `ConversationService`, verifying call order and that both turns get appended.
- Query API — `TestClient` + `app.dependency_overrides`, same pattern as Phase 4's route tests, including the `set_id`-not-found → `404` case.

## Open Items

- Exact `top_k` value for retrieval — still an explicit tuning deferral from `architecture.md`'s own Open Items, not resolved here.
- Whether a max conversation-history length/token budget is needed — noted as a future concern, not decided now.
