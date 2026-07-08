from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import KubernetesClientError
from app.models.cluster import Cluster
from app.models.enums import HealthStatus
from app.models.metric import ClusterSnapshot, PodMetric
from app.models.pod import Pod
from app.repositories.kubernetes_catalog_repository import KubernetesCatalogRepository
from app.repositories.metrics_repository import MetricsRepository
from app.schemas.kubernetes import PodRead
from app.schemas.metrics import (
    ClusterSnapshotRead,
    MetricsCollectionResponse,
    PodMetricRead,
    PodResourceMetricRead,
)
from app.services.health_scoring_service import HealthScoringService
from app.services.kubernetes_service import KubernetesService


class MetricsCollectionService:
    def __init__(
        self,
        db: Session,
        kubernetes_service: KubernetesService,
        settings: Settings | None = None,
        health_scoring_service: HealthScoringService | None = None,
    ) -> None:
        self.db = db
        self.kubernetes = kubernetes_service
        self.settings = settings or get_settings()
        self.health_scoring = health_scoring_service or HealthScoringService()
        self.catalog = KubernetesCatalogRepository(db)
        self.metrics = MetricsRepository(db)

    def collect_now(self) -> MetricsCollectionResponse:
        sampled_at = datetime.now(UTC)
        warnings: list[str] = []
        pods = self.kubernetes.list_all_pods()
        metric_map, metrics_api_available = self._pod_metric_map(warnings)

        cluster = self.catalog.ensure_cluster(
            name=self.settings.monitored_cluster_name,
            context_name=self.settings.kubernetes_context,
        )

        running_pods = sum(1 for pod in pods if pod.phase == "Running")
        pending_pods = sum(1 for pod in pods if pod.phase == "Pending")
        failed_pods = sum(1 for pod in pods if pod.phase == "Failed")
        restart_count = sum(pod.restart_count for pod in pods)
        total_cpu = 0
        total_memory = 0
        persisted_pod_metrics = 0
        health_scores: list[int] = []

        for pod in pods:
            usage = metric_map.get((pod.namespace, pod.name))
            cpu_millicores = usage.cpu_millicores if usage else 0
            memory_mebibytes = usage.memory_mebibytes if usage else 0
            total_cpu += cpu_millicores
            total_memory += memory_mebibytes

            assessment = self.health_scoring.assess_pod(pod)
            health_scores.append(assessment.health_score)
            pod_record = self._upsert_pod(
                cluster=cluster,
                pod=pod,
                cpu_millicores=cpu_millicores,
                memory_mebibytes=memory_mebibytes,
                health_score=assessment.health_score,
                health_status=assessment.health_status,
            )
            if usage is not None:
                self.metrics.add_pod_metric(
                    PodMetric(
                        pod_id=pod_record.id,
                        cpu_millicores=cpu_millicores,
                        memory_mebibytes=memory_mebibytes,
                        sampled_at=sampled_at,
                    )
                )
                persisted_pod_metrics += 1

        health_score = self._cluster_health_score(health_scores)
        self.metrics.add_cluster_snapshot(
            ClusterSnapshot(
                cluster_id=cluster.id,
                total_pods=len(pods),
                running_pods=running_pods,
                pending_pods=pending_pods,
                failed_pods=failed_pods,
                restart_count=restart_count,
                cpu_millicores=total_cpu,
                memory_mebibytes=total_memory,
                health_score=health_score,
                sampled_at=sampled_at,
            )
        )
        self.db.commit()

        return MetricsCollectionResponse(
            cluster_name=cluster.name,
            sampled_at=sampled_at,
            metrics_api_available=metrics_api_available,
            total_pods=len(pods),
            running_pods=running_pods,
            pending_pods=pending_pods,
            failed_pods=failed_pods,
            restart_count=restart_count,
            cpu_millicores=total_cpu,
            memory_mebibytes=total_memory,
            health_score=health_score,
            persisted_pod_metrics=persisted_pod_metrics,
            pods_without_metrics=len(pods) - persisted_pod_metrics,
            warnings=warnings,
        )

    def list_cluster_snapshots(self, *, limit: int) -> list[ClusterSnapshotRead]:
        snapshots = self.metrics.list_cluster_snapshots(limit=limit)
        return [self._snapshot_read_model(snapshot) for snapshot in snapshots]

    def list_pod_metrics(
        self,
        *,
        namespace: str | None,
        pod_name: str | None,
        since_minutes: int | None,
        limit: int,
    ) -> list[PodMetricRead]:
        since = (
            datetime.now(UTC) - timedelta(minutes=since_minutes)
            if since_minutes is not None
            else None
        )
        metrics = self.metrics.list_pod_metrics(
            namespace=namespace,
            pod_name=pod_name,
            since=since,
            limit=limit,
        )
        return [self._pod_metric_read_model(metric) for metric in metrics]

    def _pod_metric_map(
        self,
        warnings: list[str],
    ) -> tuple[dict[tuple[str, str], PodResourceMetricRead], bool]:
        try:
            metrics = self.kubernetes.list_pod_resource_metrics()
        except KubernetesClientError as exc:
            warnings.append(
                "Metrics API is unavailable. Install Metrics Server to collect CPU "
                f"and memory samples. Detail: {exc}"
            )
            return {}, False
        return {(metric.namespace, metric.pod_name): metric for metric in metrics}, True

    def _upsert_pod(
        self,
        *,
        cluster: Cluster,
        pod: PodRead,
        cpu_millicores: int,
        memory_mebibytes: int,
        health_score: int,
        health_status: HealthStatus,
    ) -> Pod:
        namespace = self.catalog.ensure_namespace(cluster=cluster, name=pod.namespace)
        return self.catalog.ensure_pod(
            namespace=namespace,
            name=pod.name,
            node_name=pod.node_name,
            phase=pod.phase,
            health_status=health_status,
            health_score=health_score,
            restart_count=pod.restart_count,
            ready_containers=pod.ready_containers,
            total_containers=pod.total_containers,
            cpu_millicores=cpu_millicores,
            memory_mebibytes=memory_mebibytes,
            labels=pod.labels,
            annotations=pod.annotations,
        )

    def _cluster_health_score(self, health_scores: list[int]) -> int:
        if not health_scores:
            return 100
        return round(sum(health_scores) / len(health_scores))

    def _snapshot_read_model(self, snapshot: ClusterSnapshot) -> ClusterSnapshotRead:
        return ClusterSnapshotRead(
            id=snapshot.id,
            cluster_name=snapshot.cluster.name,
            total_pods=snapshot.total_pods,
            running_pods=snapshot.running_pods,
            pending_pods=snapshot.pending_pods,
            failed_pods=snapshot.failed_pods,
            restart_count=snapshot.restart_count,
            cpu_millicores=snapshot.cpu_millicores,
            memory_mebibytes=snapshot.memory_mebibytes,
            health_score=snapshot.health_score,
            sampled_at=snapshot.sampled_at,
        )

    def _pod_metric_read_model(self, metric: PodMetric) -> PodMetricRead:
        return PodMetricRead(
            id=metric.id,
            namespace=metric.pod.namespace.name,
            pod_name=metric.pod.name,
            cpu_millicores=metric.cpu_millicores,
            memory_mebibytes=metric.memory_mebibytes,
            cpu_limit_millicores=metric.cpu_limit_millicores,
            memory_limit_mebibytes=metric.memory_limit_mebibytes,
            sampled_at=metric.sampled_at,
            created_at=metric.created_at,
            updated_at=metric.updated_at,
        )
