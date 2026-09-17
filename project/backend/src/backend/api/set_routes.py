from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_document_set_service
from backend.api.schemas import CreateSetRequest, DocumentSetResponse
from backend.services.document_set_service import DocumentSetService

router = APIRouter(prefix="/sets", tags=["sets"])


@router.post("", response_model=DocumentSetResponse, status_code=201)
def create_set(
    request: CreateSetRequest,
    doc_set_service: DocumentSetService = Depends(get_document_set_service),
) -> DocumentSetResponse:
    document_set = doc_set_service.create_set(request.name)
    return DocumentSetResponse.model_validate(document_set)


@router.get("", response_model=list[DocumentSetResponse])
def list_sets(
    doc_set_service: DocumentSetService = Depends(get_document_set_service),
) -> list[DocumentSetResponse]:
    return [DocumentSetResponse.model_validate(s) for s in doc_set_service.list_sets()]


@router.delete("/{set_id}", status_code=204)
def delete_set(
    set_id: str,
    doc_set_service: DocumentSetService = Depends(get_document_set_service),
) -> None:
    doc_set_service.delete_set(set_id)
