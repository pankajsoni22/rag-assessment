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
