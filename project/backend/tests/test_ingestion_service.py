import pytest

from backend.domain.models import DocumentFormat, IngestionStatus
from backend.loaders.registry import default_registry
from backend.services.chunking_service import ChunkingService
from backend.services.document_set_service import DocumentSetService, SetNotFoundError
from backend.services.embedding_service import EmbeddingService
from backend.services.ingestion_service import EmptyDocumentError, IngestionService
from storage.chroma_vector_store import ChromaVectorStore


class _FakeEmbeddingClient:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[float(i), 0.0] for i, _ in enumerate(texts)]


@pytest.fixture
def wiring(tmp_path):
    vector_store = ChromaVectorStore(persist_dir=tmp_path)
    doc_set_service = DocumentSetService(vector_store=vector_store)
    ingestion_service = IngestionService(
        loader_registry=default_registry(),
        chunker=ChunkingService(),
        embedder=EmbeddingService(_FakeEmbeddingClient()),
        vector_store=vector_store,
        doc_set_service=doc_set_service,
    )
    return ingestion_service, doc_set_service, vector_store


def test_ingest_marks_document_ready_and_writes_chunks(wiring, tmp_path):
    ingestion_service, doc_set_service, vector_store = wiring
    document_set = doc_set_service.create_set("Notes")
    file = tmp_path / "note.txt"
    file.write_text("Hello ingestion pipeline.", encoding="utf-8")

    document = ingestion_service.ingest(
        file=file, filename="note.txt", format=DocumentFormat.TEXT, set_id=document_set.id
    )

    assert document.status == IngestionStatus.READY
    results = vector_store.query(embedding=[0.0, 0.0], top_k=5, where={"document_id": document.id})
    assert len(results) == 1
    assert results[0]["text"] == "Hello ingestion pipeline."
    assert results[0]["metadata"]["filename"] == "note.txt"
    assert results[0]["metadata"]["format"] == "text"
    assert "uploaded_at" in results[0]["metadata"]


def test_ingest_raises_for_unknown_set(wiring, tmp_path):
    ingestion_service, _doc_set_service, _vector_store = wiring
    file = tmp_path / "note.txt"
    file.write_text("hello", encoding="utf-8")

    with pytest.raises(SetNotFoundError):
        ingestion_service.ingest(
            file=file, filename="note.txt", format=DocumentFormat.TEXT, set_id="missing"
        )


def test_ingest_marks_document_error_on_loader_failure(wiring, tmp_path):
    ingestion_service, doc_set_service, _vector_store = wiring
    document_set = doc_set_service.create_set("Notes")
    missing_file = tmp_path / "does-not-exist.txt"

    with pytest.raises(FileNotFoundError):
        ingestion_service.ingest(
            file=missing_file,
            filename="does-not-exist.txt",
            format=DocumentFormat.TEXT,
            set_id=document_set.id,
        )

    [document] = doc_set_service.list_documents(set_id=document_set.id)
    assert document.status == IngestionStatus.ERROR


def test_ingest_empty_file_raises_and_marks_error(wiring, tmp_path):
    ingestion_service, doc_set_service, vector_store = wiring
    document_set = doc_set_service.create_set("Notes")
    file = tmp_path / "empty.txt"
    file.write_text("", encoding="utf-8")

    with pytest.raises(EmptyDocumentError):
        ingestion_service.ingest(
            file=file, filename="empty.txt", format=DocumentFormat.TEXT, set_id=document_set.id
        )

    [document] = doc_set_service.list_documents(set_id=document_set.id)
    assert document.status == IngestionStatus.ERROR
    assert vector_store.query(embedding=[0.0, 0.0], top_k=5) == []
