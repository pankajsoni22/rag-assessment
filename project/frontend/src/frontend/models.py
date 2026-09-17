from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DocumentSetView:
    id: str
    name: str
    created_at: datetime


@dataclass(frozen=True)
class DocumentView:
    id: str
    set_id: str
    filename: str
    format: str
    status: str
    uploaded_at: datetime


@dataclass(frozen=True)
class CitationView:
    document_id: str
    filename: str
    chunk_id: str


@dataclass(frozen=True)
class AnswerView:
    answer: str
    citations: list[CitationView]
    grounded: bool


@dataclass(frozen=True)
class ChatMessageView:
    role: str
    content: str
    citations: list[CitationView] | None = None
    grounded: bool | None = None
