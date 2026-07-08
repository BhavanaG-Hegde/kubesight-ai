from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.pod import Pod


class AIAnalysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_analyses"

    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    pod_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("pods.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)

    incident: Mapped["Incident | None"] = relationship(back_populates="ai_analyses")
    pod: Mapped["Pod | None"] = relationship(back_populates="ai_analyses")
