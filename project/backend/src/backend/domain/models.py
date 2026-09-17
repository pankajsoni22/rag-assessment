from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DocumentFormat(str, Enum):
    PDF = "pdf"
    WORD = "word"
    TEXT = "text"
    MARKDOWN = "markdown"


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    set_id: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)
