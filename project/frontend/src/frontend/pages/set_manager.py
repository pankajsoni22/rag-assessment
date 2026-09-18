from __future__ import annotations

import streamlit as st

from frontend.api_client import get_api_client
from frontend.session_state import get_selected_set_id, set_selected_set_id
from frontend.ui import empty_state, page_header

_STATUS_BADGE = {
    "ready": ":green-badge[:material/check_circle: Ready]",
    "processing": ":orange-badge[:material/hourglass_top: Processing]",
    "error": ":red-badge[:material/error: Error]",
}

page_header(
    "Sets & Documents",
    "Create a set, then upload documents to it. Once a document shows "
    "<b>ready</b>, you can ask questions about it in Chat.",
)
st.info(
    "**Use small files.** This app runs on free-tier Gemini/Groq APIs with "
    "strict rate limits — a small PDF or plain text file (a few pages) is far "
    "more likely to process successfully than a large or scanned document.",
    icon=":material/info:",
)

api_client = get_api_client()

with st.container(border=True):
    st.subheader(
        ":material/folder_open: Step 1 · Create or choose a set",
        help="A set groups related documents so you can scope your questions to just that group later, in Chat.",
    )

    with st.form("create_set_form", clear_on_submit=True):
        form_col, button_col = st.columns([4, 1], vertical_alignment="bottom")
        with form_col:
            new_set_name = st.text_input(
                "New set name",
                placeholder="Write a unique name for this set, e.g. 'HR Policies'",
                help="A short, descriptive name, e.g. 'HR Policies' or 'Research Papers'.",
                label_visibility="collapsed",
            )
        with button_col:
            submitted = st.form_submit_button(
                "Create set", icon="➕", use_container_width=True
            )
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
        empty_state("🗂️", "No sets yet", "Create your first set above to get started.")
    else:
        set_names = {s.id: s.name for s in sets}
        options = list(set_names.keys())
        selected_id = get_selected_set_id()
        index = options.index(selected_id) if selected_id in options else 0

        select_col, delete_col = st.columns([4, 1], vertical_alignment="bottom")
        with select_col:
            chosen_id = st.selectbox(
                "Select a set",
                options=options,
                index=index,
                format_func=lambda sid: set_names[sid],
                help="The set to view, upload to, or manage documents for.",
            )
        set_selected_set_id(chosen_id)
        with delete_col:
            if st.button("Delete this set", icon="🗑️", use_container_width=True):
                st.session_state.confirm_delete_set = chosen_id

        if st.session_state.get("confirm_delete_set") == chosen_id:
            st.warning(
                f"Delete set '{set_names[chosen_id]}' and all its documents? This can't be undone."
            )
            confirm_col, cancel_col = st.columns(2)
            with confirm_col:
                if st.button("Confirm delete", type="primary", use_container_width=True):
                    try:
                        api_client.delete_set(chosen_id)
                        st.session_state.confirm_delete_set = None
                        set_selected_set_id(None)
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            with cancel_col:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.confirm_delete_set = None
                    st.rerun()

if sets:
    st.write("")  # breathing room between the two sections

    with st.container(border=True):
        st.subheader(f":material/upload_file: Step 2 · Upload documents to '{set_names[chosen_id]}'")

        st.caption("PDF, Word (.docx), plain text or Markdown · small files work best.")

        if "uploader_key" not in st.session_state:
            st.session_state.uploader_key = 0

        uploaded_files = st.file_uploader(
            "Upload document(s)",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
            help=(
                "PDF, Word, plain text, or Markdown. Select multiple files to "
                "upload and process them all with a single click. Prefer small, "
                "text-based files — see the note above."
            ),
            key=f"uploader_{st.session_state.uploader_key}",
            label_visibility="collapsed",
        )
        if uploaded_files and st.button("Upload", icon="⬆️", type="primary"):
            successes: list[str] = []
            failures: list[tuple[str, str]] = []
            progress = st.progress(0.0)
            for i, uploaded_file in enumerate(uploaded_files):
                # Uploaded one at a time, not in parallel: each upload triggers
                # real Gemini/Groq API calls on the backend, and this app runs
                # on rate-limited free tiers - firing them concurrently would
                # only make rate limiting worse.
                with st.spinner(
                    f"Uploading and processing '{uploaded_file.name}' "
                    f"({i + 1}/{len(uploaded_files)})..."
                ):
                    try:
                        api_client.upload_document(
                            chosen_id, uploaded_file.name, uploaded_file.getvalue()
                        )
                        successes.append(uploaded_file.name)
                    except Exception as exc:
                        failures.append((uploaded_file.name, str(exc)))
                progress.progress((i + 1) / len(uploaded_files))
            progress.empty()

            if successes:
                st.success(f"Uploaded: {', '.join(successes)}")
            for name, error in failures:
                st.error(f"'{name}': {error}")

            # Give the file_uploader a fresh key so it doesn't keep holding the
            # just-uploaded files after rerun - otherwise a stray extra click on
            # Upload would resubmit the same batch.
            st.session_state.uploader_key += 1
            st.rerun()

        st.divider()

        st.caption(
            "**Ready** — available for questions in Chat &nbsp;·&nbsp; "
            "**Processing** — being read and indexed &nbsp;·&nbsp; "
            "**Error** — couldn't be processed (see the message shown at upload time)"
        )

        try:
            documents = api_client.list_documents(set_id=chosen_id)
        except Exception as exc:
            st.error(str(exc))
            documents = []

        if not documents:
            empty_state("📄", "No documents in this set yet", "Upload one above to get started.")
        else:
            for document in documents:
                name_col, format_col, status_col, action_col = st.columns([3, 1, 1.2, 1])
                name_col.write(f":material/description: {document.filename}")
                format_col.write(document.format)
                status_col.write(_STATUS_BADGE.get(document.status, document.status))
                if action_col.button(
                    "Remove", key=f"remove-{document.id}", use_container_width=True
                ):
                    try:
                        api_client.remove_document(document.id)
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
