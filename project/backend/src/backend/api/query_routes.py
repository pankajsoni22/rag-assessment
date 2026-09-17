from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies import get_document_set_service, get_rag_orchestrator
from backend.api.schemas import AnswerResponse, QueryRequest
from backend.services.document_set_service import DocumentSetService, SetNotFoundError
from backend.services.rag_orchestrator import RAGOrchestrator

router = APIRouter(tags=["query"])


@router.post("/query", response_model=AnswerResponse)
def ask_question(
    request: QueryRequest,
    orchestrator: RAGOrchestrator = Depends(get_rag_orchestrator),
    doc_set_service: DocumentSetService = Depends(get_document_set_service),
) -> AnswerResponse:
    if request.set_id is not None:
        try:
            doc_set_service.get_set(request.set_id)
        except SetNotFoundError as exc:
            raise HTTPException(status_code=404, detail=f"Set not found: {exc}") from exc

    result = orchestrator.answer_question(
        session_id=request.session_id, question=request.question, set_id=request.set_id
    )
    return AnswerResponse.model_validate(result)
