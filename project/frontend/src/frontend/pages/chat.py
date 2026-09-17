from __future__ import annotations

import streamlit as st

from frontend.api_client import get_api_client
from frontend.models import ChatMessageView
from frontend.session_state import (
    append_message,
    get_chat_set_id,
    get_messages,
    get_session_id,
    set_chat_set_id,
)

st.title("Chat")

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
chosen_scope = st.selectbox(
    "Ask against",
    options=scope_options,
    index=scope_index,
    format_func=lambda sid: "Search everything" if sid is None else set_names[sid],
)
set_chat_set_id(chosen_scope)

for message in get_messages():
    with st.chat_message(message.role):
        st.write(message.content)
        if message.grounded is False:
            st.info("Not found in the documents.")
        if message.citations:
            sources = ", ".join(c.filename for c in message.citations)
            st.caption(f"Sources: {sources}")

question = st.chat_input("Ask a question about your documents")
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
                sources = ", ".join(c.filename for c in result.citations)
                st.caption(f"Sources: {sources}")
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
