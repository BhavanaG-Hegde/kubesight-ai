from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.enums import IncidentSeverity, IncidentType
from app.schemas.incident import IncidentRead
from app.schemas.monitoring import IncidentCandidateRead, IncidentDetectionResponse
from app.services.incident_history_service import IncidentHistoryService


def test_list_incidents_supports_filters(
    client: TestClient,
    auth_headers: dict[str, str],
    db_session: Session,
) -> None:
    incident = seed_incident(db_session)

    response = client.get(
        "/api/v1/incidents",
        headers=auth_headers,
        params={
            "status": "open",
            "severity": "critical",
            "namespace": "payments",
            "search": "CrashLoop",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == str(incident.id)
    assert payload["items"][0]["pod_name"] == "payment-service-9bf"
    assert payload["items"][0]["incident_type"] == "crash_loop_back_off"


def test_update_incident_resolution(
    client: TestClient,
    auth_headers: dict[str, str],
    db_session: Session,
) -> None:
    incident = seed_incident(db_session)

    response = client.patch(
        f"/api/v1/incidents/{incident.id}",
        headers=auth_headers,
        json={
            "status": "resolved",
            "root_cause": "The migration job blocked application startup.",
            "resolution": "Rolled back the deployment and increased startup probe limits.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "resolved"
    assert payload["root_cause"] == "The migration job blocked application startup."
    assert payload["resolution"] == "Rolled back the deployment and increased startup probe limits."
    assert payload["resolved_at"] is not None


def test_get_incident_returns_not_found_for_unknown_id(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get(f"/api/v1/incidents/{uuid4()}", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found."


def test_update_incident_rejects_unknown_fields(
    client: TestClient,
    auth_headers: dict[str, str],
    db_session: Session,
) -> None:
    incident = seed_incident(db_session)

    response = client.patch(
        f"/api/v1/incidents/{incident.id}",
        headers=auth_headers,
        json={
            "status": "acknowledged",
            "owner": "platform-team",
        },
    )

    assert response.status_code == 422


def seed_incident(db_session: Session) -> IncidentRead:
    service = IncidentHistoryService(
        db_session,
        settings=Settings(
            monitored_cluster_name="test-cluster",
            secret_key="test-secret",
        ),
    )
    response = service.persist_detection_result(
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
                    evidence=["restart_count=12", "last_state=terminated"],
                    recommendation="Inspect previous logs and recent config changes.",
                    detected_at=datetime.now(UTC),
                )
            ],
        )
    )
    return response.incidents[0]
