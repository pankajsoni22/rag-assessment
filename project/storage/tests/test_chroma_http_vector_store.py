from unittest.mock import MagicMock, patch

from storage.chroma_http_vector_store import ChromaHttpVectorStore


def _fake_client_and_collection():
    collection = MagicMock()
    client = MagicMock()
    client.get_or_create_collection.return_value = collection
    return client, collection


def test_connects_to_given_host_and_port():
    client, _collection = _fake_client_and_collection()
    with patch("storage.chroma_http_vector_store.chromadb.HttpClient", return_value=client) as http_client:
        ChromaHttpVectorStore(host="chroma", port=8000)

    http_client.assert_called_once_with(host="chroma", port=8000)


def test_upsert_delegates_to_collection():
    client, collection = _fake_client_and_collection()
    with patch("storage.chroma_http_vector_store.chromadb.HttpClient", return_value=client):
        store = ChromaHttpVectorStore(host="chroma", port=8000)

    store.upsert(
        [{"id": "c1", "embedding": [1.0, 0.0], "text": "alpha", "metadata": {"document_id": "d1"}}]
    )

    collection.upsert.assert_called_once_with(
        ids=["c1"], embeddings=[[1.0, 0.0]], documents=["alpha"], metadatas=[{"document_id": "d1"}]
    )


def test_query_delegates_to_collection_and_shapes_results():
    client, collection = _fake_client_and_collection()
    collection.query.return_value = {
        "ids": [["c1"]],
        "documents": [["alpha"]],
        "metadatas": [[{"document_id": "d1"}]],
        "distances": [[0.1]],
    }
    with patch("storage.chroma_http_vector_store.chromadb.HttpClient", return_value=client):
        store = ChromaHttpVectorStore(host="chroma", port=8000)

    results = store.query(embedding=[1.0, 0.0], top_k=5, where={"set_id": "s1"})

    collection.query.assert_called_once_with(
        query_embeddings=[[1.0, 0.0]], n_results=5, where={"set_id": "s1"}
    )
    assert results == [{"id": "c1", "text": "alpha", "metadata": {"document_id": "d1"}, "distance": 0.1}]


def test_delete_delegates_to_collection():
    client, collection = _fake_client_and_collection()
    with patch("storage.chroma_http_vector_store.chromadb.HttpClient", return_value=client):
        store = ChromaHttpVectorStore(host="chroma", port=8000)

    store.delete("d1")

    collection.delete.assert_called_once_with(where={"document_id": "d1"})
