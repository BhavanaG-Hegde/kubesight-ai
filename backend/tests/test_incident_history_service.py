from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.models.enums import IncidentSeverity, IncidentStatus, IncidentType
from app.schemas.incident import IncidentUpdate
from app.schemas.monitoring import IncidentCandidateRead, IncidentDetectionResponse
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


def test_persist_detection_result_creates_incident(db_session: Session) -> None:
    service = IncidentHistoryService(db_session, settings=test_settings())

    response = service.persist_detection_result(detection_response())

    assert response.created == 1
    assert response.updated == 0
    assert response.incidents[0].namespace == "payments"
    assert response.incidents[0].pod_name == "payment-service-9bf"
    assert response.incidents[0].status == IncidentStatus.OPEN


def test_persist_detection_result_updates_active_incident(db_session: Session) -> None:
    service = IncidentHistoryService(db_session, settings=test_settings())

    first_response = service.persist_detection_result(detection_response())
    second_response = service.persist_detection_result(detection_response())
    list_response = service.list_incidents(
        status=None,
        severity=None,
        incident_type=None,
        namespace=None,
        pod_name=None,
        search=None,
        limit=50,
        offset=0,
    )

    assert first_response.created == 1
    assert second_response.created == 0
    assert second_response.updated == 1
    assert list_response.total == 1


def test_update_incident_marks_resolved(db_session: Session) -> None:
    service = IncidentHistoryService(db_session, settings=test_settings())
    response = service.persist_detection_result(detection_response())

    updated = service.update_incident(
        response.incidents[0].id,
        IncidentUpdate(
            status=IncidentStatus.RESOLVED,
            resolution="Rolled back the broken deployment.",
        ),
    )

    assert updated.status == IncidentStatus.RESOLVED
    assert updated.resolution == "Rolled back the broken deployment."
    assert updated.resolved_at is not None


def detection_response() -> IncidentDetectionResponse:
    return IncidentDetectionResponse(
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


def test_settings() -> Settings:
    return Settings(
        monitored_cluster_name="test-cluster",
        secret_key="test-secret",
    )
