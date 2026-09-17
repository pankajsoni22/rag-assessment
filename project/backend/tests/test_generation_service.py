from datetime import datetime, timezone

from backend.domain.models import Citation, ConversationTurn, RetrievedChunk, Role
from backend.services.generation_service import GenerationService


class _FakeGenerationClient:
    def __init__(self, answer: str = "The answer is 42.") -> None:
        self.answer = answer
        self.received_messages: list[dict[str, str]] | None = None

    def complete(self, messages: list[dict[str, str]]) -> str:
        self.received_messages = messages
        return self.answer


def _chunk(chunk_id: str, document_id: str, filename: str, text: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        text=text,
        metadata={"filename": filename},
        distance=0.1,
    )


def test_generate_with_no_chunks_returns_not_found_without_calling_client():
    client = _FakeGenerationClient()
    service = GenerationService(client)

    result = service.generate(question="What is X?", history=[], chunks=[])

    assert result.grounded is False
    assert result.citations == []
    assert "couldn't find" in result.answer.lower()
    assert client.received_messages is None


def test_generate_with_chunks_calls_client_and_returns_citations():
    client = _FakeGenerationClient(answer="X is 42.")
    service = GenerationService(client)
    chunks = [_chunk("c1", "d1", "doc.txt", "X is 42.")]

    result = service.generate(question="What is X?", history=[], chunks=chunks)

    assert result.grounded is True
    assert result.answer == "X is 42."
    assert result.citations == [Citation(document_id="d1", filename="doc.txt", chunk_id="c1")]
    assert client.received_messages is not None


def test_generate_includes_history_and_question_in_messages():
    client = _FakeGenerationClient()
    service = GenerationService(client)
    history = [
        ConversationTurn(role=Role.USER, content="prior question", timestamp=datetime.now(timezone.utc)),
        ConversationTurn(role=Role.ASSISTANT, content="prior answer", timestamp=datetime.now(timezone.utc)),
    ]
    chunks = [_chunk("c1", "d1", "doc.txt", "context text")]

    service.generate(question="follow-up?", history=history, chunks=chunks)

    roles = [m["role"] for m in client.received_messages]
    contents = [m["content"] for m in client.received_messages]
    assert roles == ["system", "user", "assistant", "user"]
    assert contents[-1] == "follow-up?"
    assert "prior question" in contents
    assert "prior answer" in contents
    assert "context text" in contents[0]
