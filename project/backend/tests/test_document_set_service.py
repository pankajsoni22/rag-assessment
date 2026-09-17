import pytest

from backend.domain.models import DocumentFormat, IngestionStatus
from backend.services.document_set_service import (
    DocumentNotFoundError,
    DocumentSetService,
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
        service.register_document(set_id="missing", filename="a.txt", format=DocumentFormat.TEXT)


def test_register_document_starts_as_processing(service):
    document_set = service.create_set("Contracts")

    document = service.register_document(
        set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT
    )

    assert document.status == IngestionStatus.PROCESSING
    assert document.set_id == document_set.id


def test_mark_ready_and_mark_error_update_status(service):
    document_set = service.create_set("Contracts")
    document = service.register_document(
        set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT
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
    doc_a = service.register_document(set_id=set_a.id, filename="a.txt", format=DocumentFormat.TEXT)
    service.register_document(set_id=set_b.id, filename="b.txt", format=DocumentFormat.TEXT)

    assert service.list_documents(set_id=set_a.id) == [doc_a]
    assert len(service.list_documents()) == 2


def test_remove_document_deletes_from_vector_store_and_bookkeeping(service):
    document_set = service.create_set("A")
    document = service.register_document(
        set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT
    )

    service.remove_document(document.id)

    with pytest.raises(DocumentNotFoundError):
        service.get_document(document.id)


def test_delete_set_removes_set_and_its_documents(service):
    document_set = service.create_set("A")
    document = service.register_document(
        set_id=document_set.id, filename="a.txt", format=DocumentFormat.TEXT
    )

    service.delete_set(document_set.id)

    assert service.list_sets() == []
    with pytest.raises(DocumentNotFoundError):
        service.get_document(document.id)
