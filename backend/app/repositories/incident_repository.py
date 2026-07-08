from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.cluster import Cluster
from app.models.enums import IncidentSeverity, IncidentStatus, IncidentType
from app.models.incident import Incident
from app.models.namespace import KubernetesNamespace
from app.models.pod import Pod


class IncidentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, incident_id: UUID) -> Incident | None:
        statement = (
            select(Incident)
            .options(
                joinedload(Incident.cluster),
                joinedload(Incident.namespace),
                joinedload(Incident.pod),
            )
            .where(Incident.id == incident_id)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def list(
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
    ) -> tuple[list[Incident], int]:
        statement = self._filtered_statement(
            status=status,
            severity=severity,
            incident_type=incident_type,
            namespace=namespace,
            pod_name=pod_name,
            search=search,
        ).options(
            joinedload(Incident.cluster),
            joinedload(Incident.namespace),
            joinedload(Incident.pod),
        )
        count_statement = select(func.count()).select_from(
            self._filtered_statement(
                status=status,
                severity=severity,
                incident_type=incident_type,
                namespace=namespace,
                pod_name=pod_name,
                search=search,
            ).subquery()
        )
        total = self.db.execute(count_statement).scalar_one()
        incidents = self.db.execute(
            statement.order_by(Incident.last_seen_at.desc()).offset(offset).limit(limit)
        ).scalars().all()
        return incidents, total

    def find_active(
        self,
        *,
        cluster_id: UUID,
        namespace_id: UUID | None,
        pod_id: UUID | None,
        incident_type: IncidentType,
    ) -> Incident | None:
        statement = select(Incident).where(
            Incident.cluster_id == cluster_id,
            Incident.namespace_id == namespace_id,
            Incident.pod_id == pod_id,
            Incident.incident_type == incident_type,
            Incident.status != IncidentStatus.RESOLVED,
        )
        return self.db.execute(statement).scalar_one_or_none()

    def add(self, incident: Incident) -> Incident:
        self.db.add(incident)
        self.db.flush()
        return incident

    def _filtered_statement(
        self,
        *,
        status: IncidentStatus | None,
        severity: IncidentSeverity | None,
        incident_type: IncidentType | None,
        namespace: str | None,
        pod_name: str | None,
        search: str | None,
    ) -> Select[tuple[Incident]]:
        statement = select(Incident).join(Cluster)
        if namespace is not None or search is not None:
            statement = statement.outerjoin(KubernetesNamespace)
        if pod_name is not None or search is not None:
            statement = statement.outerjoin(Pod)
        if status is not None:
            statement = statement.where(Incident.status == status)
        if severity is not None:
            statement = statement.where(Incident.severity == severity)
        if incident_type is not None:
            statement = statement.where(Incident.incident_type == incident_type)
        if namespace is not None:
            statement = statement.where(KubernetesNamespace.name == namespace)
        if pod_name is not None:
            statement = statement.where(Pod.name == pod_name)
        if search:
            pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    Incident.title.ilike(pattern),
                    Incident.summary.ilike(pattern),
                    Incident.root_cause.ilike(pattern),
                    Incident.recommendation.ilike(pattern),
                    Incident.resolution.ilike(pattern),
                    KubernetesNamespace.name.ilike(pattern),
                    Pod.name.ilike(pattern),
                    Cluster.name.ilike(pattern),
                )
            )
        return statement
