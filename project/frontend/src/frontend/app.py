import streamlit as st

st.set_page_config(page_title="RAG Assistant")

st.sidebar.markdown(
    "**How it works**\n\n"
    "1. Create a Set\n"
    "2. Select a Set\n"
    "3. Upload Document(s) to it\n"
    "4. Ask a question about the Set in Chat"
)
st.sidebar.divider()

pg = st.navigation(
    [
        st.Page("pages/set_manager.py", title="Sets & Documents", default=True),
        st.Page("pages/chat.py", title="Chat"),
    ]
)
pg.run()
