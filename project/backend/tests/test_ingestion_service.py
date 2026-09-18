import pytest

from backend.domain.models import DocumentFormat, IngestionStatus
from backend.loaders.registry import default_registry
from backend.services.chunking_service import ChunkingService
from backend.services.document_set_service import (
    DocumentSetService,
    DuplicateDocumentError,
    SetNotFoundError,
)
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


def test_ingest_rejects_byte_identical_reupload(wiring, tmp_path):
    ingestion_service, doc_set_service, _vector_store = wiring
    document_set = doc_set_service.create_set("Notes")
    file = tmp_path / "note.txt"
    file.write_text("Hello ingestion pipeline.", encoding="utf-8")
    ingestion_service.ingest(
        file=file, filename="note.txt", format=DocumentFormat.TEXT, set_id=document_set.id
    )

    with pytest.raises(DuplicateDocumentError):
        ingestion_service.ingest(
            file=file, filename="note.txt", format=DocumentFormat.TEXT, set_id=document_set.id
        )

    assert len(doc_set_service.list_documents(set_id=document_set.id)) == 1


def test_ingest_replaces_old_document_when_same_filename_different_content(wiring, tmp_path):
    ingestion_service, doc_set_service, vector_store = wiring
    document_set = doc_set_service.create_set("Notes")
    file = tmp_path / "note.txt"
    file.write_text("Original content.", encoding="utf-8")
    original = ingestion_service.ingest(
        file=file, filename="note.txt", format=DocumentFormat.TEXT, set_id=document_set.id
    )

    file.write_text("Completely different content.", encoding="utf-8")
    updated = ingestion_service.ingest(
        file=file, filename="note.txt", format=DocumentFormat.TEXT, set_id=document_set.id
    )

    documents = doc_set_service.list_documents(set_id=document_set.id)
    assert [d.id for d in documents] == [updated.id]
    assert updated.status == IngestionStatus.READY

    # Old vectors are gone, only the new content's chunks remain.
    old_results = vector_store.query(
        embedding=[0.0, 0.0], top_k=5, where={"document_id": original.id}
    )
    assert old_results == []
    new_results = vector_store.query(
        embedding=[0.0, 0.0], top_k=5, where={"document_id": updated.id}
    )
    assert len(new_results) == 1
    assert new_results[0]["text"] == "Completely different content."


def test_ingest_keeps_old_document_if_replacement_upload_fails(wiring, tmp_path):
    ingestion_service, doc_set_service, vector_store = wiring
    document_set = doc_set_service.create_set("Notes")
    file = tmp_path / "note.txt"
    file.write_text("Original content.", encoding="utf-8")
    original = ingestion_service.ingest(
        file=file, filename="note.txt", format=DocumentFormat.TEXT, set_id=document_set.id
    )

    file.write_text("", encoding="utf-8")
    with pytest.raises(EmptyDocumentError):
        ingestion_service.ingest(
            file=file, filename="note.txt", format=DocumentFormat.TEXT, set_id=document_set.id
        )

    # Original document and its vectors are untouched by the failed replace.
    assert doc_set_service.get_document(original.id).status == IngestionStatus.READY
    original_results = vector_store.query(
        embedding=[0.0, 0.0], top_k=5, where={"document_id": original.id}
    )
    assert len(original_results) == 1


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
