from __future__ import annotations

from pathlib import Path

import chromadb

from storage._chroma_collection import COLLECTION_METADATA, COLLECTION_NAME, ChromaCollectionOperations


class ChromaVectorStore(ChromaCollectionOperations):
    """Chroma-backed implementation of backend's VectorStore interface (structural, no import).

    Embedded mode: Chroma runs as a local file-based library inside this
    process, persisting to `persist_dir`. Used for local (non-Docker)
    development. See `ChromaHttpVectorStore` for the client-server mode used
    when Chroma runs as its own container.
    """

    def __init__(self, persist_dir: str | Path) -> None:
        client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata=COLLECTION_METADATA,
        )
