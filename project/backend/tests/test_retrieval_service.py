import pytest

from backend.services.embedding_service import EmbeddingService
from backend.services.retrieval_service import RetrievalService
from storage.chroma_vector_store import ChromaVectorStore


class _FakeEmbeddingClient:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


@pytest.fixture
def retrieval_service(tmp_path):
    vector_store = ChromaVectorStore(persist_dir=tmp_path)
    embedder = EmbeddingService(_FakeEmbeddingClient())
    return RetrievalService(embedder=embedder, vector_store=vector_store), vector_store


def test_retrieve_returns_matching_chunks(retrieval_service):
    service, vector_store = retrieval_service
    vector_store.upsert(
        [
            {
                "id": "c1",
                "embedding": [1.0, 0.0],
                "text": "alpha",
                "metadata": {"document_id": "d1", "set_id": "s1", "filename": "a.txt"},
            }
        ]
    )

    results = service.retrieve(query="anything", set_id=None, top_k=5)

    assert len(results) == 1
    assert results[0].chunk_id == "c1"
    assert results[0].document_id == "d1"
    assert results[0].text == "alpha"
    assert results[0].metadata["filename"] == "a.txt"
    assert isinstance(results[0].distance, float)


def test_retrieve_scoped_by_set_id(retrieval_service):
    service, vector_store = retrieval_service
    vector_store.upsert(
        [
            {
                "id": "c1",
                "embedding": [1.0, 0.0],
                "text": "alpha",
                "metadata": {"document_id": "d1", "set_id": "s1"},
            },
            {
                "id": "c2",
                "embedding": [1.0, 0.0],
                "text": "beta",
                "metadata": {"document_id": "d2", "set_id": "s2"},
            },
        ]
    )

    results = service.retrieve(query="anything", set_id="s1", top_k=5)

    assert [r.chunk_id for r in results] == ["c1"]


def test_retrieve_respects_top_k(retrieval_service):
    service, vector_store = retrieval_service
    vector_store.upsert(
        [
            {"id": f"c{i}", "embedding": [1.0, 0.0], "text": f"t{i}", "metadata": {"document_id": "d1"}}
            for i in range(5)
        ]
    )

    results = service.retrieve(query="anything", set_id=None, top_k=2)

    assert len(results) == 2


def test_retrieve_on_empty_store_returns_empty_list(retrieval_service):
    service, _vector_store = retrieval_service

    assert service.retrieve(query="anything", set_id=None, top_k=5) == []
