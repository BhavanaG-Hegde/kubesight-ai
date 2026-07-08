from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.namespace import KubernetesNamespace


class Deployment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "deployments"
    __table_args__ = (
        UniqueConstraint("namespace_id", "name", name="uq_deployments_namespace_id_name"),
    )

    namespace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("kubernetes_namespaces.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    desired_replicas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_replicas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    labels: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    selector: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    namespace: Mapped["KubernetesNamespace"] = relationship(back_populates="deployments")
