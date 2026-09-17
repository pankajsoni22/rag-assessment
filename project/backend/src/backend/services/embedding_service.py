from __future__ import annotations

from typing import Protocol

from backend.domain.models import Chunk


class EmbeddingClient(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


class EmbeddingService:
    def __init__(self, client: EmbeddingClient) -> None:
        self._client = client

    def embed(self, chunks: list[Chunk]) -> list[list[float]]:
        if not chunks:
            return []
        return self._client.embed_texts([chunk.text for chunk in chunks])

    def embed_query(self, text: str) -> list[float]:
        [vector] = self._client.embed_texts([text])
        return vector
