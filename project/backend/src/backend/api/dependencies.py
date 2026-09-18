from __future__ import annotations

from functools import lru_cache

from backend.clients.gemini_client import GeminiEmbeddingClient
from backend.clients.groq_client import GroqClient
from backend.config import Settings
from backend.interfaces.vector_store import VectorStore
from backend.loaders.registry import default_registry
from backend.services.chunking_service import ChunkingService
from backend.services.conversation_service import ConversationService
from backend.services.document_set_service import DocumentSetService
from backend.services.embedding_service import EmbeddingService
from backend.services.generation_service import GenerationService
from backend.services.ingestion_service import IngestionService
from backend.services.rag_orchestrator import RAGOrchestrator
from backend.services.retrieval_service import RetrievalService
from storage.chroma_http_vector_store import ChromaHttpVectorStore
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
    settings = get_settings()
    if settings.chroma_host:
        return ChromaHttpVectorStore(host=settings.chroma_host, port=settings.chroma_port)
    return ChromaVectorStore(persist_dir=settings.chroma_persist_dir)


@lru_cache
def get_document_set_service() -> DocumentSetService:
    return DocumentSetService(vector_store=get_vector_store())


@lru_cache
def get_embedding_service() -> EmbeddingService:
    settings = get_settings()
    return EmbeddingService(GeminiEmbeddingClient(api_key=settings.google_api_key))


@lru_cache
def get_ingestion_service() -> IngestionService:
    return IngestionService(
        loader_registry=default_registry(),
        chunker=ChunkingService(),
        embedder=get_embedding_service(),
        vector_store=get_vector_store(),
        doc_set_service=get_document_set_service(),
    )


@lru_cache
def get_retrieval_service() -> RetrievalService:
    return RetrievalService(embedder=get_embedding_service(), vector_store=get_vector_store())


@lru_cache
def get_generation_service() -> GenerationService:
    settings = get_settings()
    return GenerationService(GroqClient(api_key=settings.groq_api_key))


@lru_cache
def get_conversation_service() -> ConversationService:
    return ConversationService()


@lru_cache
def get_rag_orchestrator() -> RAGOrchestrator:
    return RAGOrchestrator(
        conversation_service=get_conversation_service(),
        retrieval_service=get_retrieval_service(),
        generation_service=get_generation_service(),
    )
