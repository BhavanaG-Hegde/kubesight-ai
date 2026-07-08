from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import IncidentSeverity, IncidentStatus
from app.models.incident import Incident
from app.models.pod import Pod
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    DistributionBucket,
    IncidentTrendPoint,
    PodResourcePoint,
    TopFailingPod,
)


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_overview(self, *, days: int) -> AnalyticsOverviewResponse:
        now = datetime.now(UTC)
        start_date = now.date() - timedelta(days=days - 1)
        cutoff = datetime.combine(start_date, time.min, tzinfo=UTC)
        incidents = self._recent_incidents(since=cutoff)

        return AnalyticsOverviewResponse(
            days=days,
            generated_at=now,
            total_incidents=len(incidents),
            open_incidents=sum(1 for item in incidents if item.status == IncidentStatus.OPEN),
            critical_incidents=sum(
                1 for item in incidents if item.severity == IncidentSeverity.CRITICAL
            ),
            resolved_incidents=sum(
                1 for item in incidents if item.status == IncidentStatus.RESOLVED
            ),
            incident_trends=self._incident_trends(incidents=incidents, days=days, now=now),
            severity_distribution=self._distribution(
                Counter(incident.severity.value for incident in incidents)
            ),
            status_distribution=self._distribution(
                Counter(incident.status.value for incident in incidents)
            ),
            incident_type_distribution=self._distribution(
                Counter(incident.incident_type.value for incident in incidents)
            ),
            top_failing_pods=self._top_failing_pods(incidents),
            top_cpu_pods=self._top_pods(desc(Pod.cpu_millicores)),
            top_memory_pods=self._top_pods(desc(Pod.memory_mebibytes)),
            top_restarting_pods=self._top_pods(desc(Pod.restart_count)),
        )

    def _recent_incidents(self, *, since: datetime) -> list[Incident]:
        statement = (
            select(Incident)
            .options(joinedload(Incident.namespace), joinedload(Incident.pod))
            .where(Incident.last_seen_at >= since)
            .order_by(Incident.last_seen_at.desc())
        )
        return list(self.db.execute(statement).scalars().all())

    def _incident_trends(
        self,
        *,
        incidents: list[Incident],
        days: int,
        now: datetime,
    ) -> list[IncidentTrendPoint]:
        start = now.date() - timedelta(days=days - 1)
        buckets = {
            start + timedelta(days=offset): _TrendBucket()
            for offset in range(days)
        }

        for incident in incidents:
            bucket = buckets.get(incident.last_seen_at.date())
            if bucket is None:
                continue
            bucket.total += 1
            if incident.severity == IncidentSeverity.CRITICAL:
                bucket.critical += 1
            elif incident.severity == IncidentSeverity.WARNING:
                bucket.warning += 1
            else:
                bucket.info += 1

        return [
            IncidentTrendPoint(
                date=day,
                total=bucket.total,
                critical=bucket.critical,
                warning=bucket.warning,
                info=bucket.info,
            )
            for day, bucket in buckets.items()
        ]

    def _distribution(self, counts: Counter[str]) -> list[DistributionBucket]:
        return [
            DistributionBucket(label=label, value=value)
            for label, value in counts.most_common()
            if value > 0
        ]

    def _top_failing_pods(self, incidents: list[Incident]) -> list[TopFailingPod]:
        pod_counts: dict[tuple[str | None, str | None], _PodIncidentBucket] = defaultdict(
            _PodIncidentBucket
        )
        for incident in incidents:
            key = (
                incident.namespace.name if incident.namespace else None,
                incident.pod.name if incident.pod else None,
            )
            bucket = pod_counts[key]
            bucket.incident_count += 1
            if incident.severity == IncidentSeverity.CRITICAL:
                bucket.critical_count += 1
            if bucket.last_seen_at is None or incident.last_seen_at > bucket.last_seen_at:
                bucket.last_seen_at = incident.last_seen_at

        ranked = sorted(
            pod_counts.items(),
            key=lambda item: (
                item[1].critical_count,
                item[1].incident_count,
                item[1].last_seen_at or datetime.min.replace(tzinfo=UTC),
            ),
            reverse=True,
        )
        return [
            TopFailingPod(
                namespace=namespace,
                pod_name=pod_name,
                incident_count=bucket.incident_count,
                critical_count=bucket.critical_count,
                last_seen_at=bucket.last_seen_at,
            )
            for (namespace, pod_name), bucket in ranked[:10]
        ]

    def _top_pods(self, ordering) -> list[PodResourcePoint]:  # noqa: ANN001
        statement = (
            select(Pod)
            .options(joinedload(Pod.namespace))
            .order_by(ordering)
            .limit(10)
        )
        pods = self.db.execute(statement).scalars().all()
        return [
            PodResourcePoint(
                namespace=pod.namespace.name,
                pod_name=pod.name,
                cpu_millicores=pod.cpu_millicores,
                memory_mebibytes=pod.memory_mebibytes,
                restart_count=pod.restart_count,
                health_score=pod.health_score,
            )
            for pod in pods
            if pod.cpu_millicores > 0 or pod.memory_mebibytes > 0 or pod.restart_count > 0
        ]


@dataclass
class _TrendBucket:
    total: int = 0
    critical: int = 0
    warning: int = 0
    info: int = 0


@dataclass
class _PodIncidentBucket:
    incident_count: int = 0
    critical_count: int = 0
    last_seen_at: datetime | None = None
