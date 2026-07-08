from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import LogSeverity
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class LogEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "log_entries"

    pod_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("pods.id", ondelete="CASCADE"),
        index=True,
    )
    container_name: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[LogSeverity] = mapped_column(
        Enum(LogSeverity, name="log_severity"),
        default=LogSeverity.UNKNOWN,
        index=True,
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    fingerprint: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)

    pod: Mapped["Pod"] = relationship(back_populates="logs")
