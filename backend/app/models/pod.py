from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import HealthStatus, PodPhase, enum_values
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Pod(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pods"
    __table_args__ = (
        UniqueConstraint("namespace_id", "name", name="uq_pods_namespace_id_name"),
    )

    namespace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("kubernetes_namespaces.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    node_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phase: Mapped[PodPhase] = mapped_column(
        Enum(PodPhase, name="pod_phase", values_callable=enum_values),
        default=PodPhase.UNKNOWN,
        index=True,
        nullable=False,
    )
    health_status: Mapped[HealthStatus] = mapped_column(
        Enum(HealthStatus, name="health_status", values_callable=enum_values),
        default=HealthStatus.UNKNOWN,
        index=True,
        nullable=False,
    )
    health_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    restart_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ready_containers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_containers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cpu_millicores: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    memory_mebibytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_kind: Mapped[str | None] = mapped_column(String(80), nullable=True)
    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    labels: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    annotations: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    namespace: Mapped["KubernetesNamespace"] = relationship(back_populates="pods")
    metrics: Mapped[list["PodMetric"]] = relationship(
        back_populates="pod",
        cascade="all, delete-orphan",
    )
    logs: Mapped[list["LogEntry"]] = relationship(
        back_populates="pod",
        cascade="all, delete-orphan",
    )
    events: Mapped[list["PodEvent"]] = relationship(
        back_populates="pod",
        cascade="all, delete-orphan",
    )
    incidents: Mapped[list["Incident"]] = relationship(back_populates="pod")
    ai_analyses: Mapped[list["AIAnalysis"]] = relationship(back_populates="pod")
