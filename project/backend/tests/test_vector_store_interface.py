from backend.interfaces.vector_store import VectorStore
from storage.chroma_vector_store import ChromaVectorStore


def test_chroma_vector_store_satisfies_vector_store_protocol(tmp_path):
    store = ChromaVectorStore(persist_dir=tmp_path)
    assert isinstance(store, VectorStore)
