# Phase 5: Backend — Retrieval & Generation Services (Plan)

Plan for Phase 5 of `specs/002-master-development-plan.md`: the Retrieval Service and Generation Service, built independently of each other. **Not yet implemented** — this document describes the intended design for review before any code is written.

## Decisions (confirmed with the user)

- **`groq`**, the official Python SDK, for the Generation Service's LLM client — thin, direct wrapper around Groq's chat completions endpoint. (Alternative considered: the `openai` SDK pointed at Groq's OpenAI-compatible `base_url` — rejected as a heavier, less idiomatic dependency for a Groq-only integration.)
- **Grounding check is a simple pre-check, not a prompt-based one**: if `RetrievalService` returns zero chunks, `GenerationService` skips calling Groq entirely and returns a fixed "not found in documents" `AnswerResult`. Cheap, deterministic, and testable without a live API call. A distance-threshold cutoff (not just "zero chunks") and any LLM-judged grounding are left as future tuning, same stance as chunk size/overlap in Phase 3.

## Domain Model Additions

`GenerationService`'s own responsibility (per `architecture.md`: "builds the prompt from the question, retrieved chunks, and conversation history") genuinely needs these now, not speculatively:

- `RetrievedChunk` — `chunk_id`, `document_id`, `text`, `metadata`, `distance`. What `RetrievalService` returns, mapping `VectorStore.query()`'s plain dicts into a real domain type for the rest of the backend to use.
- `Role` (enum: `USER`, `ASSISTANT`) and `ConversationTurn` — `role`, `content`, `timestamp`. `ConversationService` itself is Phase 6's job, but `GenerationService`'s signature needs the turn type now.
- `Citation` — `document_id`, `filename`, `chunk_id`.
- `AnswerResult` — `answer`, `citations: list[Citation]`, `grounded: bool`.

## RetrievalService

`backend/services/retrieval_service.py`. Depends on `EmbeddingService` and `VectorStore`.

- `EmbeddingService` gets a new method, `embed_query(text: str) -> list[float]`, alongside its existing `embed(chunks)` — both delegate to the same injected `EmbeddingClient`.
- `retrieve(query: str, set_id: str | None, top_k: int) -> list[RetrievedChunk]`:
  1. `embedding = self._embedder.embed_query(query)`
  2. `results = self._vector_store.query(embedding, top_k, where={"set_id": set_id} if set_id else None)`
  3. Map each result dict into a `RetrievedChunk`.

## GenerationService

`backend/services/generation_service.py`. Depends on an injected `GenerationClient` Protocol (mirrors `EmbeddingClient`'s pattern from Phase 3) — real implementation is `backend/clients/groq_client.py`.

- `generate(question: str, history: list[ConversationTurn], chunks: list[RetrievedChunk]) -> AnswerResult`:
  - If `chunks` is empty: return `AnswerResult(answer="I couldn't find anything in the documents to answer that.", citations=[], grounded=False)` — no Groq call.
  - Otherwise: build a prompt (system instruction to answer only from the provided context; retrieved chunk texts; prior turns; the question), call `self._client.complete(messages)`, build `Citation`s from each chunk's `document_id`/`metadata["filename"]`/`chunk_id`, return `AnswerResult(answer=..., citations=..., grounded=True)`.
- `GenerationClient` Protocol: `complete(messages: list[dict[str, str]]) -> str`.

## GroqClient

`backend/clients/groq_client.py`. Thin wrapper, same "not unit-tested against the live API" stance as `GeminiEmbeddingClient` (Phase 3) — needs a real `GROQ_API_KEY` to verify manually. Placeholder model: `llama-3.3-70b-versatile` (a current Groq-hosted model) — flagged as tunable, not an architectural commitment, matching how chunk size/overlap were handled.

## New Dependency

`groq>=0.11` added to `project/backend/pyproject.toml`.

## Testing Plan

- `RetrievalService` — integration-style test: real tmp-dir `ChromaVectorStore` (pre-populated via `upsert`) + a fake `EmbeddingClient`, verifying `set_id` scoping and top-k ordering. Same pattern as Phase 3/4's ingestion tests.
- `GenerationService` — unit tests with a fake `GenerationClient`: empty-chunks path returns the canned "not found" answer without calling the fake client; non-empty path calls the client and returns citations built from chunk metadata.
- `GroqClient` — no automated test (mirrors `GeminiEmbeddingClient`); manual verification once `GROQ_API_KEY` is real.

## Open Question Carried Forward

None outstanding for this phase — both forks (SDK choice, grounding check) are resolved above. Prompt wording/structure itself is an implementation detail to finalize during coding, not fixed here.
