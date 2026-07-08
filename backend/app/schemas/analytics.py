from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class IncidentTrendPoint(BaseModel):
    date: date
    total: int = 0
    critical: int = 0
    warning: int = 0
    info: int = 0


class DistributionBucket(BaseModel):
    label: str
    value: int


class TopFailingPod(BaseModel):
    namespace: str | None = None
    pod_name: str | None = None
    incident_count: int
    critical_count: int
    last_seen_at: datetime | None = None


class PodResourcePoint(BaseModel):
    namespace: str
    pod_name: str
    cpu_millicores: int
    memory_mebibytes: int
    restart_count: int
    health_score: int


class AnalyticsOverviewResponse(BaseModel):
    days: int = Field(ge=1, le=90)
    generated_at: datetime
    total_incidents: int
    open_incidents: int
    critical_incidents: int
    resolved_incidents: int
    incident_trends: list[IncidentTrendPoint] = Field(default_factory=list)
    severity_distribution: list[DistributionBucket] = Field(default_factory=list)
    status_distribution: list[DistributionBucket] = Field(default_factory=list)
    incident_type_distribution: list[DistributionBucket] = Field(default_factory=list)
    top_failing_pods: list[TopFailingPod] = Field(default_factory=list)
    top_cpu_pods: list[PodResourcePoint] = Field(default_factory=list)
    top_memory_pods: list[PodResourcePoint] = Field(default_factory=list)
    top_restarting_pods: list[PodResourcePoint] = Field(default_factory=list)
