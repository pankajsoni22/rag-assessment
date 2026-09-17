from __future__ import annotations

from pathlib import Path

from backend.domain.models import Document, DocumentFormat
from backend.interfaces.vector_store import VectorStore
from backend.loaders.registry import DocumentLoaderRegistry
from backend.services.chunking_service import ChunkingService
from backend.services.document_set_service import DocumentSetService
from backend.services.embedding_service import EmbeddingService


class EmptyDocumentError(Exception):
    """Raised when a document produces no usable text/chunks (e.g. an empty file)."""


class IngestionService:
    """Orchestrates Loader -> Chunking -> Embedding -> VectorStore for one upload."""

    def __init__(
        self,
        loader_registry: DocumentLoaderRegistry,
        chunker: ChunkingService,
        embedder: EmbeddingService,
        vector_store: VectorStore,
        doc_set_service: DocumentSetService,
    ) -> None:
        self._loader_registry = loader_registry
        self._chunker = chunker
        self._embedder = embedder
        self._vector_store = vector_store
        self._doc_set_service = doc_set_service

    def ingest(self, file: Path, filename: str, format: DocumentFormat, set_id: str) -> Document:
        document = self._doc_set_service.register_document(
            set_id=set_id, filename=filename, format=format
        )
        try:
            loader = self._loader_registry.get_loader(format)
            text = loader.parse(file)
            chunks = self._chunker.chunk(text, document_id=document.id, set_id=set_id)
            if not chunks:
                raise EmptyDocumentError(f"'{filename}' has no readable text content.")
            vectors = self._embedder.embed(chunks)

            uploaded_at = document.uploaded_at.isoformat()
            records = [
                {
                    "id": chunk.id,
                    "embedding": vector,
                    "text": chunk.text,
                    "metadata": {
                        **chunk.metadata,
                        "filename": filename,
                        "format": format.value,
                        "uploaded_at": uploaded_at,
                    },
                }
                for chunk, vector in zip(chunks, vectors)
            ]
            self._vector_store.upsert(records)
        except Exception:
            self._doc_set_service.mark_error(document.id)
            raise

        self._doc_set_service.mark_ready(document.id)
        return self._doc_set_service.get_document(document.id)
