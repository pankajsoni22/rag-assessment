from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies import get_document_set_service, get_rag_orchestrator
from backend.api.schemas import AnswerResponse, QueryRequest
from backend.clients.errors import RateLimitedError
from backend.services.document_set_service import DocumentSetService, SetNotFoundError
from backend.services.rag_orchestrator import RAGOrchestrator

logger = logging.getLogger("backend")

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

    try:
        result = orchestrator.answer_question(
            session_id=request.session_id, question=request.question, set_id=request.set_id
        )
    except RateLimitedError as exc:
        raise HTTPException(
            status_code=429,
            detail=(
                "The answering service is rate-limited or out of quota right now. "
                "Please wait a bit and try again."
            ),
        ) from exc
    except Exception as exc:
        # Detail shown to the user stays generic (never leak internals, per
        # B6 privacy) - the real cause is logged here instead.
        logger.exception("Query failed for session_id=%s", request.session_id)
        raise HTTPException(
            status_code=500,
            detail="Something went wrong while answering that question. Please try again.",
        ) from exc

    return AnswerResponse.model_validate(result)
