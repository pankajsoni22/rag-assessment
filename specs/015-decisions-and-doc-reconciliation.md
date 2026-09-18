# Decisions Log & Documentation Reconciliation

Written 2026-09-18 after reading the four session transcripts in
`project_transcripts/` against the current docs and code. Purpose: (1) record
decisions that were made during development but never written into the plan,
architecture or requirements, and (2) correct docs that had drifted from what
was built. The user-facing summary of the assumptions is `ABOUT.md`.

## 1. Requests handled in this change
1. **`ABOUT.md`** added at the repo root: every assumption the app makes, tagged
   *Decided* (user) or *Default* (chosen without review), plus known limitations
   and open questions.
2. **Docs reconciled** with the transcripts and the code (section 3).
3. **UI no longer mentions file size.** The page asks for "small files".
   Streamlit's built-in dropzone line ("10MB per file • PDF, DOCX, TXT, MD")
   is hidden with CSS (`[data-testid="stFileUploaderDropzoneInstructions"]`,
   verified against Streamlit 1.64's compiled component, not in a browser) and
   replaced by our own caption naming the formats. The 10 MB ceiling still
   exists in `.streamlit/config.toml`; Streamlit's own rejection message for
   an oversized file would still contain the number (not customizable
   without a workaround — accepted). Tests assert no size text in the page.

## 2. Decisions made during development

### Confirmed with the user (in the transcripts)
| Decision | Where recorded before | Status |
|---|---|---|
| Fine-grained backend phases; explicit final integration phase | spec 002 | already recorded |
| Backend-only low-level design; domain/service classes only, no DTOs in UML | `backend-low-level-design.md` | already recorded |
| `uv`, one package per tier, Python 3.12 | spec 003 | already recorded |
| `pypdf`, `llama-index-core` only, `google-genai` | spec 005 | already recorded |
| Dedicated Pydantic DTOs; tempfile for uploads; **sets in memory** | spec 006 | recorded, but `architecture.md` still said Chroma metadata → **fixed** |
| `groq` SDK; zero-chunk pre-check for "not found" | spec 007 | already recorded |
| `pydantic-settings` in frontend; multi-page scaffold now; independent chat selector | specs 009, 010 | already recorded |
| Playwright E2E (not a manual checklist) | spec 011 | already recorded |
| Data directory `data/` at repo root, all four formats | none | now in `ABOUT.md` 4.11 |
| Block same-file re-upload; replace on changed content; multi-file upload; vector cleanup on delete | none (code only) | **now in spec 001 amendments, architecture, `ABOUT.md`** |
| "Use small files" guidance, no size numbers; show rate-limit errors; back-off with jitter; longer delays | none | **now in spec 001 amendments, `ABOUT.md`** |
| Containerize; Chroma in its own container; user installs Docker | spec 012 | already recorded |

### Made without asking (defaults) — now documented and flagged for review
Chunk size/overlap 512/50; top-k 5; cosine distance; temperature 0; the
system prompt; **no relevance threshold**; Groq model `openai/gpt-oss-120b`;
Gemini model `gemini-embedding-001`; Gemini batch size 100, 120 s timeout,
6 attempts/45 s max back-off; Groq 4 retries; 300 s frontend timeout; 10 MB
upload ceiling; synchronous ingestion and routes; sequential multi-upload;
one session per browser tab, unbounded history; set names not unique; sets not
renamable; light theme; Chroma pinned to 1.5.9; no non-root containers.
Table with locations: `architecture/architecture.md` → *Implementation
Decisions & Defaults*.

## 3. Documentation corrections

| File | Was | Now |
|---|---|---|
| `architecture/architecture.md` | Said set/document bookkeeping is Chroma metadata | Registry is in memory (per spec 006); consequence documented; duplicate/replace semantics; decisions table; open items updated |
| `architecture/tech-stack.md` | `text-embedding-004`; "Llama/Mixtral" | Actual models; tooling row added |
| `architecture/backend-low-level-design.md` | API/DTO design "deferred" | Marked resolved; drift from diagram noted |
| `specs/001-…requirements.md` | Declared final | Amendments table for post-spec user requests |
| `specs/002, 006, 007, 009, 012` | — | Short pointers/notes appended (later changes, consequences) |
| `README.md`, `docker/rag.sh`, `specs/014` | **Claimed uploaded documents survive `down`/`up`** | Corrected: registry resets, vectors remain (see below) |

## 4. Defect found while reconciling (not fixed — needs a decision)
The set/document registry is in memory but Chroma's data persists on a Docker
volume. Verified on the running stack: after a `down`/`up` the API returned
`[]` for `/sets` and `/documents` while Chroma's `chunks` collection still held
10 vectors. Effects: previously uploaded documents disappear from the UI but
still influence "Search everything" answers, and cannot be deleted from the UI.
Workaround: `./docker/rag.sh down --purge`. Options for a real fix are listed
in `ABOUT.md` §6 (persist the registry, or rebuild it from Chroma on startup).
The user chose in-memory in Phase 4 without this consequence being raised.

## 5. Other findings recorded as limitations (not fixed)
Follow-up questions retrieve on the raw question only; "not found" only
triggers on an empty scope; conversation history is unbounded.
