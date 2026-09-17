# Phase 3: Backend — Ingestion Pipeline Internals

Technical spec for Phase 3 of `specs/002-master-development-plan.md`: the Document Loaders (Strategy pattern), Chunking, and Embedding Service — the pipeline stages that turn a raw file into vectors once wired to storage.

## Decisions

New dependencies confirmed with the user this session:
- **pypdf** for PDF text extraction — pure-Python, BSD-licensed, lightest option; `pdfplumber` and `PyMuPDF` considered and rejected (heavier/table-extraction features not needed; PyMuPDF is AGPL-3.0, a licensing concern).
- **llama-index-core only** (not the full `llama-index` metapackage) for the Chunking stage's `SentenceSplitter` — avoids pulling in unused vector-store/LLM vendor integrations, since our own `RAGOrchestrator`/`VectorStore`/Gemini/Groq wrappers already do that job.
- **google-genai** (Google's current unified SDK) over the older `google-generativeai` for the Gemini embeddings client.
- **python-docx** for `.docx` parsing — decided without a separate question; it's the de facto standard with no real lighter alternative for structured Word parsing.

Design decisions:
- **First real content in `domain/`, `interfaces/document_loader.py`, `loaders/`, `services/`, `clients/`** — these subpackages didn't exist after Phase 1/2 by design (created just-in-time). This phase only adds `DocumentFormat` and `Chunk` to the domain model — `Document`, `DocumentSet`, `IngestionStatus` etc. are deferred to Phase 4, which is the first phase that actually needs them.
- **`DocumentLoader` and loaders live entirely inside `backend`** (no cross-tier boundary), so — unlike `VectorStore` — they freely use the real `DocumentFormat` domain enum in their signatures; the plain-dict-only rule from Phase 2 was specifically about the backend/storage packaging boundary, not internal backend modules.
- **`EmbeddingService` takes an injected `EmbeddingClient` Protocol**, tested with a fake client — the real `GeminiEmbeddingClient` (thin wrapper, `backend/clients/gemini_client.py`) calls a paid/free-tier external API requiring a real key, which isn't available in this environment; it's intentionally left without an automated test and flagged for manual verification once `GOOGLE_API_KEY` is set. This mirrors Phase 2's stance of "mock only what truly can't run locally," rather than mocking Chroma (which could and did run for real).
- **Chunk size/overlap defaults (512/50)** are explicitly placeholders — architecture.md's Open Items already defers this as a tuning decision to make once there's a working pipeline to test against, not an architectural one.
- **`ChunkingService` filters out empty/whitespace-only pieces** — LlamaIndex's `SentenceSplitter.split_text("")` returns `['']` rather than `[]`, which would otherwise produce a stray empty chunk.
- **PDF test fixtures are generated with `pypdf` alone** (via its low-level object API in `tests/conftest.py`), not a separate PDF-writing dependency — verified working empirically before committing to the approach.

## Environment Fix

`llama-index-core` depends on `nltk`, whose data loader refuses to open files with `st_nlink > 1` as a hardlink-based security precaution (CWE-59) — which is exactly how `uv`'s default hardlinked install leaves every site-packages file. Fixed by setting `link-mode = "copy"` in the root `pyproject.toml`'s `[tool.uv]` table (required a full `.venv` rebuild once; new `uv sync` runs pick it up automatically).

## What Was Created

- `backend/domain/models.py` — `DocumentFormat` (enum), `Chunk` (dataclass).
- `backend/interfaces/document_loader.py` — `DocumentLoader` Protocol.
- `backend/loaders/` — `TextLoader`, `MarkdownLoader`, `PdfLoader`, `WordLoader`, `DocumentLoaderRegistry` + `default_registry()`.
- `backend/services/chunking_service.py` — `ChunkingService` (LlamaIndex `SentenceSplitter`).
- `backend/services/embedding_service.py` — `EmbeddingService` + `EmbeddingClient` Protocol.
- `backend/clients/gemini_client.py` — `GeminiEmbeddingClient`.
- Tests for all of the above, plus `tests/conftest.py` fixtures (`make_pdf`, `make_docx`).

## Verification (all passed)

- `uv run --package rag-backend pytest` — 20 passed (loaders, registry, chunking, embedding service).
- `uv run --package rag-storage pytest` / `rag-frontend pytest` — unaffected, still green (6 / 1 passed).
- `GeminiEmbeddingClient` is **not** covered by automated tests — needs manual verification against the real Gemini API once a key is available.
