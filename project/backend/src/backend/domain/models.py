from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DocumentFormat(str, Enum):
    PDF = "pdf"
    WORD = "word"
    TEXT = "text"
    MARKDOWN = "markdown"


class IngestionStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    set_id: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentSet:
    id: str
    name: str
    created_at: datetime


@dataclass(frozen=True)
class Document:
    id: str
    set_id: str
    filename: str
    format: DocumentFormat
    content_hash: str
    status: IngestionStatus
    uploaded_at: datetime


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    text: str
    metadata: dict[str, str]
    distance: float


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class ConversationTurn:
    role: Role
    content: str
    timestamp: datetime


@dataclass(frozen=True)
class Citation:
    document_id: str
    filename: str
    chunk_id: str


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    citations: list[Citation]
    grounded: bool
