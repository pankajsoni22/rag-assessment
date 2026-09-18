"""Shared presentation helpers: global styling and small layout components.

Presentation only - no API calls and no session state live here, so every page
can use these without coupling to the backend.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

ASSETS_DIR = Path(__file__).parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.svg"

_CSS = """
<style>
/* Tighter, calmer page frame */
.block-container { padding-top: 2.5rem; padding-bottom: 4rem; max-width: 62rem; }
h1 { font-weight: 750; letter-spacing: -0.02em; }
h2, h3 { letter-spacing: -0.01em; }

/* Hide Streamlit chrome we don't need */
#MainMenu, footer { visibility: hidden; }

/* Sidebar */
[data-testid="stSidebar"] { border-right: 1px solid #E5E7EF; }
[data-testid="stSidebarHeader"] { padding: 1.4rem 1rem 0.6rem 1.1rem; }
[data-testid="stSidebarHeader"] img { height: 2.6rem; }
[data-testid="stSidebarNav"] { padding-top: 0.5rem; }
[data-testid="stSidebarNav"] a {
    border-radius: 0.6rem; padding: 0.45rem 0.8rem; margin: 0.1rem 0.4rem;
    font-weight: 500; transition: background 120ms ease;
}
[data-testid="stSidebarNav"] a:hover { background: #E9EAF7; }
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: #E0E1FA; color: #3730A3; font-weight: 650;
}

/* Bordered containers become soft cards */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"] > .stElementContainer) {
    border-color: #E5E7EF;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 1rem;
}

/* Buttons */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
    border-radius: 0.65rem; font-weight: 600; transition: all 120ms ease;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.28);
}
.stButton > button:hover { transform: translateY(-1px); }

/* File uploader: Streamlit prints "<limit> per file • <types>" inside the dropzone.
   We deliberately don't advertise a size - the page says "small files" instead
   (supported types are listed in our own caption). */
[data-testid="stFileUploaderDropzoneInstructions"] { display: none; }

/* Chat */
[data-testid="stChatMessage"] { border-radius: 1rem; padding: 1rem 1.1rem; }
[data-testid="stChatInput"] { border-radius: 1rem; }

/* Landing page */
.hero { text-align: center; padding: 3rem 0 1.5rem; }
.hero .eyebrow {
    display: inline-block; padding: 0.3rem 0.85rem; border-radius: 999px;
    background: #EEF0FF; color: #4338CA; font-size: 0.8rem; font-weight: 650;
    letter-spacing: 0.04em; text-transform: uppercase;
}
.hero h1 {
    font-size: 3.2rem; line-height: 1.1; margin: 1.1rem 0 0.9rem; padding: 0;
    background: linear-gradient(120deg, #1E1B4B 10%, #4F46E5 90%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { max-width: 38rem; margin: 0 auto; font-size: 1.15rem; color: #4B5563; line-height: 1.6; }

.step-card {
    height: 100%; padding: 1.4rem 1.3rem; border: 1px solid #E5E7EF; border-radius: 1rem;
    background: #FFFFFF; box-shadow: 0 1px 2px rgba(30, 27, 75, 0.04);
    transition: box-shadow 160ms ease, transform 160ms ease, border-color 160ms ease;
}
.step-card:hover {
    box-shadow: 0 10px 28px rgba(79, 70, 229, 0.12); transform: translateY(-3px);
    border-color: #C7CAF5;
}
.step-card .num {
    display: inline-flex; align-items: center; justify-content: center;
    width: 2.1rem; height: 2.1rem; border-radius: 0.65rem; margin-bottom: 0.9rem;
    background: linear-gradient(135deg, #6366F1, #4338CA); color: #fff; font-weight: 700;
}
.step-card h4 { margin: 0 0 0.35rem; font-size: 1.05rem; }
.step-card p { margin: 0; color: #6B7280; font-size: 0.93rem; line-height: 1.5; }

.tip {
    max-width: 38rem; margin: 2rem auto 0.5rem; padding: 0.85rem 1.1rem; border-radius: 0.8rem;
    background: #FFFBEB; border: 1px solid #FDE68A; color: #78350F; font-size: 0.9rem; text-align: center;
}

/* Page headers */
.page-header { margin-bottom: 1.25rem; }
.page-header p { color: #6B7280; margin: 0.15rem 0 0; font-size: 1.02rem; }

/* Empty states */
.empty-state {
    text-align: center; padding: 2.2rem 1rem; border: 1.5px dashed #D5D8EE;
    border-radius: 1rem; background: #FAFAFF; color: #6B7280;
}
.empty-state .icon { font-size: 2rem; }
.empty-state strong { color: #1E1B4B; display: block; margin: 0.4rem 0 0.2rem; }
</style>
"""

_HIDE_SIDEBAR_CSS = """
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] { display: none; }
</style>
"""


def apply_theme() -> None:
    """Inject the global stylesheet. Call once from the app entrypoint."""
    st.markdown(_CSS, unsafe_allow_html=True)


def hide_sidebar() -> None:
    """Give the current page the full width (used by the landing page)."""
    st.markdown(_HIDE_SIDEBAR_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str) -> None:
    """Title + one-line subtitle. Uses st.title so the page keeps a real heading."""
    st.title(title)
    st.markdown(f'<div class="page-header"><p>{subtitle}</p></div>', unsafe_allow_html=True)


def empty_state(icon: str, title: str, hint: str) -> None:
    st.markdown(
        f'<div class="empty-state"><div class="icon">{icon}</div>'
        f"<strong>{title}</strong>{hint}</div>",
        unsafe_allow_html=True,
    )
