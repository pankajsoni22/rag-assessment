from __future__ import annotations

from backend.domain.models import ConversationTurn


class ConversationService:
    def __init__(self) -> None:
        self._sessions: dict[str, list[ConversationTurn]] = {}

    def get_history(self, session_id: str) -> list[ConversationTurn]:
        return list(self._sessions.get(session_id, []))

    def append_turn(self, session_id: str, turn: ConversationTurn) -> None:
        self._sessions.setdefault(session_id, []).append(turn)
