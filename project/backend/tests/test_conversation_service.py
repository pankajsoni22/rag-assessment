from datetime import datetime, timezone

from backend.domain.models import ConversationTurn, Role
from backend.services.conversation_service import ConversationService


def test_get_history_for_unseen_session_returns_empty_list():
    service = ConversationService()

    assert service.get_history("missing") == []


def test_append_turn_and_get_history_round_trip():
    service = ConversationService()
    turn = ConversationTurn(role=Role.USER, content="hi", timestamp=datetime.now(timezone.utc))

    service.append_turn("s1", turn)

    assert service.get_history("s1") == [turn]


def test_history_scoped_per_session():
    service = ConversationService()
    turn_a = ConversationTurn(role=Role.USER, content="a", timestamp=datetime.now(timezone.utc))
    turn_b = ConversationTurn(role=Role.USER, content="b", timestamp=datetime.now(timezone.utc))

    service.append_turn("s1", turn_a)
    service.append_turn("s2", turn_b)

    assert service.get_history("s1") == [turn_a]
    assert service.get_history("s2") == [turn_b]


def test_append_turn_preserves_order():
    service = ConversationService()
    turn1 = ConversationTurn(role=Role.USER, content="q1", timestamp=datetime.now(timezone.utc))
    turn2 = ConversationTurn(role=Role.ASSISTANT, content="a1", timestamp=datetime.now(timezone.utc))

    service.append_turn("s1", turn1)
    service.append_turn("s1", turn2)

    assert service.get_history("s1") == [turn1, turn2]
