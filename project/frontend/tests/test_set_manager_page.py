from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from frontend.models import DocumentSetView, DocumentView

_PAGE = str(
    Path(__file__).resolve().parents[1] / "src" / "frontend" / "pages" / "set_manager.py"
)


class _FakeApiClient:
    def __init__(self, sets=None, documents=None):
        self.sets = sets or []
        self.documents = documents or []
        self.created_set_names: list[str] = []
        self.deleted_set_ids: list[str] = []
        self.uploaded: list[tuple[str, str, bytes]] = []
        self.removed_document_ids: list[str] = []

    def list_sets(self):
        return self.sets

    def create_set(self, name):
        self.created_set_names.append(name)
        return DocumentSetView(id="new-id", name=name, created_at=datetime.now(timezone.utc))

    def delete_set(self, set_id):
        self.deleted_set_ids.append(set_id)

    def list_documents(self, set_id=None):
        return self.documents

    def upload_document(self, set_id, filename, content):
        self.uploaded.append((set_id, filename, content))
        return DocumentView(
            id="new-doc",
            set_id=set_id,
            filename=filename,
            format="text",
            status="ready",
            uploaded_at=datetime.now(timezone.utc),
        )

    def remove_document(self, document_id):
        self.removed_document_ids.append(document_id)


def _run_with_client(fake_client) -> AppTest:
    with patch("frontend.api_client.get_api_client", return_value=fake_client):
        at = AppTest.from_file(_PAGE)
        at.run()
    return at


def test_no_sets_shows_empty_state():
    at = _run_with_client(_FakeApiClient(sets=[]))

    assert not at.exception
    assert any("No sets yet" in m.value for m in at.markdown)


def test_existing_set_is_selectable_and_shows_documents():
    document_set = DocumentSetView(id="s1", name="Contracts", created_at=datetime.now(timezone.utc))
    document = DocumentView(
        id="d1",
        set_id="s1",
        filename="policy.txt",
        format="text",
        status="ready",
        uploaded_at=datetime.now(timezone.utc),
    )
    at = _run_with_client(_FakeApiClient(sets=[document_set], documents=[document]))

    assert not at.exception
    assert at.selectbox[0].options == ["Contracts"]
    markdown_text = " ".join(m.value for m in at.markdown)
    assert "policy.txt" in markdown_text or any("policy.txt" in w.value for w in at.text)


def test_create_set_form_calls_api_client():
    fake_client = _FakeApiClient(sets=[])
    with patch("frontend.api_client.get_api_client", return_value=fake_client):
        at = AppTest.from_file(_PAGE)
        at.run()
        at.text_input[0].set_value("New Set").run()
        submit_button = next(b for b in at.button if b.label == "Create set")
        submit_button.click().run()

    assert fake_client.created_set_names == ["New Set"]


def test_delete_set_requires_confirmation():
    document_set = DocumentSetView(id="s1", name="Contracts", created_at=datetime.now(timezone.utc))
    fake_client = _FakeApiClient(sets=[document_set], documents=[])
    with patch("frontend.api_client.get_api_client", return_value=fake_client):
        at = AppTest.from_file(_PAGE)
        at.run()
        delete_button = next(b for b in at.button if b.label == "Delete this set")
        delete_button.click().run()

    assert fake_client.deleted_set_ids == []  # not deleted until confirmed
    assert any(w for w in at.warning)


def test_upload_document_calls_api_client():
    document_set = DocumentSetView(id="s1", name="Contracts", created_at=datetime.now(timezone.utc))
    fake_client = _FakeApiClient(sets=[document_set], documents=[])
    with patch("frontend.api_client.get_api_client", return_value=fake_client):
        at = AppTest.from_file(_PAGE)
        at.run()
        at.file_uploader[0].set_value(("note.txt", b"hello world", "text/plain")).run()
        upload_button = next(b for b in at.button if b.label == "Upload")
        upload_button.click().run()

    assert fake_client.uploaded == [("s1", "note.txt", b"hello world")]


def test_upload_multiple_documents_in_one_click():
    document_set = DocumentSetView(id="s1", name="Contracts", created_at=datetime.now(timezone.utc))
    fake_client = _FakeApiClient(sets=[document_set], documents=[])
    with patch("frontend.api_client.get_api_client", return_value=fake_client):
        at = AppTest.from_file(_PAGE)
        at.run()
        at.file_uploader[0].set_value(
            [
                ("a.txt", b"hello", "text/plain"),
                ("b.txt", b"world", "text/plain"),
            ]
        ).run()
        upload_button = next(b for b in at.button if b.label == "Upload")
        upload_button.click().run()

    assert fake_client.uploaded == [
        ("s1", "a.txt", b"hello"),
        ("s1", "b.txt", b"world"),
    ]


def test_upload_multiple_documents_reports_partial_failure():
    document_set = DocumentSetView(id="s1", name="Contracts", created_at=datetime.now(timezone.utc))
    fake_client = _FakeApiClient(sets=[document_set], documents=[])

    def upload_document(set_id, filename, content):
        if filename == "bad.txt":
            raise Exception("Could not process 'bad.txt'.")
        fake_client.uploaded.append((set_id, filename, content))

    fake_client.upload_document = upload_document

    with patch("frontend.api_client.get_api_client", return_value=fake_client):
        at = AppTest.from_file(_PAGE)
        at.run()
        at.file_uploader[0].set_value(
            [
                ("good.txt", b"hello", "text/plain"),
                ("bad.txt", b"world", "text/plain"),
            ]
        ).run()
        upload_button = next(b for b in at.button if b.label == "Upload")
        upload_button.click().run()

    # The good file still uploads even though the bad one fails - one bad
    # file in a batch doesn't block the rest.
    assert fake_client.uploaded == [("s1", "good.txt", b"hello")]


def test_remove_document_calls_api_client():
    document_set = DocumentSetView(id="s1", name="Contracts", created_at=datetime.now(timezone.utc))
    document = DocumentView(
        id="d1",
        set_id="s1",
        filename="policy.txt",
        format="text",
        status="ready",
        uploaded_at=datetime.now(timezone.utc),
    )
    fake_client = _FakeApiClient(sets=[document_set], documents=[document])
    with patch("frontend.api_client.get_api_client", return_value=fake_client):
        at = AppTest.from_file(_PAGE)
        at.run()
        remove_button = next(b for b in at.button if b.label == "Remove")
        remove_button.click().run()

    assert fake_client.removed_document_ids == ["d1"]
