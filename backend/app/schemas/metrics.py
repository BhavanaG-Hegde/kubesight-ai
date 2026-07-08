from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PodResourceMetricRead(BaseModel):
    namespace: str
    pod_name: str
    cpu_millicores: int
    memory_mebibytes: int


class ClusterSnapshotRead(BaseModel):
    id: UUID
    cluster_name: str
    total_pods: int
    running_pods: int
    pending_pods: int
    failed_pods: int
    restart_count: int
    cpu_millicores: int
    memory_mebibytes: int
    health_score: int
    sampled_at: datetime


class PodMetricRead(BaseModel):
    id: UUID
    namespace: str
    pod_name: str
    cpu_millicores: int
    memory_mebibytes: int
    cpu_limit_millicores: int | None = None
    memory_limit_mebibytes: int | None = None
    sampled_at: datetime
    created_at: datetime
    updated_at: datetime


class MetricsCollectionResponse(BaseModel):
    cluster_name: str
    sampled_at: datetime
    metrics_api_available: bool
    total_pods: int
    running_pods: int
    pending_pods: int
    failed_pods: int
    restart_count: int
    cpu_millicores: int
    memory_mebibytes: int
    health_score: int
    persisted_pod_metrics: int
    pods_without_metrics: int
    warnings: list[str] = Field(default_factory=list)
