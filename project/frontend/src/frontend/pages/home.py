from __future__ import annotations

import streamlit as st

from frontend.ui import hide_sidebar

hide_sidebar()

_STEPS = [
    ("1", "Create a set", "Group related documents under one name, like “HR Policies” or “Research Papers”."),
    ("2", "Select the set", "Pick the set you want to work in so uploads land in the right place."),
    ("3", "Upload documents", "Add PDF, Word, text or Markdown files. They're read, chunked and indexed for you."),
    ("4", "Ask in Chat", "Ask in plain language and get answers grounded in your files, with sources."),
]

st.markdown(
    """
    <div class="hero">
      <span class="eyebrow">Retrieval-Augmented Generation</span>
      <h1>Ask your documents.<br/>Trust the answers.</h1>
      <p>Upload your files, ask questions in plain language, and get answers grounded
      only in what you uploaded — with the sources to prove it.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

_, cta_col, _ = st.columns([1, 1.4, 1])
with cta_col:
    if st.button(
        "Start With RAG Assessment Project",
        type="primary",
        icon=":material/arrow_forward:",
        use_container_width=True,
    ):
        st.switch_page("pages/set_manager.py")

st.write("")
st.markdown("<h3 style='text-align:center'>How it works</h3>", unsafe_allow_html=True)
st.write("")

for column, (number, title, text) in zip(st.columns(len(_STEPS), gap="medium"), _STEPS):
    column.markdown(
        f'<div class="step-card"><div class="num">{number}</div>'
        f"<h4>{title}</h4><p>{text}</p></div>",
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="tip">💡 <b>Tip:</b> use small, text-based files. This app runs on free-tier '
    "APIs with strict rate limits, so a few pages process far more reliably than a large "
    "or scanned document.</div>",
    unsafe_allow_html=True,
)
