import pytest

from backend.domain.models import DocumentFormat, IngestionStatus
from backend.services.document_set_service import (
    DocumentNotFoundError,
    DocumentSetService,
    DuplicateDocumentError,
    SetNotFoundError,
)
from storage.chroma_vector_store import ChromaVectorStore


@pytest.fixture
def service(tmp_path):
    return DocumentSetService(vector_store=ChromaVectorStore(persist_dir=tmp_path))


def test_create_and_list_sets(service):
    created = service.create_set("Contracts")

    assert created.name == "Contracts"
    assert service.list_sets() == [created]


def test_get_set_raises_for_unknown_id(service):
    with pytest.raises(SetNotFoundError):
        service.get_set("missing")


def test_register_document_raises_for_unknown_set(service):
    with pytest.raises(SetNotFoundError):
        service.register_document(
            set_id="missing", filename="a.txt", format=DocumentFormat.TEXT, content_hash="h1"
        )


def test_register_document_starts_as_processing(service):
    document_set = service.create_set("Contracts")

    document = service.register_document(
        set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT, content_hash="h1"
    )

    assert document.status == IngestionStatus.PROCESSING
    assert document.set_id == document_set.id


def test_register_document_raises_for_byte_identical_reupload(service):
    document_set = service.create_set("Contracts")
    service.register_document(
        set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT, content_hash="h1"
    )

    with pytest.raises(DuplicateDocumentError):
        service.register_document(
            set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT, content_hash="h1"
        )


def test_register_document_allows_same_filename_with_different_content(service):
    # register_document itself only blocks a byte-identical re-upload - the
    # replace-and-remove-old-vectors behavior for a genuinely changed file is
    # orchestrated by IngestionService (see test_ingestion_service.py), which
    # calls this once it knows the new content embedded successfully.
    document_set = service.create_set("Contracts")
    first = service.register_document(
        set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT, content_hash="h1"
    )

    second = service.register_document(
        set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT, content_hash="h2"
    )

    assert second.id != first.id
    assert second.content_hash == "h2"


def test_register_document_allows_same_filename_in_different_sets(service):
    set_a = service.create_set("A")
    set_b = service.create_set("B")
    service.register_document(
        set_id=set_a.id, filename="a.txt", format=DocumentFormat.TEXT, content_hash="h1"
    )

    document = service.register_document(
        set_id=set_b.id, filename="a.txt", format=DocumentFormat.TEXT, content_hash="h1"
    )

    assert document.set_id == set_b.id


def test_register_document_allows_reupload_after_removal(service):
    document_set = service.create_set("Contracts")
    first = service.register_document(
        set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT, content_hash="h1"
    )
    service.remove_document(first.id)

    document = service.register_document(
        set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT, content_hash="h1"
    )

    assert document.filename == "a.txt"


def test_find_document_by_filename(service):
    document_set = service.create_set("Contracts")
    document = service.register_document(
        set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT, content_hash="h1"
    )

    assert service.find_document_by_filename(document_set.id, "a.txt") == document
    assert service.find_document_by_filename(document_set.id, "missing.txt") is None


def test_mark_ready_and_mark_error_update_status(service):
    document_set = service.create_set("Contracts")
    document = service.register_document(
        set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT, content_hash="h1"
    )

    service.mark_ready(document.id)
    assert service.get_document(document.id).status == IngestionStatus.READY

    service.mark_error(document.id)
    assert service.get_document(document.id).status == IngestionStatus.ERROR


def test_mark_ready_raises_for_unknown_document(service):
    with pytest.raises(DocumentNotFoundError):
        service.mark_ready("missing")


def test_list_documents_scoped_by_set(service):
    set_a = service.create_set("A")
    set_b = service.create_set("B")
    doc_a = service.register_document(
        set_id=set_a.id, filename="a.txt", format=DocumentFormat.TEXT, content_hash="h1"
    )
    service.register_document(
        set_id=set_b.id, filename="b.txt", format=DocumentFormat.TEXT, content_hash="h1"
    )

    assert service.list_documents(set_id=set_a.id) == [doc_a]
    assert len(service.list_documents()) == 2


def _seed_vector(vector_store, document_id: str, set_id: str) -> None:
    vector_store.upsert(
        [
            {
                "id": f"chunk-{document_id}",
                "embedding": [1.0, 0.0],
                "text": "some chunk text",
                "metadata": {"document_id": document_id, "set_id": set_id},
            }
        ]
    )


def test_remove_document_deletes_from_vector_store_and_bookkeeping(service):
    vector_store = service._vector_store  # same store the fixture wired up
    document_set = service.create_set("A")
    document = service.register_document(
        set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT, content_hash="h1"
    )
    _seed_vector(vector_store, document.id, document_set.id)

    service.remove_document(document.id)

    with pytest.raises(DocumentNotFoundError):
        service.get_document(document.id)
    assert vector_store.query(embedding=[1.0, 0.0], top_k=5) == []


def test_delete_set_removes_set_its_documents_and_their_vectors(service):
    vector_store = service._vector_store
    document_set = service.create_set("A")
    document = service.register_document(
        set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT, content_hash="h1"
    )
    _seed_vector(vector_store, document.id, document_set.id)

    service.delete_set(document_set.id)

    assert service.list_sets() == []
    with pytest.raises(DocumentNotFoundError):
        service.get_document(document.id)
    assert vector_store.query(embedding=[1.0, 0.0], top_k=5) == []
