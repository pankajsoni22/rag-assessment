from __future__ import annotations

import chromadb

from storage._chroma_collection import COLLECTION_METADATA, COLLECTION_NAME, ChromaCollectionOperations


class ChromaHttpVectorStore(ChromaCollectionOperations):
    """Chroma-backed implementation of backend's VectorStore interface (structural, no import).

    Client-server mode: connects to a Chroma server running as its own
    process/container over HTTP, instead of embedding Chroma in this
    process. Used when running via Docker Compose (see `docker/`), where
    Chroma is a separate service. See `ChromaVectorStore` for the embedded,
    local-development mode.
    """

    def __init__(self, host: str, port: int) -> None:
        client = chromadb.HttpClient(host=host, port=port)
        self._collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata=COLLECTION_METADATA,
        )
