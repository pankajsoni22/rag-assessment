# Tech Stack

| Concern | Choice | Why |
|---|---|---|
| Language / backend framework | Python + FastAPI | Dominant ecosystem for RAG/LLM tooling; async; typed; splits cleanly into services later |
| RAG orchestration | LlamaIndex | RAG-focused framework; fastest path to a working chunking/retrieval/prompting pipeline |
| Embeddings | Google Gemini (`text-embedding-004`), free tier | No local model/compute; generous free daily quota via Google AI Studio; requires an API key and is rate-limited |
| Vector store | Chroma | Embedded/local file-based database — not a model, no inference runs locally; free, zero setup, no account needed |
| LLM (generation) | Groq API (free tier) | Free, fast inference of open models (e.g. Llama, Mixtral); requires an API key and is rate-limited |
| Frontend | Streamlit | Fast to build a working chat/query UI without full frontend engineering effort |

This is a deliberately free, no-local-model stack: no model inference (embeddings or generation) ever runs on this machine — both go through free-tier cloud APIs (Google Gemini, Groq), each rate-limited but acceptable for this project. Chroma is the one component that keeps state on local disk, but it's a plain embedded database, not a model. If either free tier stops being viable, revisit this table.

## Secrets
Two credentials, both read from environment variables via `.env` and never hardcoded, per `CLAUDE.md` rule 7:
- `GROQ_API_KEY` — LLM generation
- `GOOGLE_API_KEY` — Gemini embeddings

See `architecture.md` for how these pieces map onto the application's tiers and working model.
