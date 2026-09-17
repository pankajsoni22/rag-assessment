from __future__ import annotations

from datetime import datetime, timezone

from backend.domain.models import AnswerResult, ConversationTurn, Role
from backend.services.conversation_service import ConversationService
from backend.services.generation_service import GenerationService
from backend.services.retrieval_service import RetrievalService

# Placeholder default — top_k tuning is an explicit deferral in architecture.md's
# Open Items until there's a working pipeline to test against.
_DEFAULT_TOP_K = 5


class RAGOrchestrator:
    def __init__(
        self,
        conversation_service: ConversationService,
        retrieval_service: RetrievalService,
        generation_service: GenerationService,
    ) -> None:
        self._conversation_service = conversation_service
        self._retrieval_service = retrieval_service
        self._generation_service = generation_service

    def answer_question(
        self, session_id: str, question: str, set_id: str | None
    ) -> AnswerResult:
        history = self._conversation_service.get_history(session_id)
        chunks = self._retrieval_service.retrieve(question, set_id, top_k=_DEFAULT_TOP_K)
        result = self._generation_service.generate(question, history, chunks)

        now = datetime.now(timezone.utc)
        self._conversation_service.append_turn(
            session_id, ConversationTurn(role=Role.USER, content=question, timestamp=now)
        )
        self._conversation_service.append_turn(
            session_id,
            ConversationTurn(role=Role.ASSISTANT, content=result.answer, timestamp=now),
        )

        return result
