from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import HealthStatus, IncidentSeverity, IncidentType


class HealthSignalRead(BaseModel):
    code: str
    severity: IncidentSeverity
    message: str
    evidence: str | None = None
    score_impact: int


class PodHealthAssessmentRead(BaseModel):
    namespace: str
    pod_name: str
    phase: str
    health_status: HealthStatus
    health_score: int
    restart_count: int
    ready_containers: int
    total_containers: int
    signals: list[HealthSignalRead] = Field(default_factory=list)


class NamespaceHealthSummaryRead(BaseModel):
    namespace: str
    total_pods: int
    healthy_pods: int
    warning_pods: int
    critical_pods: int
    average_health_score: int
    pods: list[PodHealthAssessmentRead] = Field(default_factory=list)


class IncidentCandidateRead(BaseModel):
    incident_type: IncidentType
    severity: IncidentSeverity
    namespace: str
    pod_name: str
    title: str
    summary: str
    evidence: list[str] = Field(default_factory=list)
    recommendation: str
    detected_at: datetime


class IncidentDetectionResponse(BaseModel):
    namespace: str
    pod_name: str | None = None
    scanned_pods: int
    incidents: list[IncidentCandidateRead] = Field(default_factory=list)
