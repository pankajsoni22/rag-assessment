# Frontend UX Refresh

Request: the sidebar felt plain, "How it works" didn't belong in it, and the
app needed a landing page and a more polished feel overall.

## Changes
- **Landing page** (`pages/home.py`, default route `/`): hero, four "How it
  works" step cards, a tip about small files, and a
  **Start With RAG Assessment Project** button that switches to
  Sets & Documents. Sidebar is hidden on this page only.
- **Sidebar**: "How it works" removed. Now just an SVG logo/wordmark
  (`assets/logo.svg`, via `st.logo`) and icon navigation (Home, Sets &
  Documents, Chat) with a styled active state.
- **Theme**: indigo palette via `.streamlit/config.toml` `[theme]`; extra CSS
  in `frontend/ui.py`. No new dependencies, no external fonts/CDNs.
- **Sets & Documents**: shared page header, coloured status badges, empty
  states, Material icons instead of emoji.
- **Chat**: suggested starter questions, "New chat" button, source badges
  (de-duplicated), empty state when no sets exist.
- **Routes**: pages now have explicit `url_path`s (`/`, `/sets`, `/chat`);
  e2e tests navigate to `/sets` instead of relying on it being the default.
- **Docker**: the frontend image now copies `.streamlit/` — previously the
  Streamlit config (including the 10MB upload limit) was not applied in the
  container.

## Not done / caveats
- Visual result not screenshot-verified in this environment (no browser);
  unit tests cover behaviour via Streamlit `AppTest`. E2E suite updated but,
  as before, not run here.
- Light theme only.
