from __future__ import annotations

from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.kubernetes_deps import get_kubernetes_service, raise_kubernetes_http_error
from app.core.exceptions import (
    AIAnalysisError,
    AIAnalysisNotFoundError,
    IncidentNotFoundError,
    KubernetesClientError,
)
from app.schemas.ai import (
    AIAnalysisListResponse,
    AIAnalysisRead,
    AIQuestionRequest,
    IncidentAnalysisRequest,
    PodLogAnalysisRequest,
)
from app.services.ai_assistant_service import AIAssistantService
from app.services.kubernetes_service import KubernetesService

router = APIRouter(
    prefix="/ai",
    dependencies=[Depends(get_current_user)],
)


def get_ai_service(db: Annotated[Session, Depends(get_db)]) -> AIAssistantService:
    return AIAssistantService(db)


@router.get("/analyses", response_model=AIAnalysisListResponse)
def list_recent_analyses(
    service: Annotated[AIAssistantService, Depends(get_ai_service)],
    incident_id: UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AIAnalysisListResponse:
    return AIAnalysisListResponse(
        items=service.list_recent_analyses(
            incident_id=incident_id,
            limit=limit,
            offset=offset,
        )
    )


@router.get("/analyses/{analysis_id}", response_model=AIAnalysisRead)
def get_analysis(
    analysis_id: UUID,
    service: Annotated[AIAssistantService, Depends(get_ai_service)],
) -> AIAnalysisRead:
    try:
        return service.get_analysis(analysis_id)
    except AIAnalysisNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI analysis not found.",
        ) from exc


@router.post("/pods/logs/analyze", response_model=AIAnalysisRead)
def analyze_pod_logs(
    payload: PodLogAnalysisRequest,
    db: Annotated[Session, Depends(get_db)],
    kubernetes_service: Annotated[KubernetesService, Depends(get_kubernetes_service)],
) -> AIAnalysisRead:
    service = AIAssistantService(db, kubernetes_service=kubernetes_service)
    try:
        return service.analyze_pod_logs(payload)
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)
    except AIAnalysisError as exc:
        raise_ai_http_error(exc)


@router.post("/incidents/{incident_id}/analyze", response_model=AIAnalysisRead)
def analyze_incident(
    incident_id: UUID,
    payload: IncidentAnalysisRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AIAnalysisRead:
    try:
        service = AIAssistantService(db)
        return service.analyze_incident(incident_id, payload)
    except IncidentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        ) from exc
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)
    except AIAnalysisError as exc:
        raise_ai_http_error(exc)


@router.post("/ask", response_model=AIAnalysisRead)
def ask_ai_assistant(
    payload: AIQuestionRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AIAnalysisRead:
    try:
        service = AIAssistantService(db)
        return service.answer_question(payload)
    except IncidentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        ) from exc
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)
    except AIAnalysisError as exc:
        raise_ai_http_error(exc)


def raise_ai_http_error(exc: AIAnalysisError) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=str(exc),
    ) from exc
