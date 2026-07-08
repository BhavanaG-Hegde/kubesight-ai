from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class KubernetesService(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "kubernetes_services"
    __table_args__ = (
        UniqueConstraint("namespace_id", "name", name="uq_services_namespace_id_name"),
    )

    namespace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("kubernetes_namespaces.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    service_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    cluster_ip: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ports: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    labels: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    namespace: Mapped["KubernetesNamespace"] = relationship(back_populates="services")
