# Project Transcript — 2026-09-17 (session 2)

Session covering: writing the functional and non-functional requirements
specification for the RAG Generator, in plain language.

> Note: reconstructed, human-readable transcript from conversation context
> (no raw session-export tool available), not a byte-for-byte log. Tool
> calls are summarized as action notes rather than reproduced verbatim. Same
> caveat as the prior transcript in this directory.

---

## 1. Initial request

**User** asked for a detailed functional and non-functional specification
for the "RAG Generator" problem statement (accepts documents at runtime,
builds a RAG app over them, answers questions grounded in those documents,
works with different document sets without code changes) — explicitly in
plain language, no technicalities, covering everything an engineer would
need "from a to z."

**Assistant**: read the existing (empty) `specs/rag-assessment.md`,
`architecture/architecture.md`, and `architecture/tech-stack.md` to pick up
context (tech stack already decided: FastAPI, LlamaIndex, Gemini
embeddings, Chroma, Groq, Streamlit — deliberately excluded from the spec
since the user wanted plain-language requirements only), confirmed
`specs/` naming convention (serial-number prefix), and wrote
`specs/001-rag-generator-requirements.md`: Purpose, Who Uses This, Scope,
Functional Requirements (document intake, set organization, processing,
Q&A, usability), Non-Functional Requirements (correctness, format
independence, responsiveness, reliability, growth, privacy, clarity,
maintainability), and an Open Questions list for things that were genuinely
ambiguous rather than assumed.

Left the pre-existing empty `specs/rag-assessment.md` untouched rather than
deleting/renaming it unasked.

---

## 2. User's correction and follow-up

**User** (via inline edit in the IDE) corrected one requirement: by
default no document set should be pre-selected — an answer can come from
any relevant document; the user can optionally select a set to scope a
question. Then said the open questions "need to be clear to complete these
requirements" and to go on.

**Assistant**: applied the correction to `A2` (renumbering the functional
requirements list from 23 items to stay consistent), then asked the
remaining open questions in two rounds via structured questions:

**Round 1** (4 questions):
- Single-user vs. multi-user → **User: single user, no accounts.**
- Document formats at launch → **User: PDF, Word, Text, Markdown** — with
  an explicit instruction to record that this was a deliberate scope
  decision (not an oversight), and that the code must be built so new
  formats (e.g. PowerPoint) can be added later with minimal changes and
  without breaking backward compatibility.
- Can a set be edited after creation → **User: yes, editable anytime.**
- Multi-turn conversation memory required → **User: yes.**

**Round 2** (1 question, held back from round 1 to avoid overloading):
- Document deletion / retention policy → **User: deletable anytime by the
  user; kept indefinitely otherwise, no auto-expiry.**

**Assistant**: folded all five decisions into the spec (formats list in
A1.2 with the deliberate-choice note, set editability in A2.11, multi-turn
memory in A4.19, retention in B6.11, and a new maintainability requirement
B8.14 requiring new-format support to be addable without reworking existing
format handling or breaking already-loaded documents), removed the now-
resolved Open Questions section, and replaced it with a **Decisions Log**
table dated 2026-09-17 marking the spec final pending future amendments.

Flagged for the user: the "extensible to new formats" instruction is partly
an architectural concern (how the ingestion code is shaped, e.g. a
pluggable per-format loader) that belongs in `architecture/architecture.md`
once that module is actually designed, per the project's own documentation
rule that architecture decisions live there and not in specs — not yet
written since no ingestion design exists yet. Asked the user whether to add
a forward-looking note now or wait.

---

## 3. Transcript-saving gap noticed

**User**: opened this directory's existing transcript file and asked
whether transcripts were being saved per `CLAUDE.md`.

**Assistant**: checked `CLAUDE.md`, found Documentation Instructions #4
("All my discussions in chat should be saved in project_transcripts in md
files as it is") — a rule not present in the copy of `CLAUDE.md` loaded at
the start of this conversation, so it had not been followed during this
session. Acknowledged the gap directly, noted the same "no raw export tool"
caveat the prior transcript file already documents, and wrote this file to
backfill session 2 and resume compliance going forward.

---

## 4. Filename convention for transcripts

**User**: made a further edit to `CLAUDE.md`, appending to rule 4: "keep
name of the file as name of the chat tab."

**Assistant**: had no way to read the IDE's chat tab name/title from the
available tools, so asked the user to supply it directly (after an initial
malformed single-option question was rejected by the question tool and
corrected).

**User**: edited `CLAUDE.md` again — replaced the tab-name instruction
with a concrete fixed path for now: save to
`D:\online_assessment\develope_rag_model\project_transcripts\2026-09-17-functional-requirements-spec.md`.
Then asked the assistant to re-read `CLAUDE.md` and apply it.

**Assistant**: re-read `CLAUDE.md`, confirmed the specified path already
matched this file exactly (no rename needed), and appended this section to
keep the transcript current per the rule.

---

## 5. Committing and pushing session work

**User**: asked to commit and push to git.

**Assistant**: checked `git status`/`diff`, confirmed `.env` stayed
correctly gitignored, staged `CLAUDE.md` plus all the untracked
documentation (`.env.example`, `README.md`, `architecture/`,
`project_transcripts/`, `specs/001-rag-generator-requirements.md`),
committed, and pushed to `origin/main` (`630683d..93a619b`).

---

## 6. Designing the application architecture

**User**: asked to design the application's architecture — modules, how
they interact, diagrams if possible.

**Assistant**: before finalizing, asked three data-model questions since
they were genuine architectural decisions rather than things to assume:
- How to track document/set metadata (filenames, status, set membership)
  → **User: Chroma metadata only, no second database.**
- Whether conversation history needs to survive a backend restart →
  **User: in-memory per session is enough.**
- Whether an in-flight "processing" ingestion status needs to be
  recoverable after a crash → **User: no, re-upload is acceptable.**

With those settled, wrote the full design into `architecture/architecture.md`,
replacing the earlier placeholder: guiding principles, backend modules table
(API layer, Document & Set Management, Ingestion, Document Loaders behind a
shared interface, Chunking, Embedding, Retrieval, Generation, Conversation,
RAG Orchestrator, Config), the storage tier design (Chroma-only, metadata
carried on each chunk, no second store), the frontend modules (API Client,
Set/Document Manager UI, Chat UI, Session State), the design patterns used
(Strategy for loaders, Adapter/Repository for the vector store, a thin
service layer, an Orchestrator for the query flow), a Mermaid component
diagram, and two Mermaid sequence diagrams (document ingestion; question
answering). Left API route design and retrieval/prompt tuning as open items
for when the backend is actually scaffolded.
