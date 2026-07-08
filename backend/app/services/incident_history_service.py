from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import IncidentNotFoundError
from app.models.cluster import Cluster
from app.models.enums import (
    HealthStatus,
    IncidentSeverity,
    IncidentStatus,
    IncidentType,
)
from app.models.incident import Incident
from app.repositories.incident_repository import IncidentRepository
from app.repositories.kubernetes_catalog_repository import KubernetesCatalogRepository
from app.schemas.incident import (
    IncidentListResponse,
    IncidentRead,
    IncidentSyncResponse,
    IncidentUpdate,
)
from app.schemas.monitoring import IncidentCandidateRead, IncidentDetectionResponse


class IncidentHistoryService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.incidents = IncidentRepository(db)
        self.catalog = KubernetesCatalogRepository(db)

    def list_incidents(
        self,
        *,
        status: IncidentStatus | None,
        severity: IncidentSeverity | None,
        incident_type: IncidentType | None,
        namespace: str | None,
        pod_name: str | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> IncidentListResponse:
        incidents, total = self.incidents.list(
            status=status,
            severity=severity,
            incident_type=incident_type,
            namespace=namespace,
            pod_name=pod_name,
            search=search,
            limit=limit,
            offset=offset,
        )
        return IncidentListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=[self.to_read_model(incident) for incident in incidents],
        )

    def get_incident(self, incident_id: UUID) -> IncidentRead:
        incident = self.incidents.get(incident_id)
        if incident is None:
            raise IncidentNotFoundError("Incident not found.")
        return self.to_read_model(incident)

    def update_incident(self, incident_id: UUID, payload: IncidentUpdate) -> IncidentRead:
        incident = self.incidents.get(incident_id)
        if incident is None:
            raise IncidentNotFoundError("Incident not found.")

        if payload.status is not None:
            incident.status = payload.status
            incident.resolved_at = (
                datetime.now(UTC) if payload.status == IncidentStatus.RESOLVED else None
            )
        if payload.root_cause is not None:
            incident.root_cause = payload.root_cause
        if payload.recommendation is not None:
            incident.recommendation = payload.recommendation
        if payload.resolution is not None:
            incident.resolution = payload.resolution

        self.db.commit()
        self.db.refresh(incident)
        return self.to_read_model(incident)

    def persist_detection_result(
        self,
        detection: IncidentDetectionResponse,
    ) -> IncidentSyncResponse:
        cluster = self.catalog.ensure_cluster(
            name=self.settings.monitored_cluster_name,
            context_name=self.settings.kubernetes_context,
        )

        created = 0
        updated = 0
        saved_incidents: list[Incident] = []
        for candidate in detection.incidents:
            incident, was_created = self._upsert_candidate(candidate, cluster=cluster)
            if was_created:
                created += 1
            else:
                updated += 1
            saved_incidents.append(incident)

        self.db.commit()
        for incident in saved_incidents:
            self.db.refresh(incident)

        return IncidentSyncResponse(
            namespace=detection.namespace,
            pod_name=detection.pod_name,
            scanned_pods=detection.scanned_pods,
            created=created,
            updated=updated,
            incidents=[self.to_read_model(incident) for incident in saved_incidents],
        )

    def to_read_model(self, incident: Incident) -> IncidentRead:
        return IncidentRead(
            id=incident.id,
            cluster_name=incident.cluster.name,
            namespace=incident.namespace.name if incident.namespace else None,
            pod_name=incident.pod.name if incident.pod else None,
            incident_type=incident.incident_type,
            severity=incident.severity,
            status=incident.status,
            title=incident.title,
            summary=incident.summary,
            root_cause=incident.root_cause,
            recommendation=incident.recommendation,
            resolution=incident.resolution,
            detection_source=incident.detection_source,
            first_seen_at=incident.first_seen_at,
            last_seen_at=incident.last_seen_at,
            resolved_at=incident.resolved_at,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
        )

    def _upsert_candidate(
        self,
        candidate: IncidentCandidateRead,
        *,
        cluster: Cluster,
    ) -> tuple[Incident, bool]:
        namespace = self.catalog.ensure_namespace(cluster=cluster, name=candidate.namespace)
        pod = self.catalog.ensure_pod(
            namespace=namespace,
            name=candidate.pod_name,
            health_status=self._health_status_for_severity(candidate.severity),
        )

        incident = self.incidents.find_active(
            cluster_id=cluster.id,
            namespace_id=namespace.id,
            pod_id=pod.id,
            incident_type=candidate.incident_type,
        )
        if incident is None:
            incident = self.incidents.add(
                Incident(
                    cluster_id=cluster.id,
                    namespace_id=namespace.id,
                    pod_id=pod.id,
                    incident_type=candidate.incident_type,
                    severity=candidate.severity,
                    status=IncidentStatus.OPEN,
                    title=candidate.title,
                    summary=self._summary_with_evidence(candidate),
                    recommendation=candidate.recommendation,
                    detection_source="rule_engine",
                    first_seen_at=candidate.detected_at,
                    last_seen_at=candidate.detected_at,
                )
            )
            return incident, True

        incident.severity = candidate.severity
        incident.title = candidate.title
        incident.summary = self._summary_with_evidence(candidate)
        incident.recommendation = candidate.recommendation
        incident.last_seen_at = candidate.detected_at
        return incident, False

    def _summary_with_evidence(self, candidate: IncidentCandidateRead) -> str:
        if not candidate.evidence:
            return candidate.summary
        evidence = "\n".join(f"- {item}" for item in candidate.evidence)
        return f"{candidate.summary}\n\nEvidence:\n{evidence}"

    def _health_status_for_severity(self, severity: IncidentSeverity) -> HealthStatus:
        if severity == IncidentSeverity.CRITICAL:
            return HealthStatus.CRITICAL
        if severity == IncidentSeverity.WARNING:
            return HealthStatus.WARNING
        return HealthStatus.HEALTHY
