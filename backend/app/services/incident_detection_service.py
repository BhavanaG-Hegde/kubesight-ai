from __future__ import annotations

from datetime import UTC, datetime

from app.models.enums import IncidentSeverity, IncidentType
from app.schemas.monitoring import (
    HealthSignalRead,
    IncidentCandidateRead,
    PodHealthAssessmentRead,
)


class IncidentDetectionService:
    def detect_from_assessment(
        self,
        assessment: PodHealthAssessmentRead,
    ) -> list[IncidentCandidateRead]:
        incidents: list[IncidentCandidateRead] = []
        for signal in assessment.signals:
            incident_type = self._incident_type_for_signal(signal)
            if incident_type is None:
                continue
            incidents.append(self._candidate_for_signal(assessment, signal, incident_type))
        return self._deduplicate_incidents(incidents)

    def _candidate_for_signal(
        self,
        assessment: PodHealthAssessmentRead,
        signal: HealthSignalRead,
        incident_type: IncidentType,
    ) -> IncidentCandidateRead:
        title = self._title_for_incident(incident_type, assessment.pod_name)
        return IncidentCandidateRead(
            incident_type=incident_type,
            severity=self._severity_for_incident(incident_type, signal.severity),
            namespace=assessment.namespace,
            pod_name=assessment.pod_name,
            title=title,
            summary=signal.message,
            evidence=[value for value in [signal.evidence] if value],
            recommendation=self._recommendation_for_incident(incident_type),
            detected_at=datetime.now(UTC),
        )

    def _incident_type_for_signal(self, signal: HealthSignalRead) -> IncidentType | None:
        mapping = {
            "crash_loop_back_off": IncidentType.CRASH_LOOP_BACK_OFF,
            "oom_killed": IncidentType.OOM_KILLED,
            "image_pull_back_off": IncidentType.IMAGE_PULL_BACK_OFF,
            "high_restart_count": IncidentType.HIGH_RESTART_COUNT,
            "timeout_errors": IncidentType.TIMEOUT_ERRORS,
            "database_connection_failure": IncidentType.DATABASE_CONNECTION_FAILURE,
            "error_log_spike": IncidentType.ERROR_LOG_SPIKE,
            "pod_not_ready": IncidentType.POD_NOT_READY,
            "pod_failed": IncidentType.POD_NOT_READY,
        }
        return mapping.get(signal.code)

    def _severity_for_incident(
        self,
        incident_type: IncidentType,
        fallback: IncidentSeverity,
    ) -> IncidentSeverity:
        critical_incidents = {
            IncidentType.CRASH_LOOP_BACK_OFF,
            IncidentType.OOM_KILLED,
            IncidentType.IMAGE_PULL_BACK_OFF,
            IncidentType.DATABASE_CONNECTION_FAILURE,
        }
        if incident_type in critical_incidents:
            return IncidentSeverity.CRITICAL
        return fallback

    def _title_for_incident(self, incident_type: IncidentType, pod_name: str) -> str:
        titles = {
            IncidentType.CRASH_LOOP_BACK_OFF: "CrashLoopBackOff detected",
            IncidentType.OOM_KILLED: "Container killed due to memory pressure",
            IncidentType.IMAGE_PULL_BACK_OFF: "Container image pull failure",
            IncidentType.HIGH_RESTART_COUNT: "High pod restart count",
            IncidentType.TIMEOUT_ERRORS: "Timeout errors detected in logs",
            IncidentType.DATABASE_CONNECTION_FAILURE: "Database connectivity failure",
            IncidentType.ERROR_LOG_SPIKE: "Repeated application errors",
            IncidentType.POD_NOT_READY: "Pod is not healthy",
        }
        return f"{titles[incident_type]}: {pod_name}"

    def _recommendation_for_incident(self, incident_type: IncidentType) -> str:
        recommendations = {
            IncidentType.CRASH_LOOP_BACK_OFF: (
                "Inspect the previous container logs, verify startup configuration, "
                "and check recent deployments or missing environment variables."
            ),
            IncidentType.OOM_KILLED: (
                "Review memory usage, increase memory limits if justified, and inspect "
                "the application for leaks or oversized requests."
            ),
            IncidentType.IMAGE_PULL_BACK_OFF: (
                "Verify the image name, tag, registry credentials, and network access "
                "from the cluster nodes."
            ),
            IncidentType.HIGH_RESTART_COUNT: (
                "Check container logs and events to identify whether restarts are caused "
                "by crashes, probes, resource pressure, or node disruption."
            ),
            IncidentType.TIMEOUT_ERRORS: (
                "Check downstream service health, network policies, DNS resolution, "
                "and application timeout settings."
            ),
            IncidentType.DATABASE_CONNECTION_FAILURE: (
                "Validate database service DNS, credentials, connection pool settings, "
                "network policies, and database availability."
            ),
            IncidentType.ERROR_LOG_SPIKE: (
                "Inspect the repeated error lines, compare with recent releases, and "
                "check dependent service health."
            ),
            IncidentType.POD_NOT_READY: (
                "Inspect readiness probes, container status, pod events, and resource "
                "availability on the scheduled node."
            ),
        }
        return recommendations[incident_type]

    def _deduplicate_incidents(
        self,
        incidents: list[IncidentCandidateRead],
    ) -> list[IncidentCandidateRead]:
        seen: set[tuple[IncidentType, str, str]] = set()
        unique_incidents: list[IncidentCandidateRead] = []
        for incident in incidents:
            key = (incident.incident_type, incident.namespace, incident.pod_name)
            if key in seen:
                continue
            seen.add(key)
            unique_incidents.append(incident)
        return unique_incidents
