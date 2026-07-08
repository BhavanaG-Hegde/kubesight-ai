from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.cluster import Cluster
    from app.models.pod import Pod


class ClusterSnapshot(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "cluster_snapshots"

    cluster_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("clusters.id", ondelete="CASCADE"),
        index=True,
    )
    total_pods: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    running_pods: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pending_pods: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_pods: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    restart_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cpu_millicores: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    memory_mebibytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    health_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    sampled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )

    cluster: Mapped["Cluster"] = relationship(back_populates="snapshots")


class PodMetric(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pod_metrics"

    pod_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("pods.id", ondelete="CASCADE"),
        index=True,
    )
    cpu_millicores: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    memory_mebibytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cpu_limit_millicores: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_limit_mebibytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sampled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=False,
    )

    pod: Mapped["Pod"] = relationship(back_populates="metrics")
