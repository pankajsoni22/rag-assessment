from backend.domain.models import Chunk
from backend.services.embedding_service import EmbeddingService


class _FakeEmbeddingClient:
    def __init__(self):
        self.received_texts: list[str] | None = None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.received_texts = texts
        return [[float(len(text)), 0.0] for text in texts]


def _chunk(text: str, chunk_id: str = "c1") -> Chunk:
    return Chunk(id=chunk_id, document_id="d1", set_id="s1", text=text)


def test_embed_passes_chunk_texts_to_client_in_order():
    client = _FakeEmbeddingClient()
    service = EmbeddingService(client)

    service.embed([_chunk("alpha", "c1"), _chunk("beta-two", "c2")])

    assert client.received_texts == ["alpha", "beta-two"]


def test_embed_returns_vectors_from_client():
    client = _FakeEmbeddingClient()
    service = EmbeddingService(client)

    vectors = service.embed([_chunk("alpha")])

    assert vectors == [[5.0, 0.0]]


def test_embed_empty_chunk_list_returns_empty_without_calling_client():
    client = _FakeEmbeddingClient()
    service = EmbeddingService(client)

    vectors = service.embed([])

    assert vectors == []
    assert client.received_texts is None
