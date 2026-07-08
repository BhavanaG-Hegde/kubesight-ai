from __future__ import annotations

from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.core.exceptions import KubernetesClientError, KubernetesResourceNotFoundError
from app.schemas.kubernetes import (
    ClusterSummaryRead,
    DeploymentRead,
    NamespaceRead,
    PodEventRead,
    PodLogRead,
    PodRead,
    ServiceRead,
)
from app.services.kubernetes_service import KubernetesService

router = APIRouter(
    prefix="/kubernetes",
    dependencies=[Depends(get_current_user)],
)


def get_kubernetes_service() -> KubernetesService:
    try:
        return KubernetesService()
    except KubernetesClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


def raise_kubernetes_http_error(exc: KubernetesClientError) -> NoReturn:
    if isinstance(exc, KubernetesResourceNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=str(exc),
    ) from exc


@router.get("/summary", response_model=ClusterSummaryRead)
def get_cluster_summary(
    service: Annotated[KubernetesService, Depends(get_kubernetes_service)],
) -> ClusterSummaryRead:
    try:
        return service.get_cluster_summary()
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)


@router.get("/namespaces", response_model=list[NamespaceRead])
def list_namespaces(
    service: Annotated[KubernetesService, Depends(get_kubernetes_service)],
) -> list[NamespaceRead]:
    try:
        return service.list_namespaces()
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)


@router.get("/namespaces/{namespace}/deployments", response_model=list[DeploymentRead])
def list_deployments(
    namespace: str,
    service: Annotated[KubernetesService, Depends(get_kubernetes_service)],
) -> list[DeploymentRead]:
    try:
        return service.list_deployments(namespace)
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)


@router.get("/namespaces/{namespace}/services", response_model=list[ServiceRead])
def list_services(
    namespace: str,
    service: Annotated[KubernetesService, Depends(get_kubernetes_service)],
) -> list[ServiceRead]:
    try:
        return service.list_services(namespace)
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)


@router.get("/namespaces/{namespace}/pods", response_model=list[PodRead])
def list_pods(
    namespace: str,
    service: Annotated[KubernetesService, Depends(get_kubernetes_service)],
) -> list[PodRead]:
    try:
        return service.list_pods(namespace)
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)


@router.get("/namespaces/{namespace}/pods/{pod_name}", response_model=PodRead)
def get_pod(
    namespace: str,
    pod_name: str,
    service: Annotated[KubernetesService, Depends(get_kubernetes_service)],
) -> PodRead:
    try:
        return service.get_pod(namespace, pod_name)
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)


@router.get("/namespaces/{namespace}/pods/{pod_name}/events", response_model=list[PodEventRead])
def list_pod_events(
    namespace: str,
    pod_name: str,
    service: Annotated[KubernetesService, Depends(get_kubernetes_service)],
) -> list[PodEventRead]:
    try:
        return service.list_pod_events(namespace, pod_name)
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)


@router.get("/namespaces/{namespace}/pods/{pod_name}/logs", response_model=PodLogRead)
def get_pod_logs(
    namespace: str,
    pod_name: str,
    service: Annotated[KubernetesService, Depends(get_kubernetes_service)],
    container: str | None = Query(default=None),
    tail_lines: int = Query(default=200, ge=1, le=5000),
    previous: bool = Query(default=False),
    timestamps: bool = Query(default=True),
) -> PodLogRead:
    try:
        return service.get_pod_logs(
            namespace,
            pod_name,
            container=container,
            tail_lines=tail_lines,
            previous=previous,
            timestamps=timestamps,
        )
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)
