from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timezone

from backend.domain.models import Document, DocumentFormat, DocumentSet, IngestionStatus
from backend.interfaces.vector_store import VectorStore


class SetNotFoundError(Exception):
    pass


class DocumentNotFoundError(Exception):
    pass


class DocumentSetService:
    """Owns all set/document bookkeeping in backend memory (id, name, status, etc.).

    Deliberately not derived from Chroma metadata, even though architecture.md
    originally sketched it that way: an empty, just-created set has no chunks to
    derive from, and in-flight ingestion status already had to live in memory
    regardless (per architecture.md), so a second, partial derivation path
    would just be extra complexity for no consistency benefit. Chroma remains
    the source of truth for chunks/vectors only.
    """

    def __init__(self, vector_store: VectorStore) -> None:
        self._vector_store = vector_store
        self._sets: dict[str, DocumentSet] = {}
        self._documents: dict[str, Document] = {}

    def create_set(self, name: str) -> DocumentSet:
        document_set = DocumentSet(
            id=str(uuid.uuid4()), name=name, created_at=datetime.now(timezone.utc)
        )
        self._sets[document_set.id] = document_set
        return document_set

    def list_sets(self) -> list[DocumentSet]:
        return list(self._sets.values())

    def get_set(self, set_id: str) -> DocumentSet:
        try:
            return self._sets[set_id]
        except KeyError:
            raise SetNotFoundError(set_id) from None

    def delete_set(self, set_id: str) -> None:
        self._sets.pop(set_id, None)
        document_ids = [d.id for d in self._documents.values() if d.set_id == set_id]
        for document_id in document_ids:
            self.remove_document(document_id)

    def register_document(self, set_id: str, filename: str, format: DocumentFormat) -> Document:
        if set_id not in self._sets:
            raise SetNotFoundError(set_id)
        document = Document(
            id=str(uuid.uuid4()),
            set_id=set_id,
            filename=filename,
            format=format,
            status=IngestionStatus.PROCESSING,
            uploaded_at=datetime.now(timezone.utc),
        )
        self._documents[document.id] = document
        return document

    def mark_ready(self, document_id: str) -> None:
        self._set_status(document_id, IngestionStatus.READY)

    def mark_error(self, document_id: str) -> None:
        self._set_status(document_id, IngestionStatus.ERROR)

    def _set_status(self, document_id: str, status: IngestionStatus) -> None:
        document = self._documents.get(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)
        self._documents[document_id] = replace(document, status=status)

    def get_document(self, document_id: str) -> Document:
        try:
            return self._documents[document_id]
        except KeyError:
            raise DocumentNotFoundError(document_id) from None

    def list_documents(self, set_id: str | None = None) -> list[Document]:
        documents = list(self._documents.values())
        if set_id is not None:
            documents = [d for d in documents if d.set_id == set_id]
        return documents

    def remove_document(self, document_id: str) -> None:
        self._vector_store.delete(document_id)
        self._documents.pop(document_id, None)
