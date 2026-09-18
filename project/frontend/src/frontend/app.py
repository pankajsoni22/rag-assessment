import streamlit as st

from frontend.ui import LOGO_PATH, apply_theme

st.set_page_config(page_title="RAG Assessment", page_icon="📚", layout="wide")
st.logo(str(LOGO_PATH), size="large")
apply_theme()

pg = st.navigation(
    [
        st.Page("pages/home.py", title="Home", icon=":material/home:", url_path="", default=True),
        st.Page(
            "pages/set_manager.py",
            title="Sets & Documents",
            icon=":material/folder_open:",
            url_path="sets",
        ),
        st.Page("pages/chat.py", title="Chat", icon=":material/chat:", url_path="chat"),
    ]
)
pg.run()
