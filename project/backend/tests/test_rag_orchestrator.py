from backend.domain.models import AnswerResult, RetrievedChunk, Role
from backend.services.conversation_service import ConversationService
from backend.services.rag_orchestrator import RAGOrchestrator


class _FakeRetrievalService:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.chunks = chunks
        self.received_args: tuple | None = None

    def retrieve(self, query: str, set_id: str | None, top_k: int) -> list[RetrievedChunk]:
        self.received_args = (query, set_id, top_k)
        return self.chunks


class _FakeGenerationService:
    def __init__(self, result: AnswerResult) -> None:
        self.result = result
        self.received_args: tuple | None = None

    def generate(self, question, history, chunks) -> AnswerResult:
        self.received_args = (question, history, chunks)
        return self.result


def test_answer_question_calls_collaborators_in_order_and_returns_result():
    chunk = RetrievedChunk(chunk_id="c1", document_id="d1", text="t", metadata={}, distance=0.1)
    answer = AnswerResult(answer="42", citations=[], grounded=True)
    retrieval = _FakeRetrievalService([chunk])
    generation = _FakeGenerationService(answer)
    conversation = ConversationService()
    orchestrator = RAGOrchestrator(conversation, retrieval, generation)

    result = orchestrator.answer_question(session_id="s1", question="What is X?", set_id="set-a")

    assert result == answer
    assert retrieval.received_args == ("What is X?", "set-a", 5)
    question_arg, history_arg, chunks_arg = generation.received_args
    assert question_arg == "What is X?"
    assert history_arg == []  # no prior history for a fresh session
    assert chunks_arg == [chunk]


def test_answer_question_appends_both_turns_to_conversation():
    answer = AnswerResult(answer="42", citations=[], grounded=True)
    retrieval = _FakeRetrievalService([])
    generation = _FakeGenerationService(answer)
    conversation = ConversationService()
    orchestrator = RAGOrchestrator(conversation, retrieval, generation)

    orchestrator.answer_question(session_id="s1", question="What is X?", set_id=None)

    history = conversation.get_history("s1")
    assert len(history) == 2
    assert history[0].role == Role.USER
    assert history[0].content == "What is X?"
    assert history[1].role == Role.ASSISTANT
    assert history[1].content == "42"


def test_answer_question_appends_turns_even_when_not_grounded():
    answer = AnswerResult(answer="not found", citations=[], grounded=False)
    retrieval = _FakeRetrievalService([])
    generation = _FakeGenerationService(answer)
    conversation = ConversationService()
    orchestrator = RAGOrchestrator(conversation, retrieval, generation)

    orchestrator.answer_question(session_id="s1", question="What is X?", set_id=None)

    assert len(conversation.get_history("s1")) == 2


def test_answer_question_uses_prior_history_on_second_call():
    answer1 = AnswerResult(answer="a1", citations=[], grounded=True)
    answer2 = AnswerResult(answer="a2", citations=[], grounded=True)
    retrieval = _FakeRetrievalService([])
    generation = _FakeGenerationService(answer1)
    conversation = ConversationService()
    orchestrator = RAGOrchestrator(conversation, retrieval, generation)

    orchestrator.answer_question(session_id="s1", question="q1", set_id=None)
    generation.result = answer2
    orchestrator.answer_question(session_id="s1", question="q2", set_id=None)

    _question, history_arg, _chunks = generation.received_args
    assert [turn.content for turn in history_arg] == ["q1", "a1"]
