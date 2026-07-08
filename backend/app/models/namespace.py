from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class KubernetesNamespace(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "kubernetes_namespaces"
    __table_args__ = (
        UniqueConstraint("cluster_id", "name", name="uq_namespaces_cluster_id_name"),
    )

    cluster_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("clusters.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    labels: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    cluster: Mapped["Cluster"] = relationship(back_populates="namespaces")
    deployments: Mapped[list["Deployment"]] = relationship(
        back_populates="namespace",
        cascade="all, delete-orphan",
    )
    pods: Mapped[list["Pod"]] = relationship(
        back_populates="namespace",
        cascade="all, delete-orphan",
    )
    services: Mapped[list["KubernetesService"]] = relationship(
        back_populates="namespace",
        cascade="all, delete-orphan",
    )
    incidents: Mapped[list["Incident"]] = relationship(back_populates="namespace")
