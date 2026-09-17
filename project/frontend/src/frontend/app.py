import streamlit as st

st.set_page_config(page_title="RAG Assistant")

pg = st.navigation(
    [
        st.Page("pages/set_manager.py", title="Sets & Documents", default=True),
        st.Page("pages/chat.py", title="Chat"),
    ]
)
pg.run()
