from __future__ import annotations

from typing import Any

COLLECTION_NAME = "chunks"
COLLECTION_METADATA = {"hnsw:space": "cosine"}


class ChromaCollectionOperations:
    """Shared upsert/query/delete logic against a Chroma collection.

    Both the embedded (`ChromaVectorStore`) and server-backed
    (`ChromaHttpVectorStore`) implementations only differ in how they obtain
    a `chromadb` client (`PersistentClient` vs `HttpClient`) - once
    `self._collection` is set, every VectorStore operation is identical.
    """

    _collection: Any

    def upsert(self, records: list[dict[str, Any]]) -> None:
        if not records:
            return
        self._collection.upsert(
            ids=[record["id"] for record in records],
            embeddings=[record["embedding"] for record in records],
            documents=[record["text"] for record in records],
            metadatas=[record["metadata"] for record in records],
        )

    def query(
        self,
        embedding: list[float],
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        kwargs: dict[str, Any] = {"query_embeddings": [embedding], "n_results": top_k}
        if where:
            kwargs["where"] = where
        result = self._collection.query(**kwargs)

        ids = result["ids"][0]
        documents = result["documents"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]
        return [
            {"id": id_, "text": text, "metadata": metadata, "distance": distance}
            for id_, text, metadata, distance in zip(ids, documents, metadatas, distances)
        ]

    def delete(self, document_id: str) -> None:
        self._collection.delete(where={"document_id": document_id})
