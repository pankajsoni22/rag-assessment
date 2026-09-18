from __future__ import annotations

import uuid

import streamlit as st

from frontend.models import ChatMessageView


def get_session_id() -> str:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id


def get_selected_set_id() -> str | None:
    return st.session_state.get("selected_set_id")


def set_selected_set_id(set_id: str | None) -> None:
    st.session_state.selected_set_id = set_id


def get_chat_set_id() -> str | None:
    return st.session_state.get("chat_set_id")


def set_chat_set_id(set_id: str | None) -> None:
    st.session_state.chat_set_id = set_id


def get_messages() -> list[ChatMessageView]:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    return st.session_state.messages


def append_message(message: ChatMessageView) -> None:
    get_messages().append(message)


def reset_conversation() -> None:
    """Drop the transcript and rotate the session id so backend memory resets too."""
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
