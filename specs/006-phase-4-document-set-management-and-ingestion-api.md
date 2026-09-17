# Phase 4: Document & Set Management + Ingestion API

Technical spec for Phase 4 of `specs/002-master-development-plan.md`: `DocumentSetService`, `IngestionService`, and the FastAPI endpoints exposing both. Completes the document-ingestion vertical slice end-to-end.

## Decisions

- **API contract: dedicated Pydantic DTOs per endpoint** (`backend/api/schemas.py`), not domain dataclasses serialized directly — confirmed with the user. Keeps the public API contract stable if internal domain classes change shape.
- **Uploaded files land in a `tempfile.NamedTemporaryFile`**, parsed, then discarded — confirmed with the user. No persistent upload storage; matches architecture.md's "a document only exists in Chroma once fully processed" framing.
- **Set/document bookkeeping is fully in-memory** (`DocumentSetService`), not partially derived from Chroma metadata as architecture.md originally sketched. Surfaced as a real gap during this phase: an empty, just-created `DocumentSet` has no chunks in Chroma to derive a name from. Resolved with the user: sets live in backend memory, same as the in-flight ingestion status architecture.md already called for — restart loses set *names*, but any already-uploaded documents keep their chunks in Chroma (findable by `set_id`) and aren't lost. Once that in-memory store existed anyway for sets, keeping full document bookkeeping (filename, format, status) there too avoided a second, partial "derive some things from Chroma, others from memory" derivation path.
- **Composition root is fully lazy** (`backend/api/dependencies.py`, `functools.lru_cache` providers wired via FastAPI `Depends`) — nothing constructs `Settings()`/`ChromaVectorStore`/`GeminiEmbeddingClient` at import time. This was necessary, not just nice-to-have: `test_health.py` already imports `backend.main`, and eager construction would have made every test require a real `.env`. Tests override providers via `app.dependency_overrides` instead of hitting real Gemini/needing real API keys.
- **Error handling split by expectedness**: `SetNotFoundError` → `404`, unsupported file extension → `400` (both normal, anticipated user errors). Unexpected pipeline failures (bad PDF, embedding API down) are left to bubble to FastAPI's default `500` — the document's `ERROR` status is still recorded via `IngestionService`'s try/except and stays inspectable via `GET /documents/{id}`. No broader error-handling framework built for scenarios that aren't expected to happen.
- **Routes stay synchronous `def`** (FastAPI runs them in a threadpool automatically) rather than `async def` — Chroma, pypdf, python-docx, and the Gemini client's default methods are all blocking, so `async def` would buy nothing without also async-wrapping each of those.
- **`python-multipart`** added as an explicit direct dependency (required for `UploadFile`; was previously only present transitively).

## What Was Created

- `backend/domain/models.py` — added `IngestionStatus`, `DocumentSet`, `Document`.
- `backend/loaders/registry.py` — added `format_from_filename()`.
- `backend/services/document_set_service.py` — `DocumentSetService` (+ `SetNotFoundError`, `DocumentNotFoundError`).
- `backend/services/ingestion_service.py` — `IngestionService`.
- `backend/api/dependencies.py` — lazy, cached provider functions (composition root).
- `backend/api/schemas.py` — `CreateSetRequest`, `DocumentSetResponse`, `DocumentResponse`.
- `backend/api/set_routes.py` — `POST/GET /sets`, `DELETE /sets/{id}`.
- `backend/api/document_routes.py` — `POST/GET /documents`, `GET/DELETE /documents/{id}`.
- `backend/main.py` — routers wired in.

## Verification (all passed)

- `uv run --package rag-backend pytest` — 39 passed (service unit tests using a real tmp-dir `ChromaVectorStore` + fake embedding client; API route tests via `TestClient` + `dependency_overrides`).
- Live smoke test: started the real server, hit `/health`, created and listed a set over real HTTP, and confirmed the upload path reaches the real composition root (fails at the real Gemini call with a fake key, as expected — the same error/`ERROR`-status path already covered by unit tests).
