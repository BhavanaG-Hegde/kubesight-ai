from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.models.enums import IncidentSeverity, IncidentType
from app.schemas.ai import AIQuestionRequest, IncidentAnalysisRequest
from app.schemas.monitoring import IncidentCandidateRead, IncidentDetectionResponse
from app.services.ai_assistant_service import AIAssistantService
from app.services.incident_history_service import IncidentHistoryService


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_analyze_incident_persists_ai_analysis(db_session: Session) -> None:
    incident = create_test_incident(db_session)
    service = FakeAIAssistantService(db_session, settings=make_test_settings())

    analysis = service.analyze_incident(
        incident.id,
        IncidentAnalysisRequest(include_pod_logs=False),
    )

    assert analysis.incident_id == incident.id
    assert analysis.model_name == "llama3.2"
    assert "probable root cause" in analysis.response.lower()


def test_answer_question_uses_incident_context(db_session: Session) -> None:
    incident = create_test_incident(db_session)
    service = FakeAIAssistantService(db_session, settings=make_test_settings())

    analysis = service.answer_question(
        AIQuestionRequest(
            question="Why is payment-service unhealthy?",
            incident_id=incident.id,
            include_logs=False,
        )
    )

    assert analysis.question == "Why is payment-service unhealthy?"
    assert analysis.incident_id == incident.id
    assert "payment-service" in service.last_prompt


class FakeAIAssistantService(AIAssistantService):
    last_prompt: str = ""

    def _generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return "Plain-language summary\nProbable root cause: configuration error"


def create_test_incident(db_session: Session):
    history = IncidentHistoryService(db_session, settings=make_test_settings())
    response = history.persist_detection_result(
        IncidentDetectionResponse(
            namespace="payments",
            pod_name="payment-service-9bf",
            scanned_pods=1,
            incidents=[
                IncidentCandidateRead(
                    incident_type=IncidentType.CRASH_LOOP_BACK_OFF,
                    severity=IncidentSeverity.CRITICAL,
                    namespace="payments",
                    pod_name="payment-service-9bf",
                    title="CrashLoopBackOff detected: payment-service-9bf",
                    summary="Container payment-service is CrashLoopBackOff.",
                    evidence=["restart_count=12"],
                    recommendation="Inspect previous logs and recent config changes.",
                    detected_at=datetime.now(UTC),
                )
            ],
        )
    )
    incident_read = response.incidents[0]
    return history.incidents.get(incident_read.id)


def make_test_settings() -> Settings:
    return Settings(
        monitored_cluster_name="test-cluster",
        secret_key="test-secret",
    )
