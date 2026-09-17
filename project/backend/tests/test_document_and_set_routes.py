import io

import pytest
from fastapi.testclient import TestClient

from backend.api.dependencies import get_document_set_service, get_ingestion_service
from backend.clients.errors import RateLimitedError
from backend.loaders.registry import default_registry
from backend.main import app
from backend.services.chunking_service import ChunkingService
from backend.services.document_set_service import DocumentSetService
from backend.services.embedding_service import EmbeddingService
from backend.services.ingestion_service import IngestionService
from storage.chroma_vector_store import ChromaVectorStore


class _FakeEmbeddingClient:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[float(i), 0.0] for i, _ in enumerate(texts)]


class _RateLimitedEmbeddingClient:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise RateLimitedError("quota exceeded")


@pytest.fixture
def client(tmp_path):
    vector_store = ChromaVectorStore(persist_dir=tmp_path)
    doc_set_service = DocumentSetService(vector_store=vector_store)
    ingestion_service = IngestionService(
        loader_registry=default_registry(),
        chunker=ChunkingService(),
        embedder=EmbeddingService(_FakeEmbeddingClient()),
        vector_store=vector_store,
        doc_set_service=doc_set_service,
    )

    app.dependency_overrides[get_document_set_service] = lambda: doc_set_service
    app.dependency_overrides[get_ingestion_service] = lambda: ingestion_service
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_create_and_list_sets(client):
    response = client.post("/sets", json={"name": "Contracts"})
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Contracts"

    response = client.get("/sets")
    assert response.status_code == 200
    assert [s["id"] for s in response.json()] == [created["id"]]


def test_delete_set(client):
    set_id = client.post("/sets", json={"name": "Temp"}).json()["id"]

    response = client.delete(f"/sets/{set_id}")

    assert response.status_code == 204
    assert client.get("/sets").json() == []


def test_upload_document_and_list(client):
    set_id = client.post("/sets", json={"name": "Notes"}).json()["id"]

    response = client.post(
        "/documents",
        params={"set_id": set_id},
        files={"file": ("note.txt", io.BytesIO(b"hello world"), "text/plain")},
    )

    assert response.status_code == 201
    document = response.json()
    assert document["status"] == "ready"
    assert document["filename"] == "note.txt"

    response = client.get("/documents", params={"set_id": set_id})
    assert [d["id"] for d in response.json()] == [document["id"]]


def test_upload_document_unsupported_extension_returns_400(client):
    set_id = client.post("/sets", json={"name": "Notes"}).json()["id"]

    response = client.post(
        "/documents",
        params={"set_id": set_id},
        files={"file": ("note.exe", io.BytesIO(b"binary"), "application/octet-stream")},
    )

    assert response.status_code == 400


def test_upload_document_unknown_set_returns_404(client):
    response = client.post(
        "/documents",
        params={"set_id": "missing"},
        files={"file": ("note.txt", io.BytesIO(b"hello"), "text/plain")},
    )

    assert response.status_code == 404


def test_upload_empty_document_returns_422_with_plain_language_detail(client):
    set_id = client.post("/sets", json={"name": "Notes"}).json()["id"]

    response = client.post(
        "/documents",
        params={"set_id": set_id},
        files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
    )

    assert response.status_code == 422
    assert "empty.txt" in response.json()["detail"]

    # The document is still visible, marked as an error, not silently dropped.
    [document] = client.get("/documents", params={"set_id": set_id}).json()
    assert document["status"] == "error"


def test_upload_corrupt_pdf_returns_422_without_leaking_internals(client):
    set_id = client.post("/sets", json={"name": "Notes"}).json()["id"]

    response = client.post(
        "/documents",
        params={"set_id": set_id},
        files={"file": ("bad.pdf", io.BytesIO(b"not a real pdf"), "application/pdf")},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "bad.pdf" in detail
    # Plain-language message only — no raw exception class names or stack details.
    assert "PdfStreamError" not in detail
    assert "Traceback" not in detail


def test_upload_document_returns_429_when_embedding_is_rate_limited(tmp_path):
    vector_store = ChromaVectorStore(persist_dir=tmp_path)
    doc_set_service = DocumentSetService(vector_store=vector_store)
    ingestion_service = IngestionService(
        loader_registry=default_registry(),
        chunker=ChunkingService(),
        embedder=EmbeddingService(_RateLimitedEmbeddingClient()),
        vector_store=vector_store,
        doc_set_service=doc_set_service,
    )
    app.dependency_overrides[get_document_set_service] = lambda: doc_set_service
    app.dependency_overrides[get_ingestion_service] = lambda: ingestion_service
    try:
        test_client = TestClient(app)
        set_id = test_client.post("/sets", json={"name": "Notes"}).json()["id"]

        response = test_client.post(
            "/documents",
            params={"set_id": set_id},
            files={"file": ("note.txt", io.BytesIO(b"hello world"), "text/plain")},
        )

        assert response.status_code == 429
        assert "rate-limited" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_get_document_unknown_id_returns_404(client):
    response = client.get("/documents/missing")

    assert response.status_code == 404


def test_remove_document(client):
    set_id = client.post("/sets", json={"name": "Notes"}).json()["id"]
    document = client.post(
        "/documents",
        params={"set_id": set_id},
        files={"file": ("note.txt", io.BytesIO(b"hello world"), "text/plain")},
    ).json()

    response = client.delete(f"/documents/{document['id']}")

    assert response.status_code == 204
    assert client.get("/documents").json() == []
