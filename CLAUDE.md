# Keep In Mind
I am Pankaj Soni, a generative AI engineer. My task is to develop a RAG (Retrieval-Augmented Generation) model following best practices. The project will be modular: initially built as a monolith, but structured so it can later be split into a distributed deployment. Write code that is decoupled, scalable, and testable from the start.

# Tech Stack
Not yet decided. Once a language/framework/vector-store choice is made, record it here (and in `architecture/`) so it stays the single source of truth — don't let the two drift apart.

# Project Instructions
1. All project code lives inside the `project` directory.
2. Within `project`, follow a multi-tier structure with separate directories per tier (e.g. `backend`, `frontend`, `storage`/`store` for the persistence layer — propose a better name if one fits) plus any other tier the project needs.
3. Files belong only in the directory for their tier — e.g. anything data-related goes under the storage/database directory, not scattered elsewhere.
4. If it's unclear which tier or directory a file/entity belongs in, ask before creating it.
5. Write clean, object-oriented code using appropriate design patterns and principles — favor composition and clear interfaces between tiers so they can be split apart later without a rewrite.
6. Write unit tests for both backend and frontend code.
7. Never hardcode secrets, API keys, or credentials. Keep them in environment variables (e.g. `.env`, excluded via `.gitignore`) and commit a `.env.example` with placeholder values instead.

# Collaboration & Decision-Making
1. Always ask before proceeding on any non-trivial or architectural decision (tier boundaries, module structure, choice of libraries/patterns, data models) rather than assuming — this extends rule 4 above beyond just file placement.
2. Always ask before adding a new external dependency/package. State what it's for and any lighter-weight alternative considered.
3. For trivial, clearly-scoped follow-ups within an already-agreed plan, proceed without re-confirming.

# Version Control
1. Initialize and maintain a git repository for this project at `https://github.com/pankajsoni22/rag-assessment.git`.
2. Commit at logical checkpoints (e.g. a completed module, a passing test suite) with clear, descriptive messages — not one giant commit at the end.
3. Standard safety rules apply: never force-push, rewrite history, or run destructive git commands without explicit confirmation.

# Documentation Instructions
1. Maintain the architecture document; any change that affects the architecture must be reflected there, in the `architecture` directory.
2. Save planning-related documents in the `specs` directory, filenames prefixed with a serial number and named for the feature they describe (e.g. `001-document-ingestion-pipeline.md`).
