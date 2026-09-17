from __future__ import annotations

from typing import Protocol

from backend.domain.models import AnswerResult, Citation, ConversationTurn, RetrievedChunk

_NOT_FOUND_ANSWER = "I couldn't find anything in the documents to answer that."

_SYSTEM_PROMPT = (
    "You are a document question-answering assistant. Answer the question using "
    "only the provided context. If the context doesn't contain enough information "
    "to answer, say so clearly instead of guessing."
)


class GenerationClient(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str: ...


class GenerationService:
    def __init__(self, client: GenerationClient) -> None:
        self._client = client

    def generate(
        self,
        question: str,
        history: list[ConversationTurn],
        chunks: list[RetrievedChunk],
    ) -> AnswerResult:
        if not chunks:
            return AnswerResult(answer=_NOT_FOUND_ANSWER, citations=[], grounded=False)

        messages = self._build_messages(question, history, chunks)
        answer = self._client.complete(messages)
        citations = [
            Citation(
                document_id=chunk.document_id,
                filename=chunk.metadata.get("filename", ""),
                chunk_id=chunk.chunk_id,
            )
            for chunk in chunks
        ]
        return AnswerResult(answer=answer, citations=citations, grounded=True)

    def _build_messages(
        self,
        question: str,
        history: list[ConversationTurn],
        chunks: list[RetrievedChunk],
    ) -> list[dict[str, str]]:
        context = "\n\n".join(
            f"[{i + 1}] (from {chunk.metadata.get('filename', 'unknown')}) {chunk.text}"
            for i, chunk in enumerate(chunks)
        )
        messages = [{"role": "system", "content": f"{_SYSTEM_PROMPT}\n\nContext:\n{context}"}]
        for turn in history:
            messages.append({"role": turn.role.value, "content": turn.content})
        messages.append({"role": "user", "content": question})
        return messages
