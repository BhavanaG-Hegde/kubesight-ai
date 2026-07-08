from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.kubernetes_deps import get_kubernetes_service, raise_kubernetes_http_error
from app.core.exceptions import KubernetesClientError
from app.schemas.metrics import (
    ClusterSnapshotRead,
    MetricsCollectionResponse,
    PodMetricRead,
)
from app.services.kubernetes_service import KubernetesService
from app.services.metrics_collection_service import MetricsCollectionService

router = APIRouter(
    prefix="/metrics",
    dependencies=[Depends(get_current_user)],
)


def get_metrics_collection_service(
    db: Annotated[Session, Depends(get_db)],
    kubernetes_service: Annotated[KubernetesService, Depends(get_kubernetes_service)],
) -> MetricsCollectionService:
    return MetricsCollectionService(db, kubernetes_service)


@router.post("/collect", response_model=MetricsCollectionResponse)
def collect_metrics(
    service: Annotated[
        MetricsCollectionService,
        Depends(get_metrics_collection_service),
    ],
) -> MetricsCollectionResponse:
    try:
        return service.collect_now()
    except KubernetesClientError as exc:
        raise_kubernetes_http_error(exc)


@router.get("/snapshots", response_model=list[ClusterSnapshotRead])
def list_cluster_snapshots(
    service: Annotated[
        MetricsCollectionService,
        Depends(get_metrics_collection_service),
    ],
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ClusterSnapshotRead]:
    return service.list_cluster_snapshots(limit=limit)


@router.get("/pods", response_model=list[PodMetricRead])
def list_pod_metrics(
    service: Annotated[
        MetricsCollectionService,
        Depends(get_metrics_collection_service),
    ],
    namespace: str | None = Query(default=None),
    pod_name: str | None = Query(default=None),
    since_minutes: int | None = Query(default=24 * 60, ge=1, le=90 * 24 * 60),
    limit: int = Query(default=200, ge=1, le=1000),
) -> list[PodMetricRead]:
    return service.list_pod_metrics(
        namespace=namespace,
        pod_name=pod_name,
        since_minutes=since_minutes,
        limit=limit,
    )
