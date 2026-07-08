from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session, joinedload

from app.models.metric import ClusterSnapshot, PodMetric
from app.models.namespace import KubernetesNamespace
from app.models.pod import Pod


class MetricsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_cluster_snapshot(self, snapshot: ClusterSnapshot) -> ClusterSnapshot:
        self.db.add(snapshot)
        self.db.flush()
        return snapshot

    def add_pod_metric(self, metric: PodMetric) -> PodMetric:
        self.db.add(metric)
        self.db.flush()
        return metric

    def list_cluster_snapshots(self, *, limit: int) -> list[ClusterSnapshot]:
        statement = (
            select(ClusterSnapshot)
            .options(joinedload(ClusterSnapshot.cluster))
            .order_by(desc(ClusterSnapshot.sampled_at))
            .limit(limit)
        )
        return list(self.db.execute(statement).scalars().all())

    def list_pod_metrics(
        self,
        *,
        namespace: str | None,
        pod_name: str | None,
        since: datetime | None,
        limit: int,
    ) -> list[PodMetric]:
        statement = self._pod_metrics_statement(
            namespace=namespace,
            pod_name=pod_name,
            since=since,
        )
        metrics = self.db.execute(
            statement.order_by(desc(PodMetric.sampled_at)).limit(limit)
        ).scalars()
        return list(metrics.all())

    def _pod_metrics_statement(
        self,
        *,
        namespace: str | None,
        pod_name: str | None,
        since: datetime | None,
    ) -> Select[tuple[PodMetric]]:
        statement = (
            select(PodMetric)
            .join(Pod)
            .join(KubernetesNamespace)
            .options(joinedload(PodMetric.pod).joinedload(Pod.namespace))
        )
        if namespace is not None:
            statement = statement.where(KubernetesNamespace.name == namespace)
        if pod_name is not None:
            statement = statement.where(Pod.name == pod_name)
        if since is not None:
            statement = statement.where(PodMetric.sampled_at >= since)
        return statement
