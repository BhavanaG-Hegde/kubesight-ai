from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.api.kubernetes_deps import get_kubernetes_service, raise_kubernetes_http_error
from app.core.exceptions import KubernetesClientError
from app.schemas.monitoring import (
    IncidentDetectionResponse,
    NamespaceHealthSummaryRead,
    PodHealthAssessmentRead,
)
from app.services.kubernetes_service import KubernetesService
from app.services.monitoring_service import MonitoringService

router = APIRouter(
    prefix="/monitoring",
    dependencies=[Depends(get_current_user)],
)


def get_monitoring_service(
    kubernetes_service: Annotated[KubernetesService, Depends(get_kubernetes_service)],
) -> MonitoringService:
    return MonitoringService(kubernetes_service)


@router.get("/namespaces/{namespace}/health", response_model=NamespaceHealthSummaryRead)
def get_namespace_health(
    namespace: str,
    service: Annotated[MonitoringService, Depends(get_monitoring_service)],
    include_logs: bool = Query(default=False),
    tail_lines: int = Query(default=200, ge=1, le=1000),
) -> NamespaceHealthSummaryRead:
    try:
        return service.get_namespace_health(
            namespace,
            include_logs=include_logs,
            tail_lines=tail_lines,
        )
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)


@router.get(
    "/namespaces/{namespace}/pods/{pod_name}/health",
    response_model=PodHealthAssessmentRead,
)
def get_pod_health(
    namespace: str,
    pod_name: str,
    service: Annotated[MonitoringService, Depends(get_monitoring_service)],
    include_logs: bool = Query(default=True),
    tail_lines: int = Query(default=200, ge=1, le=1000),
) -> PodHealthAssessmentRead:
    try:
        return service.get_pod_health(
            namespace,
            pod_name,
            include_logs=include_logs,
            tail_lines=tail_lines,
        )
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)


@router.get(
    "/namespaces/{namespace}/incidents/detect",
    response_model=IncidentDetectionResponse,
)
def detect_namespace_incidents(
    namespace: str,
    service: Annotated[MonitoringService, Depends(get_monitoring_service)],
    include_logs: bool = Query(default=True),
    tail_lines: int = Query(default=200, ge=1, le=1000),
) -> IncidentDetectionResponse:
    try:
        return service.detect_namespace_incidents(
            namespace,
            include_logs=include_logs,
            tail_lines=tail_lines,
        )
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)


@router.get(
    "/namespaces/{namespace}/pods/{pod_name}/incidents/detect",
    response_model=IncidentDetectionResponse,
)
def detect_pod_incidents(
    namespace: str,
    pod_name: str,
    service: Annotated[MonitoringService, Depends(get_monitoring_service)],
    include_logs: bool = Query(default=True),
    tail_lines: int = Query(default=200, ge=1, le=1000),
) -> IncidentDetectionResponse:
    try:
        return service.detect_pod_incidents(
            namespace,
            pod_name,
            include_logs=include_logs,
            tail_lines=tail_lines,
        )
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)
