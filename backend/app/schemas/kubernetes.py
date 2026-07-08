from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NamespaceRead(BaseModel):
    name: str
    status: str
    labels: dict[str, str] = Field(default_factory=dict)


class ClusterSummaryRead(BaseModel):
    total_pods: int
    running_pods: int
    pending_pods: int
    failed_pods: int
    restart_count: int


class DeploymentRead(BaseModel):
    name: str
    namespace: str
    desired_replicas: int
    ready_replicas: int
    available_replicas: int
    updated_replicas: int
    labels: dict[str, str] = Field(default_factory=dict)
    selector: dict[str, Any] = Field(default_factory=dict)


class ServicePortRead(BaseModel):
    name: str | None = None
    protocol: str
    port: int
    target_port: str | None = None
    node_port: int | None = None


class ServiceRead(BaseModel):
    name: str
    namespace: str
    service_type: str | None = None
    cluster_ip: str | None = None
    ports: list[ServicePortRead] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)


class ContainerStatusRead(BaseModel):
    name: str
    ready: bool
    restart_count: int
    state: str
    reason: str | None = None


class PodRead(BaseModel):
    name: str
    namespace: str
    phase: str
    node_name: str | None = None
    pod_ip: str | None = None
    host_ip: str | None = None
    restart_count: int
    ready_containers: int
    total_containers: int
    containers: list[ContainerStatusRead] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    created_at: datetime | None = None


class PodEventRead(BaseModel):
    event_type: str
    reason: str
    message: str
    source_component: str | None = None
    count: int
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None


class PodLogRead(BaseModel):
    namespace: str
    pod_name: str
    container: str | None = None
    tail_lines: int
    lines: list[str]
