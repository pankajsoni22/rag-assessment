# About This Project

A Retrieval-Augmented Generation (RAG) application: bring your own documents, ask questions in plain language, get answers grounded in those documents, with sources. This file records **the assumptions this application deliberately makes** — what it is, what it is not, and the defaults it runs on — so nobody has to rediscover them from the code.

- How to run it → [`README.md`](README.md)
- How it is built → [`architecture/architecture.md`](architecture/architecture.md), [`architecture/tech-stack.md`](architecture/tech-stack.md)
- What was required → [`specs/001-rag-generator-requirements.md`](specs/001-rag-generator-requirements.md)
- Full change/decision log → [`specs/015-decisions-and-doc-reconciliation.md`](specs/015-decisions-and-doc-reconciliation.md)

## How to read this file

Every assumption is tagged with where it came from:

| Tag | Meaning |
|---|---|
| **Decided** | You (Pankaj) chose it explicitly, in the requirements or in a design question. |
| **Default** | A sensible value was picked during implementation without asking you. It works, but you have not reviewed it — treat it as a proposal and change it if you disagree. |

---

## 1. Product & scope

| # | Assumption | Source |
|---|---|---|
| 1.1 | **Single user, no accounts, no login.** Nothing separates one person's documents from another's; anyone who can reach the app sees everything. | Decided |
| 1.2 | **Supported formats: PDF, Word (.docx), plain text, Markdown** — a deliberate launch scope, not an oversight. Other formats (e.g. PowerPoint) are rejected with a clear message. | Decided |
| 1.3 | **New formats must be additive.** Each format is one loader class behind a shared interface, so adding one never touches existing formats or already-loaded documents. | Decided |
| 1.4 | **Documents are grouped into sets; by default no set is selected** and a question searches everything. Selecting a set scopes the question to it. | Decided |
| 1.5 | **Sets are editable any time** — documents can be added to or removed from an existing set. (Sets cannot currently be renamed.) | Decided |
| 1.6 | **Multi-turn memory:** a follow-up question is understood in the context of the conversation so far. | Decided |
| 1.7 | **Retention:** a user can delete a document or a whole set at any time; nothing expires automatically. | Decided |
| 1.8 | **Answers must be grounded in the documents, with citations** (document names), and the app must say so when the documents don't cover a question rather than guess. | Decided |
| 1.9 | **Text only.** PDFs are read as text (no OCR, no tables/layout/images), so scanned PDFs usually fail with "no readable text content". | Decided (no layout preservation) / Default (no OCR) |
| 1.10 | **Out of scope:** editing or generating documents, unprompted summaries, anything not driven by a user question. | Decided |
| 1.11 | **Uploading the exact same file twice into a set is blocked.** A same-named file with *different* content replaces the old one (old vectors are deleted only after the new version ingests successfully). Duplicates are judged per set, by filename + SHA-256 of content. | Decided (block duplicates by filename; replace on changed content) |
| 1.12 | **Several files can be uploaded in one click**; they are processed one after another, not in parallel. | Decided (multi-upload) / Default (sequential) |
| 1.13 | **Removing a document or set removes its vectors** from the vector store, so it stops being used to answer questions and no stale data remains. | Decided |
| 1.14 | **The UI never states a file-size limit** — it just asks for *small files*. (A hard 10 MB ceiling still exists underneath; see 4.6.) | Decided |

## 2. Technology

| # | Assumption | Source |
|---|---|---|
| 2.1 | **Free cloud APIs only; no model runs locally** — not for embeddings, not for generation. Rate limits are accepted as a fact of life. | Decided |
| 2.2 | **LLM: Groq** (free tier). Current model `openai/gpt-oss-120b` — the originally planned Llama model was no longer in the account's catalogue. | Decided (Groq) / Default (model) |
| 2.3 | **Embeddings: Google Gemini** (free tier). Current model `gemini-embedding-001` — the originally named `text-embedding-004` was superseded. | Decided (Gemini) / Default (model) |
| 2.4 | **Vector store: Chroma** (not a model, so allowed). Embedded in-process for local development; its own container under Docker. | Decided |
| 2.5 | **Backend: Python + FastAPI, LlamaIndex** (only `llama-index-core`, for chunking). **Frontend: Streamlit.** | Decided |
| 2.6 | **Tooling:** `uv`, Python 3.12, one package per tier (backend, storage, frontend), `pypdf` for PDFs, `google-genai` and `groq` official SDKs, `pydantic-settings` for config in both backend and frontend. | Decided |
| 2.7 | **API shape:** dedicated Pydantic request/response models per endpoint; uploads go through a temp file that is deleted after ingestion; routes are synchronous (the libraries underneath are blocking). | Decided (DTOs, temp file) / Default (sync routes) |
| 2.8 | **Containers:** Docker + Compose, one container per tier, **Chroma in its own container** (the first tier split out of the backend process). You install Docker yourself. Images: `python:3.12-slim`; Chroma pinned to `1.5.9` to match the client. | Decided |
| 2.9 | **Frontend structure:** multi-page Streamlit app; the Chat page has its own set selector, independent of the one on Sets & Documents. | Decided |

## 3. Data & state

| # | Assumption | Source |
|---|---|---|
| 3.1 | **Sets, the document list and ingestion status live in backend memory only.** They reset whenever the backend restarts. (Originally planned as Chroma metadata; changed because an empty set has no chunks to derive from.) | Decided |
| 3.2 | **Conversation history is in-memory per session** and does not survive a restart; a "session" is one browser tab. **New chat** starts a fresh session. | Decided (in-memory) / Default (per tab) |
| 3.3 | **If ingestion is interrupted, the user re-uploads.** A document only appears in the vector store once fully processed. | Decided |
| 3.4 | **No second database.** The only persistent store is Chroma (chunks, embeddings, and per-chunk metadata: document, set, filename, format, upload time). | Decided |
| 3.5 | **Original uploaded files are not kept** — only their extracted text chunks. | Decided |

## 4. Behavioural defaults (not reviewed by you)

These are tuning values and behaviours picked so the pipeline works end-to-end. All are **Default**.

| # | Default | Effect / where |
|---|---|---|
| 4.1 | **Chunking:** sentence-aware, 512 tokens with 50 overlap. | `services/chunking_service.py` |
| 4.2 | **Retrieval:** top 5 chunks, cosine similarity; no re-ranking, no hybrid/keyword search. | `services/rag_orchestrator.py`, `storage/_chroma_collection.py` |
| 4.3 | **Generation:** temperature 0 (consistent answers, per requirement B1.2); one fixed system prompt telling the model to answer only from context. | `clients/groq_client.py`, `services/generation_service.py` |
| 4.4 | **"Not found" rule:** the fixed "couldn't find anything" answer is returned only when retrieval returns *zero* chunks. There is no similarity threshold, so otherwise the model itself decides whether the context is enough (see 5.3). | `services/generation_service.py` |
| 4.5 | **Rate-limit handling:** Gemini — batches of 100 texts, 120 s timeout, up to 6 attempts with exponential backoff + jitter (max 45 s between tries). Groq — up to 4 retries (SDK backoff with jitter). A 429/503 surfaces to the UI as a plain rate-limit message. The backoff itself was requested; the numbers are defaults. | `clients/gemini_client.py`, `clients/groq_client.py` |
| 4.6 | **Upload ceiling:** Streamlit is configured to reject files over 10 MB (`.streamlit/config.toml`), and the frontend waits up to 300 s for an upload or answer. The size is not advertised in the UI. | `.streamlit/config.toml`, `frontend/api_client.py` |
| 4.7 | **Ingestion is synchronous:** the upload request returns when the document is ready or has failed, so the *Processing* status is rarely visible to the user. | `api/document_routes.py` |
| 4.8 | **Set names are not required to be unique** (the placeholder asks for a unique name, but nothing enforces it). | `services/document_set_service.py` |
| 4.9 | **Secrets** live only in `.env` (git-ignored); `.env.example` has empty placeholders; `.env` is excluded from Docker images. | `.gitignore`, `.dockerignore` |
| 4.10 | **Exposure:** the frontend (8501) and backend (8000) publish ports to the host; Chroma does not. No TLS or authentication; containers run as root. Suitable for a local/assessment deployment only. | `docker/docker-compose.yml` |
| 4.11 | **Sample documents** (one per format, under ~200 lines) live in `data/` at the repo root for manual testing. | `data/` |
| 4.12 | **Visual design:** light theme only, indigo palette, landing page as the default route. | `.streamlit/config.toml`, `frontend/ui.py` |

## 5. Known limitations (consequences of the above)

1. **Restart leaves invisible vectors.** Because sets/documents are in memory (3.1) but vectors persist in Chroma's volume, after a backend restart the UI lists nothing while old vectors remain searchable under "Search everything" and cannot be deleted from the UI. `./docker/rag.sh down --purge` is the clean-slate workaround. *Verified: after a restart the API listed no sets while Chroma still held vectors.*
2. **Follow-ups retrieve on the raw question only.** Conversation history is sent to the LLM, but retrieval searches with just the latest question text — "what about contractors?" may retrieve poorly (no query rewriting).
3. **Weak "not found" detection.** With any non-empty scope retrieval always returns 5 chunks, so an unrelated question is answered by the model's own judgement, and the response is still marked grounded and shows citations for whatever was retrieved. There is no relevance threshold.
4. **History is unbounded.** Every prior turn is sent to the LLM and sessions are never evicted from memory.
5. **Free-tier fragility.** Large or scanned documents commonly hit rate limits or fail; small text-based files work best.
6. **Real Gemini/Groq calls are not covered by automated tests** (both are faked for determinism and cost); verify manually with real keys. The browser E2E suite (Playwright) has not been run in the development sandbox for lack of system libraries.

## 6. Open questions for you

These need a decision before they change; nothing has been altered.

1. **Restart behaviour (5.1):** persist the set/document registry (e.g. in Chroma metadata plus a small registry), rebuild it from Chroma on startup, or accept the limitation and document it?
2. **"Not found" (4.4 / 5.3):** add a similarity-distance threshold so unrelated questions get the explicit "not found" answer?
3. **Follow-up retrieval (5.2):** rewrite the question using the conversation history before searching?
4. **Tuning (4.1–4.2):** review chunk size/overlap and top-k against your real documents.
