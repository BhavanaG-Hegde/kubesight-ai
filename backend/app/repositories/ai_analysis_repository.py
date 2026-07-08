from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_analysis import AIAnalysis


class AIAnalysisRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, analysis_id: UUID) -> AIAnalysis | None:
        return self.db.get(AIAnalysis, analysis_id)

    def list_recent(self, *, limit: int, offset: int) -> list[AIAnalysis]:
        statement = (
            select(AIAnalysis)
            .order_by(AIAnalysis.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return self.db.execute(statement).scalars().all()

    def create(
        self,
        *,
        model_name: str,
        prompt: str,
        response: str,
        question: str | None,
        incident_id: UUID | None = None,
        pod_id: UUID | None = None,
    ) -> AIAnalysis:
        analysis = AIAnalysis(
            model_name=model_name,
            prompt=prompt,
            response=response,
            question=question,
            incident_id=incident_id,
            pod_id=pod_id,
        )
        self.db.add(analysis)
        self.db.flush()
        return analysis
