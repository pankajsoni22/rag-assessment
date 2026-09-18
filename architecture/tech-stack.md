# Tech Stack

| Concern | Choice | Why |
|---|---|---|
| Language / backend framework | Python + FastAPI | Dominant ecosystem for RAG/LLM tooling; async; typed; splits cleanly into services later |
| RAG orchestration | LlamaIndex | RAG-focused framework; fastest path to a working chunking/retrieval/prompting pipeline |
| Embeddings | Google Gemini (`text-embedding-004`), free tier | No local model/compute; generous free daily quota via Google AI Studio; requires an API key and is rate-limited |
| Vector store | Chroma | Free, zero-account database; runs embedded (local dev) or as its own server (Docker) — see below |
| LLM (generation) | Groq API (free tier) | Free, fast inference of open models (e.g. Llama, Mixtral); requires an API key and is rate-limited |
| Frontend | Streamlit | Fast to build a working chat/query UI without full frontend engineering effort |
| Containerization | Docker + Docker Compose | Packages each tier as its own image/container for a reproducible run, without changing the free-tier/no-local-model stack above |

This is a deliberately free, no-local-model stack: no model inference (embeddings or generation) ever runs anywhere — both go through free-tier cloud APIs (Google Gemini, Groq), each rate-limited but acceptable for this project. If either free tier stops being viable, revisit this table.

### Chroma: embedded vs. server

Chroma runs in one of two modes, chosen by config, not by code changes at the call site (see `architecture.md`'s *Storage Tier*):
- **Local (non-Docker) development** — embedded, an in-process file-based
  library (`chromadb.PersistentClient`). No separate process, zero setup.
- **Docker Compose** — its own container, the official `chromadb/chroma`
  image, reached over HTTP (`chromadb.HttpClient`). This is the first tier
  actually split out of the backend process, in service of the "structured
  so it can later be split into a distributed deployment" goal.

Client and server versions are pinned to match (`chromadb==1.5.9` resolved
in `uv.lock`; `docker/docker-compose.yml` pins `chromadb/chroma:1.5.9`) —
Chroma's wire protocol isn't guaranteed stable across major versions.

## Secrets
Two credentials, both read from environment variables via `.env` and never hardcoded, per `CLAUDE.md` rule 7:
- `GROQ_API_KEY` — LLM generation
- `GOOGLE_API_KEY` — Gemini embeddings

See `architecture.md` for how these pieces map onto the application's tiers and working model.
