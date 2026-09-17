from __future__ import annotations

from functools import lru_cache

from backend.clients.gemini_client import GeminiEmbeddingClient
from backend.config import Settings
from backend.interfaces.vector_store import VectorStore
from backend.loaders.registry import default_registry
from backend.services.chunking_service import ChunkingService
from backend.services.document_set_service import DocumentSetService
from backend.services.embedding_service import EmbeddingService
from backend.services.ingestion_service import IngestionService
from storage.chroma_vector_store import ChromaVectorStore

# Every provider below is lazy (only runs when a request actually depends on
# it, via FastAPI's Depends) and cached as a singleton. Nothing here runs at
# module import time, so importing `backend.main` never requires a real .env —
# tests override these providers via app.dependency_overrides instead.


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_vector_store() -> VectorStore:
    return ChromaVectorStore(persist_dir=get_settings().chroma_persist_dir)


@lru_cache
def get_document_set_service() -> DocumentSetService:
    return DocumentSetService(vector_store=get_vector_store())


@lru_cache
def get_ingestion_service() -> IngestionService:
    settings = get_settings()
    embedder = EmbeddingService(GeminiEmbeddingClient(api_key=settings.google_api_key))
    return IngestionService(
        loader_registry=default_registry(),
        chunker=ChunkingService(),
        embedder=embedder,
        vector_store=get_vector_store(),
        doc_set_service=get_document_set_service(),
    )
