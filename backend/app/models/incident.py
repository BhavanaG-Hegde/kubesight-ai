from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import IncidentSeverity, IncidentStatus, IncidentType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Incident(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "incidents"

    cluster_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("clusters.id", ondelete="CASCADE"),
        index=True,
    )
    namespace_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("kubernetes_namespaces.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    pod_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("pods.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    incident_type: Mapped[IncidentType] = mapped_column(
        Enum(IncidentType, name="incident_type"),
        index=True,
        nullable=False,
    )
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity, name="incident_severity"),
        index=True,
        nullable=False,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, name="incident_status"),
        default=IncidentStatus.OPEN,
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    detection_source: Mapped[str] = mapped_column(String(80), default="rule_engine", nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    cluster: Mapped["Cluster"] = relationship(back_populates="incidents")
    namespace: Mapped["KubernetesNamespace | None"] = relationship(back_populates="incidents")
    pod: Mapped["Pod | None"] = relationship(back_populates="incidents")
    ai_analyses: Mapped[list["AIAnalysis"]] = relationship(back_populates="incident")
