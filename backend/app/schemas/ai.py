from __future__ import annotations

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class PodLogAnalysisRequest(BaseModel):
    namespace: str = Field(min_length=1, max_length=120)
    pod_name: str = Field(min_length=1, max_length=255)
    container: str | None = Field(default=None, max_length=120)
    tail_lines: int = Field(default=200, ge=1, le=2000)
    previous: bool = False
    question: str | None = Field(default=None, max_length=1000)


class IncidentAnalysisRequest(BaseModel):
    question: str | None = Field(default=None, max_length=1000)
    include_pod_logs: bool = True
    tail_lines: int = Field(default=200, ge=1, le=2000)


class AIQuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    incident_id: UUID | None = None
    namespace: str | None = Field(default=None, max_length=120)
    pod_name: str | None = Field(default=None, max_length=255)
    include_logs: bool = True
    tail_lines: int = Field(default=200, ge=1, le=2000)

    @model_validator(mode="after")
    def validate_pod_context(self) -> Self:
        if bool(self.namespace) != bool(self.pod_name):
            raise ValueError("namespace and pod_name must be provided together.")
        return self


class AIAnalysisRead(BaseModel):
    id: UUID
    incident_id: UUID | None = None
    pod_id: UUID | None = None
    model_name: str
    question: str | None = None
    response: str
    created_at: datetime


class AIAnalysisListResponse(BaseModel):
    items: list[AIAnalysisRead]
