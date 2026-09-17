import io

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies import (
    get_document_set_service,
    get_ingestion_service,
    get_rag_orchestrator,
)
from backend.clients.errors import RateLimitedError
from backend.loaders.registry import default_registry
from backend.main import app
from backend.services.chunking_service import ChunkingService
from backend.services.conversation_service import ConversationService
from backend.services.document_set_service import DocumentSetService
from backend.services.embedding_service import EmbeddingService
from backend.services.generation_service import GenerationService
from backend.services.ingestion_service import IngestionService
from backend.services.rag_orchestrator import RAGOrchestrator
from backend.services.retrieval_service import RetrievalService
from storage.chroma_vector_store import ChromaVectorStore


class _FakeEmbeddingClient:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


class _FakeGenerationClient:
    def complete(self, messages: list[dict[str, str]]) -> str:
        return "Fake grounded answer."


class _RateLimitedGenerationClient:
    def complete(self, messages: list[dict[str, str]]) -> str:
        raise RateLimitedError("quota exceeded")


class _BrokenGenerationClient:
    def complete(self, messages: list[dict[str, str]]) -> str:
        raise RuntimeError("boom")


@pytest.fixture
def client(tmp_path):
    vector_store = ChromaVectorStore(persist_dir=tmp_path)
    doc_set_service = DocumentSetService(vector_store=vector_store)
    embedder = EmbeddingService(_FakeEmbeddingClient())
    ingestion_service = IngestionService(
        loader_registry=default_registry(),
        chunker=ChunkingService(),
        embedder=embedder,
        vector_store=vector_store,
        doc_set_service=doc_set_service,
    )
    orchestrator = RAGOrchestrator(
        conversation_service=ConversationService(),
        retrieval_service=RetrievalService(embedder=embedder, vector_store=vector_store),
        generation_service=GenerationService(_FakeGenerationClient()),
    )

    app.dependency_overrides[get_document_set_service] = lambda: doc_set_service
    app.dependency_overrides[get_ingestion_service] = lambda: ingestion_service
    app.dependency_overrides[get_rag_orchestrator] = lambda: orchestrator
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_ask_with_no_ingested_documents_returns_not_found(client):
    response = client.post(
        "/query", json={"question": "What is X?", "set_id": None, "session_id": "s1"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is False
    assert body["citations"] == []


def test_ask_with_ingested_document_returns_grounded_answer_with_citations(client):
    set_id = client.post("/sets", json={"name": "Notes"}).json()["id"]
    client.post(
        "/documents",
        params={"set_id": set_id},
        files={"file": ("note.txt", io.BytesIO(b"The answer is 42."), "text/plain")},
    )

    response = client.post(
        "/query", json={"question": "What is the answer?", "set_id": None, "session_id": "s1"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is True
    assert body["answer"] == "Fake grounded answer."
    assert len(body["citations"]) == 1
    assert body["citations"][0]["filename"] == "note.txt"


def test_ask_scoped_to_unknown_set_returns_404(client):
    response = client.post(
        "/query", json={"question": "What is X?", "set_id": "missing", "session_id": "s1"}
    )

    assert response.status_code == 404


def test_ask_scoped_to_known_set_succeeds(client):
    set_id = client.post("/sets", json={"name": "Notes"}).json()["id"]

    response = client.post(
        "/query", json={"question": "What is X?", "set_id": set_id, "session_id": "s1"}
    )

    assert response.status_code == 200


def _client_with_generation_client(generation_client, tmp_path) -> TestClient:
    vector_store = ChromaVectorStore(persist_dir=tmp_path)
    doc_set_service = DocumentSetService(vector_store=vector_store)
    embedder = EmbeddingService(_FakeEmbeddingClient())
    ingestion_service = IngestionService(
        loader_registry=default_registry(),
        chunker=ChunkingService(),
        embedder=embedder,
        vector_store=vector_store,
        doc_set_service=doc_set_service,
    )
    orchestrator = RAGOrchestrator(
        conversation_service=ConversationService(),
        retrieval_service=RetrievalService(embedder=embedder, vector_store=vector_store),
        generation_service=GenerationService(generation_client),
    )
    app.dependency_overrides[get_document_set_service] = lambda: doc_set_service
    app.dependency_overrides[get_ingestion_service] = lambda: ingestion_service
    app.dependency_overrides[get_rag_orchestrator] = lambda: orchestrator
    test_client = TestClient(app)
    # Ingest a document so retrieval returns non-empty chunks, forcing
    # GenerationService to actually call the (broken) client rather than
    # taking the no-chunks "not found" shortcut.
    set_id = test_client.post("/sets", json={"name": "Notes"}).json()["id"]
    test_client.post(
        "/documents",
        params={"set_id": set_id},
        files={"file": ("note.txt", io.BytesIO(b"The answer is 42."), "text/plain")},
    )
    return test_client


def test_ask_returns_429_when_generation_is_rate_limited(tmp_path):
    try:
        test_client = _client_with_generation_client(_RateLimitedGenerationClient(), tmp_path)

        response = test_client.post(
            "/query", json={"question": "What is the answer?", "set_id": None, "session_id": "s1"}
        )

        assert response.status_code == 429
        assert "rate-limited" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_ask_returns_500_with_generic_detail_on_unexpected_failure(tmp_path):
    try:
        test_client = _client_with_generation_client(_BrokenGenerationClient(), tmp_path)

        response = test_client.post(
            "/query", json={"question": "What is the answer?", "set_id": None, "session_id": "s1"}
        )

        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "boom" not in detail
        assert "RuntimeError" not in detail
    finally:
        app.dependency_overrides.clear()
