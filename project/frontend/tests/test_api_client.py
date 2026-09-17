import json
from datetime import datetime, timezone

import httpx
import pytest

from frontend.api_client import ApiClient
from frontend.models import CitationView


def _client_with_handler(handler) -> ApiClient:
    client = ApiClient(base_url="http://testserver")
    client._client = httpx.Client(
        base_url="http://testserver", transport=httpx.MockTransport(handler)
    )
    return client


def test_create_set_posts_and_parses_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/sets"
        assert json.loads(request.read()) == {"name": "Contracts"}
        return httpx.Response(
            201, json={"id": "s1", "name": "Contracts", "created_at": "2026-01-01T00:00:00+00:00"}
        )

    client = _client_with_handler(handler)

    result = client.create_set("Contracts")

    assert result.id == "s1"
    assert result.name == "Contracts"
    assert result.created_at == datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_list_sets_parses_list():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/sets"
        return httpx.Response(
            200, json=[{"id": "s1", "name": "A", "created_at": "2026-01-01T00:00:00+00:00"}]
        )

    client = _client_with_handler(handler)

    result = client.list_sets()

    assert [s.id for s in result] == ["s1"]


def test_delete_set_calls_delete():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/sets/s1"
        return httpx.Response(204)

    client = _client_with_handler(handler)

    client.delete_set("s1")


def test_list_documents_with_set_id_passes_query_param():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["set_id"] == "s1"
        return httpx.Response(200, json=[])

    client = _client_with_handler(handler)

    client.list_documents(set_id="s1")


def test_list_documents_without_set_id_omits_query_param():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "set_id" not in request.url.params
        return httpx.Response(200, json=[])

    client = _client_with_handler(handler)

    client.list_documents()


def test_upload_document_posts_multipart_and_parses_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/documents"
        assert request.url.params["set_id"] == "s1"
        return httpx.Response(
            201,
            json={
                "id": "d1",
                "set_id": "s1",
                "filename": "a.txt",
                "format": "text",
                "status": "ready",
                "uploaded_at": "2026-01-01T00:00:00+00:00",
            },
        )

    client = _client_with_handler(handler)

    result = client.upload_document("s1", "a.txt", b"hello")

    assert result.id == "d1"
    assert result.status == "ready"


def test_remove_document_calls_delete():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/documents/d1"
        return httpx.Response(204)

    client = _client_with_handler(handler)

    client.remove_document("d1")


def test_raises_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "not found"})

    client = _client_with_handler(handler)

    with pytest.raises(httpx.HTTPStatusError):
        client.delete_set("missing")


def test_ask_posts_question_and_parses_grounded_answer():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/query"
        assert json.loads(request.read()) == {
            "question": "What is X?",
            "set_id": "s1",
            "session_id": "sess-1",
        }
        return httpx.Response(
            200,
            json={
                "answer": "X is 42.",
                "citations": [{"document_id": "d1", "filename": "a.txt", "chunk_id": "c1"}],
                "grounded": True,
            },
        )

    client = _client_with_handler(handler)

    result = client.ask(question="What is X?", set_id="s1", session_id="sess-1")

    assert result.answer == "X is 42."
    assert result.grounded is True
    assert result.citations == [CitationView(document_id="d1", filename="a.txt", chunk_id="c1")]


def test_ask_parses_not_found_answer():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"answer": "Not found.", "citations": [], "grounded": False}
        )

    client = _client_with_handler(handler)

    result = client.ask(question="What is X?", set_id=None, session_id="sess-1")

    assert result.grounded is False
    assert result.citations == []
