from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.kubernetes_deps import get_kubernetes_service, raise_kubernetes_http_error
from app.core.exceptions import IncidentNotFoundError, KubernetesClientError
from app.models.enums import IncidentSeverity, IncidentStatus, IncidentType
from app.schemas.incident import (
    IncidentListResponse,
    IncidentRead,
    IncidentSyncResponse,
    IncidentUpdate,
)
from app.services.incident_history_service import IncidentHistoryService
from app.services.kubernetes_service import KubernetesService
from app.services.monitoring_service import MonitoringService

router = APIRouter(
    prefix="/incidents",
    dependencies=[Depends(get_current_user)],
)


def get_incident_history_service(
    db: Annotated[Session, Depends(get_db)],
) -> IncidentHistoryService:
    return IncidentHistoryService(db)


def get_monitoring_service(
    kubernetes_service: Annotated[KubernetesService, Depends(get_kubernetes_service)],
) -> MonitoringService:
    return MonitoringService(kubernetes_service)


@router.get("", response_model=IncidentListResponse)
def list_incidents(
    service: Annotated[IncidentHistoryService, Depends(get_incident_history_service)],
    status_filter: IncidentStatus | None = Query(default=None, alias="status"),
    severity: IncidentSeverity | None = Query(default=None),
    incident_type: IncidentType | None = Query(default=None),
    namespace: str | None = Query(default=None),
    pod_name: str | None = Query(default=None),
    search: str | None = Query(default=None, min_length=2, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> IncidentListResponse:
    return service.list_incidents(
        status=status_filter,
        severity=severity,
        incident_type=incident_type,
        namespace=namespace,
        pod_name=pod_name,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(
    incident_id: UUID,
    service: Annotated[IncidentHistoryService, Depends(get_incident_history_service)],
) -> IncidentRead:
    try:
        return service.get_incident(incident_id)
    except IncidentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        ) from exc


@router.patch("/{incident_id}", response_model=IncidentRead)
def update_incident(
    incident_id: UUID,
    payload: IncidentUpdate,
    service: Annotated[IncidentHistoryService, Depends(get_incident_history_service)],
) -> IncidentRead:
    try:
        return service.update_incident(incident_id, payload)
    except IncidentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found.",
        ) from exc


@router.post("/sync/namespaces/{namespace}", response_model=IncidentSyncResponse)
def sync_namespace_incidents(
    namespace: str,
    monitoring: Annotated[MonitoringService, Depends(get_monitoring_service)],
    history: Annotated[IncidentHistoryService, Depends(get_incident_history_service)],
    include_logs: bool = Query(default=True),
    tail_lines: int = Query(default=200, ge=1, le=1000),
) -> IncidentSyncResponse:
    try:
        detection = monitoring.detect_namespace_incidents(
            namespace,
            include_logs=include_logs,
            tail_lines=tail_lines,
        )
        return history.persist_detection_result(detection)
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)


@router.post(
    "/sync/namespaces/{namespace}/pods/{pod_name}",
    response_model=IncidentSyncResponse,
)
def sync_pod_incidents(
    namespace: str,
    pod_name: str,
    monitoring: Annotated[MonitoringService, Depends(get_monitoring_service)],
    history: Annotated[IncidentHistoryService, Depends(get_incident_history_service)],
    include_logs: bool = Query(default=True),
    tail_lines: int = Query(default=200, ge=1, le=1000),
) -> IncidentSyncResponse:
    try:
        detection = monitoring.detect_pod_incidents(
            namespace,
            pod_name,
            include_logs=include_logs,
            tail_lines=tail_lines,
        )
        return history.persist_detection_result(detection)
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)
