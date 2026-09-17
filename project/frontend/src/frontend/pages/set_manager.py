from __future__ import annotations

import streamlit as st

from frontend.api_client import get_api_client
from frontend.session_state import get_selected_set_id, set_selected_set_id

st.title("Sets & Documents")
st.caption(
    "Create a set, then upload documents to it. Once a document shows "
    "**ready**, you can ask questions about it on the Chat page."
)
st.info(
    "📄 **Use small files.** This app runs on free-tier Gemini/Groq APIs with "
    "strict rate limits — a small PDF or plain text file (a few pages) is far "
    "more likely to process successfully than a large or scanned document. "
    "Uploads are capped at 10MB.",
    icon="ℹ️",
)

api_client = get_api_client()

st.subheader(
    "Sets",
    help="A set groups related documents so you can scope your questions to just that group later, in Chat.",
)

with st.form("create_set_form", clear_on_submit=True):
    new_set_name = st.text_input(
        "New set name", help="A short, descriptive name, e.g. 'HR Policies' or 'Research Papers'."
    )
    submitted = st.form_submit_button("Create set")
    if submitted and new_set_name:
        try:
            api_client.create_set(new_set_name)
            st.success(f"Created set '{new_set_name}'.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

try:
    sets = api_client.list_sets()
except Exception as exc:
    st.error(str(exc))
    sets = []

if not sets:
    st.info("No sets yet. Create one above.")
else:
    set_names = {s.id: s.name for s in sets}
    options = list(set_names.keys())
    selected_id = get_selected_set_id()
    index = options.index(selected_id) if selected_id in options else 0
    chosen_id = st.selectbox(
        "Select a set",
        options=options,
        index=index,
        format_func=lambda sid: set_names[sid],
        help="The set to view, upload to, or manage documents for.",
    )
    set_selected_set_id(chosen_id)

    if st.button("Delete this set"):
        st.session_state.confirm_delete_set = chosen_id

    if st.session_state.get("confirm_delete_set") == chosen_id:
        st.warning(
            f"Delete set '{set_names[chosen_id]}' and all its documents? This can't be undone."
        )
        confirm_col, cancel_col = st.columns(2)
        with confirm_col:
            if st.button("Confirm delete", type="primary"):
                try:
                    api_client.delete_set(chosen_id)
                    st.session_state.confirm_delete_set = None
                    set_selected_set_id(None)
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with cancel_col:
            if st.button("Cancel"):
                st.session_state.confirm_delete_set = None
                st.rerun()

    st.subheader(
        f"Documents in '{set_names[chosen_id]}'",
        help=(
            "**processing** — being read and indexed (embedded) · "
            "**ready** — indexed and available for questions in Chat · "
            "**error** — couldn't be processed (see the message shown at upload time)"
        ),
    )

    uploaded_file = st.file_uploader(
        "Upload a document",
        type=["pdf", "docx", "txt", "md"],
        help="PDF, Word, plain text, or Markdown. Prefer small, text-based files — see the note above.",
    )
    if uploaded_file is not None and st.button("Upload"):
        try:
            with st.spinner(f"Uploading and processing '{uploaded_file.name}'..."):
                api_client.upload_document(chosen_id, uploaded_file.name, uploaded_file.getvalue())
            st.success(f"Uploaded '{uploaded_file.name}'.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    try:
        documents = api_client.list_documents(set_id=chosen_id)
    except Exception as exc:
        st.error(str(exc))
        documents = []

    if not documents:
        st.info("No documents in this set yet.")
    else:
        for document in documents:
            name_col, format_col, status_col, action_col = st.columns([3, 1, 1, 1])
            name_col.write(document.filename)
            format_col.write(document.format)
            status_col.write(document.status)
            if action_col.button("Remove", key=f"remove-{document.id}"):
                try:
                    api_client.remove_document(document.id)
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
