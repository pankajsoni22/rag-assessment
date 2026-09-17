from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from frontend.models import AnswerView, CitationView, DocumentSetView

_PAGE = str(Path(__file__).resolve().parents[1] / "src" / "frontend" / "pages" / "chat.py")


class _FakeApiClient:
    def __init__(self, sets=None, answer: AnswerView | None = None):
        self.sets = sets or []
        self.answer = answer or AnswerView(answer="42", citations=[], grounded=True)
        self.received_ask_args: tuple | None = None

    def list_sets(self):
        return self.sets

    def ask(self, question, set_id, session_id):
        self.received_ask_args = (question, set_id, session_id)
        return self.answer


def _run_with_client(fake_client) -> AppTest:
    with patch("frontend.api_client.get_api_client", return_value=fake_client):
        at = AppTest.from_file(_PAGE)
        at.run()
    return at


def test_default_scope_is_search_everything():
    document_set = DocumentSetView(id="s1", name="Contracts", created_at=datetime.now(timezone.utc))
    at = _run_with_client(_FakeApiClient(sets=[document_set]))

    assert not at.exception
    assert at.selectbox[0].value is None


def test_submitting_question_renders_user_and_assistant_messages():
    fake_client = _FakeApiClient(answer=AnswerView(answer="X is 42.", citations=[], grounded=True))
    with patch("frontend.api_client.get_api_client", return_value=fake_client):
        at = AppTest.from_file(_PAGE)
        at.run()
        at.chat_input[0].set_value("What is X?").run()

    assert not at.exception
    assert fake_client.received_ask_args == ("What is X?", None, at.session_state["session_id"])
    chat_texts = [m.value for block in at.chat_message for m in block.markdown]
    assert "What is X?" in chat_texts
    assert "X is 42." in chat_texts


def test_not_found_answer_renders_distinct_info_state():
    fake_client = _FakeApiClient(
        answer=AnswerView(answer="Not found.", citations=[], grounded=False)
    )
    with patch("frontend.api_client.get_api_client", return_value=fake_client):
        at = AppTest.from_file(_PAGE)
        at.run()
        at.chat_input[0].set_value("What is X?").run()

    assert not at.exception
    assert any("Not found in the documents" in info.value for info in at.info)


def test_citations_render_as_caption():
    citation = CitationView(document_id="d1", filename="policy.txt", chunk_id="c1")
    fake_client = _FakeApiClient(
        answer=AnswerView(answer="X is 42.", citations=[citation], grounded=True)
    )
    with patch("frontend.api_client.get_api_client", return_value=fake_client):
        at = AppTest.from_file(_PAGE)
        at.run()
        at.chat_input[0].set_value("What is X?").run()

    assert not at.exception
    assert any("policy.txt" in c.value for c in at.caption)


def test_chat_scope_selector_is_independent_of_set_manager_selection():
    document_set = DocumentSetView(id="s1", name="Contracts", created_at=datetime.now(timezone.utc))
    fake_client = _FakeApiClient(sets=[document_set])
    with patch("frontend.api_client.get_api_client", return_value=fake_client):
        at = AppTest.from_file(_PAGE)
        at.session_state["selected_set_id"] = "s1"  # set on the (unrelated) Set Manager page
        at.run()

    assert not at.exception
    assert at.session_state.get("chat_set_id") is None
    assert at.selectbox[0].value is None
