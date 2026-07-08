from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import ClusterStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Cluster(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clusters"

    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    context_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_server: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ClusterStatus] = mapped_column(
        Enum(ClusterStatus, name="cluster_status"),
        default=ClusterStatus.DISCONNECTED,
        nullable=False,
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    namespaces: Mapped[list["KubernetesNamespace"]] = relationship(
        back_populates="cluster",
        cascade="all, delete-orphan",
    )
    snapshots: Mapped[list["ClusterSnapshot"]] = relationship(
        back_populates="cluster",
        cascade="all, delete-orphan",
    )
    incidents: Mapped[list["Incident"]] = relationship(back_populates="cluster")
