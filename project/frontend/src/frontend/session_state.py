from __future__ import annotations

import uuid

import streamlit as st


def get_session_id() -> str:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id


def get_selected_set_id() -> str | None:
    return st.session_state.get("selected_set_id")


def set_selected_set_id(set_id: str | None) -> None:
    st.session_state.selected_set_id = set_id
