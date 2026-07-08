from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IncidentSeverity, IncidentStatus, IncidentType


class IncidentRead(BaseModel):
    id: UUID
    cluster_name: str
    namespace: str | None = None
    pod_name: str | None = None
    incident_type: IncidentType
    severity: IncidentSeverity
    status: IncidentStatus
    title: str
    summary: str
    root_cause: str | None = None
    recommendation: str | None = None
    resolution: str | None = None
    detection_source: str
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class IncidentListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[IncidentRead] = Field(default_factory=list)


class IncidentUpdate(BaseModel):
    status: IncidentStatus | None = None
    root_cause: str | None = Field(default=None, max_length=5000)
    recommendation: str | None = Field(default=None, max_length=5000)
    resolution: str | None = Field(default=None, max_length=5000)

    model_config = ConfigDict(extra="forbid")


class IncidentSyncResponse(BaseModel):
    namespace: str
    pod_name: str | None = None
    scanned_pods: int
    created: int
    updated: int
    incidents: list[IncidentRead] = Field(default_factory=list)
