# Master Development Plan

This document defines the **phases** of development for the RAG application, in the order they should be built, and why that order was chosen. It does **not** prescribe technical details — libraries, class designs, API schemas, or data models for any phase. Each phase gets its own detailed spec file (`specs/00X-<phase-name>.md`), created just before work on that phase begins, once this ordering is agreed.

The ordering below follows the dependency graph described in `architecture/architecture.md`: each phase only depends on tiers/modules already built in an earlier phase, so at every point there is a working, testable increment rather than a pile of interdependent unfinished pieces.

Unit tests for a phase's own code are written as part of that phase (per `CLAUDE.md`'s testing rule) — testing is not a separate phase.

---

## Phase 1 — Project Scaffolding & Environment Setup

Create the `project/backend`, `project/storage`, and `project/frontend` tier directories per the architecture's tier mapping. Wire up environment/secrets loading (`.env`, excluded via `.gitignore`, with `.env.example` kept current). Set up dependency management and base automated-test scaffolding for both backend and frontend, so every later phase has a place to add code and tests from day one.

**Depends on:** nothing — first phase.

---

## Phase 2 — Storage Tier: Vector Store Foundation

Implement the `VectorStore` interface and its Chroma-backed implementation (upsert, query, delete, with metadata filtering). This is the persistence foundation that every backend service touching data depends on, so it's built before any of those services.

**Depends on:** Phase 1.

---

## Phase 3 — Backend: Ingestion Pipeline Internals

Build the Document Loaders (one per format — PDF, Word, plain text, Markdown — behind a shared interface), the Chunking stage, and the Embedding Service (Gemini). These are the internal pipeline stages that turn a raw file into vectors once wired to storage.

**Depends on:** Phase 2 (the pipeline's output is written to the VectorStore).

---

## Phase 4 — Backend: Document & Set Management + Ingestion API

Build the Document & Set Management Service (create/list/delete sets and documents, ingestion status tracking) and the Ingestion Service that orchestrates Loader → Chunking → Embedding → VectorStore. Expose both through the FastAPI API layer. This completes the document-ingestion vertical slice end-to-end.

**Depends on:** Phase 3.

---

## Phase 5 — Backend: Retrieval & Generation Services

Build the Retrieval Service (similarity search against the VectorStore, with optional set scoping) and the Generation Service (Groq LLM wrapper). These two are independent of each other and can be built in either order within this phase.

**Depends on:** Phase 2 (Retrieval reads from the VectorStore). Exercising retrieval meaningfully also benefits from ingested data produced in Phase 4.

---

## Phase 6 — Backend: Conversation Service, RAG Orchestrator & Query API

Build the Conversation Service (in-memory multi-turn history) and the RAG Orchestrator that coordinates Conversation, Retrieval, and Generation for the "answer a question" use case. Expose it through the FastAPI query endpoint. This completes the question-answering vertical slice end-to-end.

**Depends on:** Phase 5.

---

## Phase 7 — Frontend: API Client & Set/Document Manager UI

Build the API Client (the frontend's sole HTTP bridge to the backend — nothing else in the frontend talks to the backend directly) and the Set & Document Manager UI (create/select sets, upload documents, show status, remove documents), wired to the Phase 4 endpoints.

**Depends on:** Phase 4 (endpoints to call against) and Phase 1 (frontend scaffolding).

---

## Phase 8 — Frontend: Chat UI & Session State

Build the Chat UI (question input, answer + citations display, explicit "not found in documents" state) and Session State handling, wired to the Phase 6 query endpoint. This completes the full user-facing product.

**Depends on:** Phase 6 (query endpoint) and Phase 7 (API Client, frontend scaffolding already in place).

---

## Phase 9 — Integration & Hardening

Verify both vertical slices (ingestion and question-answering) end-to-end through the real UI across all three tiers. Pass against the non-functional requirements in `specs/001-rag-generator-requirements.md` (reliability, error clarity, privacy/retention, etc.) before considering the MVP complete.

**Depends on:** Phase 8.

---

## Next Steps

Before starting Phase 1, create `specs/003-phase-1-project-scaffolding-and-environment-setup.md` with the technical plan for that phase. Each subsequent phase gets its own spec file in the same way, numbered sequentially with a `phase-<n>-` tag, immediately before that phase's work begins.
