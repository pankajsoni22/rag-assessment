from backend.services.chunking_service import ChunkingService


def test_chunk_short_text_returns_single_chunk_with_expected_metadata():
    service = ChunkingService()

    chunks = service.chunk("Just a short sentence.", document_id="d1", set_id="s1")

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.document_id == "d1"
    assert chunk.set_id == "s1"
    assert chunk.text == "Just a short sentence."
    assert chunk.metadata == {"document_id": "d1", "set_id": "s1"}
    assert chunk.id


def test_chunk_long_text_splits_into_multiple_chunks():
    service = ChunkingService(chunk_size=50, chunk_overlap=0)
    text = " ".join(f"word{i}" for i in range(200))

    chunks = service.chunk(text, document_id="d1", set_id="s1")

    assert len(chunks) > 1
    assert all(chunk.document_id == "d1" for chunk in chunks)


def test_chunk_ids_are_unique():
    service = ChunkingService(chunk_size=50, chunk_overlap=0)
    text = " ".join(f"word{i}" for i in range(200))

    chunks = service.chunk(text, document_id="d1", set_id="s1")

    assert len({chunk.id for chunk in chunks}) == len(chunks)


def test_chunk_empty_text_returns_no_chunks():
    service = ChunkingService()

    assert service.chunk("", document_id="d1", set_id="s1") == []
