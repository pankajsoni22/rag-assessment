from __future__ import annotations

import uuid

from llama_index.core.node_parser import SentenceSplitter

from backend.domain.models import Chunk

# Placeholder defaults — chunk size/overlap tuning is explicitly deferred in
# architecture.md's Open Items until there's a working pipeline to test against.
_DEFAULT_CHUNK_SIZE = 512
_DEFAULT_CHUNK_OVERLAP = 50


class ChunkingService:
    def __init__(
        self,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = _DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        self._splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def chunk(self, text: str, document_id: str, set_id: str) -> list[Chunk]:
        pieces = self._splitter.split_text(text)
        return [
            Chunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                set_id=set_id,
                text=piece,
                metadata={"document_id": document_id, "set_id": set_id},
            )
            for piece in pieces
            if piece.strip()
        ]
