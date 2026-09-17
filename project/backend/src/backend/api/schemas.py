from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.domain.models import DocumentFormat, IngestionStatus


class CreateSetRequest(BaseModel):
    name: str


class DocumentSetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    created_at: datetime


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    set_id: str
    filename: str
    format: DocumentFormat
    status: IngestionStatus
    uploaded_at: datetime
