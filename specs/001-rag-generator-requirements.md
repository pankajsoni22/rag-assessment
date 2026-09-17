# 001 - RAG Generator: Requirements Specification

## Purpose

Build a tool that lets a person bring their own set of documents, have the
tool learn those documents, and then ask questions about them in natural
language. The answers must come from what is actually written in the
documents (not made up), and the tool must work the same way no matter what
documents are loaded — nobody should have to change the tool itself to point
it at a new set of files.

## Who Uses This

- **A regular user**: someone who has a set of documents and wants answers
  from them without reading the whole thing.
- Single-person tool: no accounts, no login, no separation between
  different people's documents. (Decided 2026-09-17.)

## Scope

In scope: loading documents, asking questions about them, getting grounded
answers back.

Out of scope unless we decide otherwise: editing documents, generating new
documents, summarizing an entire document unprompted, anything not driven by
a user's question.

---

## A. Functional Requirements

### A1. Bringing In Documents
1. A user can add one or more documents to the tool while it is running —
   no code changes, no restart, no developer involvement.
2. The tool should accept these document formats at launch: PDF, Word
   files, plain text, and Markdown. This is a deliberate, scoped-down
   choice for launch, not an oversight — the tool should be built so that
   support for further formats (e.g. PowerPoint) can be added later with
   minimal changes and without breaking the formats already supported.
   (Decided 2026-09-17.)
3. A user can add more than one document at a time, and documents can be of
   different formats within the same set.
4. The tool should tell the user clearly when a document was added
   successfully, and clearly when it was not (e.g. wrong format, unreadable
   file, empty file).
5. A user should be able to see what documents are currently loaded.
6. A user should be able to remove a document they previously added, and the
   tool should stop using it to answer questions after that.

### A2. Organizing Documents Into Sets
7. Documents can be organized into "sets" (a collection put together for one
   purpose, e.g. "HR Policies" or "Product Manuals") so a user can scope
   their questions when they want to.
8. By default, no set is selected: a question can be answered using any
   relevant document across everything the user has loaded. A user can
   optionally select a specific set to scope a question to just that set.
9. A user can create a new set and add documents to it.
10. Switching between "search everything" and a specific set must not
    require any change to the tool itself — this is the core requirement of
    the whole project.
11. A set can be edited after creation: documents can be added to or removed
    from an existing set at any time, not just when it's first created.
    (Decided 2026-09-17.)

### A3. Understanding the Documents
12. After documents are added, the tool must process them so it "knows" their
    content well enough to answer questions about it, without a person
    manually summarizing or tagging anything first.
13. This processing should happen automatically after upload, with some
    indication to the user that it's in progress and when it's done.
14. The tool should handle reasonably large documents and reasonably large
    sets of documents without needing special handling from the user.

### A4. Asking Questions
15. A user can type a question in plain language and get an answer.
16. The answer must be grounded in the loaded documents — it should reflect
    what the documents actually say, not general knowledge or guesses.
17. The tool should show the user where an answer came from (e.g. which
    document, and ideally which part of it), so the answer can be checked.
18. If the documents don't contain enough information to answer a question,
    the tool must say so clearly instead of guessing or making something up.
19. A user should be able to ask a follow-up question that makes sense in the
    context of the conversation so far — the tool must remember prior
    questions and answers in the session so a question like "what about for
    contractors?" is understood in that context, not answered as if it
    were the first question asked. (Decided 2026-09-17.)
20. The tool should give an answer in a reasonable amount of time — a user
    should not be left wondering if it's stuck.

### A5. Everyday Usability
21. The tool should have a simple screen/interface: a way to manage
    documents and sets, and a way to ask questions and read answers. No
    technical steps should be required from the user.
22. Error messages shown to the user should be in plain language, not
    technical error codes or jargon.
23. A user should be able to tell, at a glance, whether they are currently
    asking against everything or against one specific set — and if a set,
    which one.

---

## B. Non-Functional Requirements

### B1. Correctness & Trustworthiness
1. Answers must stay faithful to the source documents; the tool should avoid
   presenting invented information as fact.
2. The tool should behave consistently — asking the same question against
   the same set of documents should give a consistent, dependable answer.

### B2. Works With Any Document Set
3. Nothing about the tool's behavior should be specific to one particular
   set of documents. A brand-new, never-seen-before set of documents should
   work exactly as well as one used during development, with zero setup
   changes.

### B3. Responsiveness
4. Adding a document and getting it ready for questions should complete
   within a reasonable, predictable time relative to its size.
5. Getting an answer to a question should feel responsive in normal
   conversation, not like a long wait.

### B4. Reliability
6. The tool should keep working correctly as more documents and more sets
   are added over time, not degrade or become unstable.
7. If something goes wrong (e.g. an unreadable file, a temporary hiccup),
   the tool should fail gracefully with a clear message rather than
   crashing or leaving the user stuck.

### B5. Growth
8. The tool should be able to grow from small use (one person, a handful of
   documents) toward heavier use (more documents, more sets, potentially
   more users) without needing to be rebuilt from scratch.

### B6. Privacy & Data Handling
9. Documents a user uploads are theirs — the tool should not use them for
   anything other than answering that user's questions.
10. Anything sensitive (credentials, access to outside services the tool
    depends on) must never be exposed to the end user or shown in the
    interface.
11. A user can delete an uploaded document or an entire set at any time.
    Nothing is deleted automatically on a timer — data is kept indefinitely
    until the user removes it. (Decided 2026-09-17.)

### B7. Clarity & Trust in Answers
12. The tool should make it easy for a user to distinguish "the documents
    answer this" from "the documents don't cover this."

### B8. Maintainability
13. The tool should be organized so that individual pieces of it (handling
    documents, understanding questions, showing results) can be improved,
    replaced, or scaled independently later without reworking the entire
    tool.
14. Adding support for a new document format in the future should be a
    small, contained change — it must not require reworking how existing
    formats are handled, and must not break documents already loaded in
    formats supported today. (Decided 2026-09-17, in response to the
    launch format list in A1.2.)

---

## Decisions Log

All open questions from the first draft have been resolved with Pankaj on
2026-09-17:

| Question | Decision |
|---|---|
| Single user or multi-user? | Single user, no accounts |
| Document formats at launch? | PDF, Word, plain text, Markdown — deliberately scoped, with room to add more formats later without breaking changes |
| Can a set be edited after creation? | Yes, editable anytime |
| Multi-turn conversation required? | Yes, with memory of prior questions in the session |
| Document deletion / retention? | Deletable anytime by the user; kept indefinitely otherwise, no auto-expiry |

This spec is considered final as of this decisions log. Any further change
to scope should be proposed as an amendment here, not silently implemented.
