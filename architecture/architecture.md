# Architecture

The working model of the application (module boundaries, data flow, tier responsibilities in detail) will be added here as the design takes shape. For now, this holds the initial tier mapping. See `tech-stack.md` for technology choices and why.

## Tier Mapping
- `project/backend/` — FastAPI app; the LlamaIndex pipeline (ingestion, chunking, retrieval, prompting); the Groq and Gemini client wrappers.
- `project/storage/` — Chroma persistence.
- `project/frontend/` — Streamlit app.

Each tier talks to the others through clear interfaces (not direct imports across tier internals), so any tier can later be pulled out into its own service without a rewrite.
