from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.pod import Pod


class PodEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pod_events"
    __table_args__ = (
        UniqueConstraint("pod_id", "event_uid", name="uq_pod_events_pod_id_event_uid"),
    )

    pod_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("pods.id", ondelete="CASCADE"),
        index=True,
    )
    event_uid: Mapped[str] = mapped_column(String(120), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    source_component: Mapped[str | None] = mapped_column(String(120), nullable=True)
    count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    pod: Mapped["Pod"] = relationship(back_populates="events")
