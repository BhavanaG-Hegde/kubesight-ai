from __future__ import annotations

from app.models.enums import HealthStatus
from app.schemas.kubernetes import ContainerStatusRead, PodLogRead, PodRead
from app.services.health_scoring_service import HealthScoringService
from app.services.incident_detection_service import IncidentDetectionService


def test_healthy_running_pod_scores_healthy() -> None:
    pod = PodRead(
        name="api-7d9",
        namespace="default",
        phase="Running",
        restart_count=0,
        ready_containers=1,
        total_containers=1,
        containers=[
            ContainerStatusRead(
                name="api",
                ready=True,
                restart_count=0,
                state="running",
            )
        ],
    )

    assessment = HealthScoringService().assess_pod(pod)

    assert assessment.health_score == 100
    assert assessment.health_status == HealthStatus.HEALTHY
    assert assessment.signals == []


def test_crash_looping_pod_scores_critical_and_detects_incident() -> None:
    pod = PodRead(
        name="payment-service-9bf",
        namespace="payments",
        phase="Running",
        restart_count=12,
        ready_containers=0,
        total_containers=1,
        containers=[
            ContainerStatusRead(
                name="payment-service",
                ready=False,
                restart_count=12,
                state="waiting",
                reason="CrashLoopBackOff",
            )
        ],
    )

    assessment = HealthScoringService().assess_pod(pod)
    incidents = IncidentDetectionService().detect_from_assessment(assessment)

    assert assessment.health_status == HealthStatus.CRITICAL
    assert any(signal.code == "crash_loop_back_off" for signal in assessment.signals)
    assert any(incident.incident_type == "crash_loop_back_off" for incident in incidents)


def test_database_errors_in_logs_reduce_health_score() -> None:
    pod = PodRead(
        name="orders-api-85f",
        namespace="orders",
        phase="Running",
        restart_count=0,
        ready_containers=1,
        total_containers=1,
        containers=[
            ContainerStatusRead(
                name="orders-api",
                ready=True,
                restart_count=0,
                state="running",
            )
        ],
    )
    logs = PodLogRead(
        namespace="orders",
        pod_name="orders-api-85f",
        tail_lines=100,
        lines=[
            "ERROR database connection refused",
            "timeout while opening postgres connection",
        ],
    )

    assessment = HealthScoringService().assess_pod(pod, logs=logs)

    assert assessment.health_status == HealthStatus.WARNING
    assert any(signal.code == "database_connection_failure" for signal in assessment.signals)
