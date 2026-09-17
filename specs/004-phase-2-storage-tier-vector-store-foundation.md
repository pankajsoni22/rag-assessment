# Phase 2: Storage Tier — Vector Store Foundation

Technical spec for Phase 2 of `specs/002-master-development-plan.md`: implement the `VectorStore` interface and its Chroma-backed implementation, the persistence foundation every backend data-touching service depends on.

## Decisions

- **Interface uses plain types only** — `dict[str, Any]`, `list[float]`, `str` — not backend domain classes (`Chunk`, etc., which don't exist yet and won't be built until Phase 3). This keeps Phase 1's "storage has zero dependency on backend" rule airtight even at the type-hint level: `storage` never imports anything from `backend`. A record is `{"id": str, "embedding": list[float], "text": str, "metadata": dict[str, Any]}`; a query result is a record plus a `"distance"` key (lower = more similar, following Chroma's own terminology rather than inventing a "score" with implied direction).
- **`VectorStore` is `@runtime_checkable`**, so conformance can be verified with `isinstance()` without requiring `ChromaVectorStore` to inherit from it — `storage` still never imports `backend.interfaces.vector_store`. Verified in `project/backend/tests/test_vector_store_interface.py` (backend already depends on storage for its future composition root, so this direction of import is fine).
- **Single Chroma collection (`"chunks"`)** for everything, matching `architecture.md`'s "no second database — metadata does the bookkeeping" principle. Scoping (e.g. to one set) and listing both go through the `where` metadata filter, not separate collections.
- **`hnsw:space="cosine"`** set explicitly at collection creation — Chroma's default is L2, but cosine is the standard choice for text embedding similarity (and what Gemini's embeddings are typically compared with).
- **No local embedding model ever invoked**: every `upsert`/`query` call passes explicit `embeddings=`/`query_embeddings=`, never `documents`-only or `query_texts`-only. This is what actually enforces the "no local model inference" tech-stack decision at the Chroma API level — passing only text would silently trigger Chroma's bundled ONNX embedding model.
- **No custom exception wrapping this phase.** A `VectorStoreError` was considered (to keep Chroma-specific exceptions from leaking through the abstraction) but deferred — there's no caller yet to need it, and it has nowhere non-coupled to live until a Phase 3+ service consumes the interface and can wrap at that boundary. Chroma's own exceptions propagate as-is for now.
- **Tests are real, not mocked** — a `tmp_path`-backed `chromadb.PersistentClient` per test, matching what actually runs in production (an embedded local database, not something worth mocking).

## What Was Created

- `project/backend/src/backend/interfaces/vector_store.py` — the `VectorStore` Protocol (`upsert`, `query`, `delete`).
- `project/storage/src/storage/chroma_vector_store.py` — `ChromaVectorStore`, backed by `chromadb.PersistentClient`.
- `project/storage/tests/test_chroma_vector_store.py` — upsert/query round trip, metadata-filtered query, idempotent upsert-by-id, delete-by-document, empty-store query, no-op empty upsert.
- `project/backend/tests/test_vector_store_interface.py` — `isinstance(ChromaVectorStore(...), VectorStore)` conformance check.
- Removed `project/storage/tests/test_placeholder.py` (Phase 1 placeholder, superseded by real tests).

## Verification (all passed)

- `uv run --package rag-storage pytest` — 6 passed.
- `uv run --package rag-backend pytest` — 2 passed (health check + interface conformance).
