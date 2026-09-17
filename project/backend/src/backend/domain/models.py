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
    status: IngestionStatus
    uploaded_at: datetime
