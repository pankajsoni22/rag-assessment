from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from backend.api.dependencies import get_document_set_service, get_ingestion_service
from backend.api.schemas import DocumentResponse
from backend.loaders.registry import format_from_filename
from backend.services.document_set_service import (
    DocumentNotFoundError,
    DocumentSetService,
    SetNotFoundError,
)
from backend.services.ingestion_service import IngestionService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
def upload_document(
    set_id: str,
    file: UploadFile,
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> DocumentResponse:
    filename = file.filename or "unnamed"
    try:
        format = format_from_filename(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix) as tmp:
        tmp.write(file.file.read())
        tmp.flush()
        try:
            document = ingestion_service.ingest(
                file=Path(tmp.name), filename=filename, format=format, set_id=set_id
            )
        except SetNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"Set not found: {exc}") from exc

    return DocumentResponse.model_validate(document)


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    set_id: str | None = None,
    doc_set_service: DocumentSetService = Depends(get_document_set_service),
) -> list[DocumentResponse]:
    return [
        DocumentResponse.model_validate(d) for d in doc_set_service.list_documents(set_id=set_id)
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    doc_set_service: DocumentSetService = Depends(get_document_set_service),
) -> DocumentResponse:
    try:
        document = doc_set_service.get_document(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", status_code=204)
def remove_document(
    document_id: str,
    doc_set_service: DocumentSetService = Depends(get_document_set_service),
) -> None:
    doc_set_service.remove_document(document_id)
