from __future__ import annotations

import streamlit as st

from frontend.api_client import get_api_client
from frontend.models import ChatMessageView
from frontend.ui import empty_state, page_header
from frontend.session_state import (
    append_message,
    get_chat_set_id,
    get_messages,
    get_session_id,
    reset_conversation,
    set_chat_set_id,
)

_SUGGESTIONS = [
    "Summarize the key points of these documents",
    "What are the main topics covered?",
    "List any important dates, numbers or deadlines",
]


def _sources_line(citations) -> str:
    filenames = list(dict.fromkeys(c.filename for c in citations))
    return "Sources: " + " ".join(f":blue-badge[:material/description: {name}]" for name in filenames)


page_header(
    "Chat",
    "Answers are grounded only in your uploaded documents — if nothing relevant "
    "is found, you'll see an explicit <b>not found</b> notice instead of a guess.",
)

api_client = get_api_client()

try:
    sets = api_client.list_sets()
except Exception as exc:
    st.error(str(exc))
    sets = []

set_names = {s.id: s.name for s in sets}
scope_options = [None, *set_names.keys()]
current_scope = get_chat_set_id()
scope_index = scope_options.index(current_scope) if current_scope in scope_options else 0
scope_col, reset_col = st.columns([4, 1], vertical_alignment="bottom")
with scope_col:
    chosen_scope = st.selectbox(
        "Ask against",
        options=scope_options,
        index=scope_index,
        format_func=lambda sid: "Search everything" if sid is None else set_names[sid],
        help=(
            "Scope this question to one set, or search everything you've "
            "uploaded. Independent from the set selected on Sets & Documents."
        ),
    )
set_chat_set_id(chosen_scope)
with reset_col:
    if st.button(
        "New chat",
        icon=":material/add_comment:",
        use_container_width=True,
        help="Clear this conversation and start fresh.",
    ):
        reset_conversation()
        st.rerun()

if not sets:
    empty_state(
        "🗂️",
        "No document sets yet",
        "Create a set and upload a few documents, then come back to ask questions.",
    )
    if st.button("Go to Sets & Documents", icon=":material/folder_open:"):
        st.switch_page("pages/set_manager.py")

for message in get_messages():
    with st.chat_message(message.role):
        st.write(message.content)
        if message.grounded is False:
            st.info("Not found in the documents.")
        if message.citations:
            st.caption(_sources_line(message.citations))

# Resolve the question first (chat_input is pinned to the bottom regardless of
# where it is called) so the suggestions don't flash while an answer is generated.
pending_question = st.session_state.pop("pending_question", None)
question = st.chat_input("Ask a question about your documents") or pending_question

if sets and not get_messages() and not question:
    st.markdown("**Try asking**")
    for suggestion in _SUGGESTIONS:
        if st.button(suggestion, key=f"suggest-{suggestion}", icon=":material/lightbulb:"):
            st.session_state.pending_question = suggestion
            st.rerun()

if question:
    append_message(ChatMessageView(role="user", content=question))
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                result = api_client.ask(
                    question=question, set_id=chosen_scope, session_id=get_session_id()
                )
            st.write(result.answer)
            if result.grounded is False:
                st.info("Not found in the documents.")
            if result.citations:
                st.caption(_sources_line(result.citations))
            append_message(
                ChatMessageView(
                    role="assistant",
                    content=result.answer,
                    citations=result.citations,
                    grounded=result.grounded,
                )
            )
        except Exception as exc:
            st.error(str(exc))
            append_message(ChatMessageView(role="assistant", content=f"Error: {exc}"))
