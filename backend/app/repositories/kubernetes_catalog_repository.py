from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cluster import Cluster
from app.models.enums import ClusterStatus, HealthStatus, PodPhase
from app.models.namespace import KubernetesNamespace
from app.models.pod import Pod


class KubernetesCatalogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_cluster(
        self,
        *,
        name: str,
        context_name: str | None,
    ) -> Cluster:
        cluster = self.db.execute(
            select(Cluster).where(Cluster.name == name)
        ).scalar_one_or_none()
        if cluster is None:
            cluster = Cluster(
                name=name,
                context_name=context_name,
                status=ClusterStatus.CONNECTED,
                last_seen_at=datetime.now(UTC),
            )
            self.db.add(cluster)
        else:
            cluster.status = ClusterStatus.CONNECTED
            cluster.context_name = context_name or cluster.context_name
            cluster.last_seen_at = datetime.now(UTC)

        self.db.flush()
        return cluster

    def ensure_namespace(self, *, cluster: Cluster, name: str) -> KubernetesNamespace:
        namespace = self.db.execute(
            select(KubernetesNamespace).where(
                KubernetesNamespace.cluster_id == cluster.id,
                KubernetesNamespace.name == name,
            )
        ).scalar_one_or_none()
        if namespace is None:
            namespace = KubernetesNamespace(
                cluster_id=cluster.id,
                name=name,
                labels={},
            )
            self.db.add(namespace)

        self.db.flush()
        return namespace

    def ensure_pod(
        self,
        *,
        namespace: KubernetesNamespace,
        name: str,
        phase: str = PodPhase.UNKNOWN.value,
        health_status: HealthStatus = HealthStatus.UNKNOWN,
        health_score: int = 100,
        restart_count: int = 0,
        ready_containers: int = 0,
        total_containers: int = 0,
    ) -> Pod:
        pod = self.db.execute(
            select(Pod).where(Pod.namespace_id == namespace.id, Pod.name == name)
        ).scalar_one_or_none()

        if pod is None:
            pod = Pod(
                namespace_id=namespace.id,
                name=name,
                labels={},
                annotations={},
            )
            self.db.add(pod)

        pod.phase = self._pod_phase(phase)
        pod.health_status = health_status
        pod.health_score = health_score
        pod.restart_count = restart_count
        pod.ready_containers = ready_containers
        pod.total_containers = total_containers
        pod.last_seen_at = datetime.now(UTC)

        self.db.flush()
        return pod

    def _pod_phase(self, value: str) -> PodPhase:
        for phase in PodPhase:
            if phase.value == value:
                return phase
        return PodPhase.UNKNOWN
