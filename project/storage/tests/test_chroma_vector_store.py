import pytest

from storage.chroma_vector_store import ChromaVectorStore


@pytest.fixture
def store(tmp_path):
    return ChromaVectorStore(persist_dir=tmp_path)


def test_upsert_and_query_round_trip(store):
    store.upsert(
        [
            {
                "id": "c1",
                "embedding": [1.0, 0.0],
                "text": "alpha",
                "metadata": {"document_id": "d1", "set_id": "s1"},
            },
            {
                "id": "c2",
                "embedding": [0.0, 1.0],
                "text": "beta",
                "metadata": {"document_id": "d1", "set_id": "s1"},
            },
        ]
    )

    results = store.query(embedding=[1.0, 0.0], top_k=1)

    assert len(results) == 1
    assert results[0]["id"] == "c1"
    assert results[0]["text"] == "alpha"
    assert results[0]["metadata"] == {"document_id": "d1", "set_id": "s1"}
    assert "distance" in results[0]


def test_query_scoped_by_metadata_filter(store):
    store.upsert(
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

    results = store.query(embedding=[1.0, 0.0], top_k=5, where={"set_id": "s1"})

    assert [r["id"] for r in results] == ["c1"]


def test_upsert_overwrites_existing_id(store):
    store.upsert(
        [{"id": "c1", "embedding": [1.0, 0.0], "text": "old", "metadata": {"document_id": "d1"}}]
    )
    store.upsert(
        [{"id": "c1", "embedding": [1.0, 0.0], "text": "new", "metadata": {"document_id": "d1"}}]
    )

    results = store.query(embedding=[1.0, 0.0], top_k=5)

    assert len(results) == 1
    assert results[0]["text"] == "new"


def test_delete_removes_all_chunks_for_document(store):
    store.upsert(
        [
            {"id": "c1", "embedding": [1.0, 0.0], "text": "a", "metadata": {"document_id": "d1"}},
            {"id": "c2", "embedding": [1.0, 0.0], "text": "b", "metadata": {"document_id": "d1"}},
            {"id": "c3", "embedding": [1.0, 0.0], "text": "c", "metadata": {"document_id": "d2"}},
        ]
    )

    store.delete("d1")

    results = store.query(embedding=[1.0, 0.0], top_k=5)
    assert [r["id"] for r in results] == ["c3"]


def test_query_on_empty_store_returns_empty_list(store):
    assert store.query(embedding=[1.0, 0.0], top_k=5) == []


def test_upsert_with_no_records_is_a_no_op(store):
    store.upsert([])
    assert store.query(embedding=[1.0, 0.0], top_k=5) == []
