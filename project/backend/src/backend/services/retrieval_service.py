from __future__ import annotations

from typing import Any

from backend.domain.models import RetrievedChunk
from backend.interfaces.vector_store import VectorStore
from backend.services.embedding_service import EmbeddingService


class RetrievalService:
    def __init__(self, embedder: EmbeddingService, vector_store: VectorStore) -> None:
        self._embedder = embedder
        self._vector_store = vector_store

    def retrieve(self, query: str, set_id: str | None, top_k: int) -> list[RetrievedChunk]:
        embedding = self._embedder.embed_query(query)
        where: dict[str, Any] | None = {"set_id": set_id} if set_id else None
        results = self._vector_store.query(embedding, top_k, where=where)
        return [
            RetrievedChunk(
                chunk_id=result["id"],
                document_id=result["metadata"]["document_id"],
                text=result["text"],
                metadata=result["metadata"],
                distance=result["distance"],
            )
            for result in results
        ]
