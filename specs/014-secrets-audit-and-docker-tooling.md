# Secrets Audit & Docker Tooling

Final pre-handoff pass over what is pushed to GitHub, plus completing the
Docker setup and adding a simple start/stop command.

## 1. Secrets audit

**Scope:** every tracked file (including all of `project_transcripts/`),
the full git history (`git log -S`), the git remote config, and the built
Docker images.

**Method:** (a) regex scan for common credential shapes (Google `AIza…`,
Groq `gsk_…`, OpenAI/Anthropic `sk-…`, GitHub `ghp_`/`github_pat_`,
Slack, AWS `AKIA…`, PEM private keys, SSH keys, bearer tokens, long
`KEY/TOKEN/SECRET/PASSWORD` assignments); (b) value-based scan — the real
values in the local `.env` (never printed) searched for, in full and as
12/20/25-character prefixes/suffixes, in the working tree and in history.

**Findings**

| Item | Result |
|---|---|
| `.env` | Not tracked; gitignored; only `.env.example` (empty placeholders) is committed. |
| Full Groq / Google API key anywhere in tree or history | **None.** |
| Partial key fragments | **Found (fixed in tree).** One transcript (`…re-read-claudemd-and-get-yourself-familiar-with.txt`) contained a pydantic validation error that printed the first ~25 and last ~23 characters of both real API keys. Present in commits `4e25544`, `d062079`, `69cda89`, all already pushed. |
| GitHub PAT | None in the repo. An earlier session's transcript notes a PAT was pasted in chat and is already marked redacted; verified no `ghp_`/`github_pat_` string exists. |
| SSH private keys / public keys | None. Remote uses SSH (`git@github.com:…`); no credentials in the URL. |
| Public IPs | None (the Streamlit "External URL" line was not captured in tracked files). |
| Personal data | Two personal email addresses appear in one transcript (not credentials). Left as-is; redact if the repo is public and that matters. |
| Docker images | Neither image contains `.env` nor either key value (checked by filename and by grepping for the values). |

**Actions taken:** the two fragments were replaced with `[REDACTED-GROQ-KEY]`
/ `[REDACTED-GOOGLE-KEY]` in the working tree, and a re-scan found zero
remaining hits. A README "Security & Secrets" section records the rules.

**Not done (needs an explicit decision):** the fragments are still in the
git history. Removing them means rewriting history and force-pushing, which
the project rules forbid without explicit confirmation. Because ~80–90% of
each key is exposed, **rotate both keys** at the providers
(console.groq.com/keys, aistudio.google.com/apikey) regardless — rotation
makes history cleanup optional. If the earlier-pasted GitHub PAT is still
active, revoke it too.

## 2. Docker completeness

Reviewed the compose file and both Dockerfiles. Changes:
- Frontend health check added (`/_stcore/health`) so `up --wait` can confirm
  all three services.
- `restart: unless-stopped` on all services.
- Frontend image copies `.streamlit/` (done in spec 013) so config applies.
- Verified: build from a clean state, `depends_on` ordering by health,
  Chroma unpublished, no secrets in images, data persisted across `down`/`up`.

Known limitations (unchanged, deliberate): containers run as root; no TLS or
auth in front of the frontend/backend (local/assessment deployment);
compose project name stays `docker` (renaming it would orphan the existing
data volume).

## 3. `docker/rag.sh`

`up` / `down` / `down --purge` / `restart` / `status` / `logs` / `help`.
Placed in `docker/` (container tooling tier). `up` preflights Docker and
`.env` (creates it from `.env.example` when absent; errors clearly if either
key is empty, without printing values), then runs
`docker compose up --build -d --wait`. `down --purge` requires typing `yes`.
Documented in README *Running the Application → Option A*.
