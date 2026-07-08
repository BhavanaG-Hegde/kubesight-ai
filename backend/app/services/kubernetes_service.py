from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from typing import Any

from kubernetes import client, config
from kubernetes.client import ApiException
from kubernetes.config.config_exception import ConfigException

from app.core.config import Settings, get_settings
from app.core.exceptions import KubernetesClientError, KubernetesResourceNotFoundError
from app.schemas.kubernetes import (
    ClusterSummaryRead,
    ContainerStatusRead,
    DeploymentRead,
    NamespaceRead,
    PodEventRead,
    PodLogRead,
    PodRead,
    ServicePortRead,
    ServiceRead,
)
from app.schemas.metrics import PodResourceMetricRead

logger = logging.getLogger(__name__)


class KubernetesService:
    _configured: bool = False

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._ensure_configured()
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.custom_objects = client.CustomObjectsApi()

    def get_cluster_summary(self) -> ClusterSummaryRead:
        pods = self.list_all_pods()
        return self._build_cluster_summary(pods)

    def list_all_pods(self) -> list[PodRead]:
        pods = self._request(lambda: self.core_v1.list_pod_for_all_namespaces().items)
        return [self._map_pod(pod) for pod in pods]

    def list_pod_resource_metrics(self) -> list[PodResourceMetricRead]:
        response = self._request(
            lambda: self.custom_objects.list_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="pods",
            )
        )
        return [self._map_pod_metric(item) for item in response.get("items", [])]

    def list_namespaces(self) -> list[NamespaceRead]:
        namespaces = self._request(lambda: self.core_v1.list_namespace().items)
        return [
            NamespaceRead(
                name=namespace.metadata.name,
                status=namespace.status.phase or "Unknown",
                labels=self._metadata_map(namespace.metadata.labels),
            )
            for namespace in namespaces
        ]

    def list_deployments(self, namespace: str) -> list[DeploymentRead]:
        deployments = self._request(
            lambda: self.apps_v1.list_namespaced_deployment(namespace=namespace).items
        )
        return [self._map_deployment(deployment) for deployment in deployments]

    def list_services(self, namespace: str) -> list[ServiceRead]:
        services = self._request(lambda: self.core_v1.list_namespaced_service(namespace).items)
        return [self._map_service(service) for service in services]

    def list_pods(self, namespace: str) -> list[PodRead]:
        pods = self._request(lambda: self.core_v1.list_namespaced_pod(namespace).items)
        return [self._map_pod(pod) for pod in pods]

    def get_pod(self, namespace: str, pod_name: str) -> PodRead:
        pod = self._request(lambda: self.core_v1.read_namespaced_pod(pod_name, namespace))
        return self._map_pod(pod)

    def list_pod_events(self, namespace: str, pod_name: str) -> list[PodEventRead]:
        field_selector = f"involvedObject.kind=Pod,involvedObject.name={pod_name}"
        events = self._request(
            lambda: self.core_v1.list_namespaced_event(
                namespace=namespace,
                field_selector=field_selector,
            ).items
        )
        return [self._map_event(event) for event in events]

    def get_pod_logs(
        self,
        namespace: str,
        pod_name: str,
        *,
        container: str | None,
        tail_lines: int,
        previous: bool,
        timestamps: bool,
    ) -> PodLogRead:
        log_text = self._request(
            lambda: self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines,
                previous=previous,
                timestamps=timestamps,
            )
        )
        return PodLogRead(
            namespace=namespace,
            pod_name=pod_name,
            container=container,
            tail_lines=tail_lines,
            lines=log_text.splitlines(),
        )

    def stream_pod_logs(
        self,
        namespace: str,
        pod_name: str,
        *,
        container: str | None,
        tail_lines: int,
        previous: bool,
        timestamps: bool,
    ) -> Iterator[str]:
        response = self._request(
            lambda: self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                follow=True,
                tail_lines=tail_lines,
                previous=previous,
                timestamps=timestamps,
                _preload_content=False,
            )
        )
        buffer = ""
        try:
            for chunk in response.stream(amt=8192, decode_content=True):
                if not chunk:
                    continue
                buffer += self._decode_log_chunk(chunk)
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    yield line.rstrip("\r")
            if buffer:
                yield buffer.rstrip("\r")
        except ApiException as exc:
            logger.warning(
                "Kubernetes log stream failed: status=%s reason=%s",
                exc.status,
                exc.reason,
            )
            raise KubernetesClientError(
                exc.reason or "Kubernetes log stream failed."
            ) from exc
        except Exception as exc:
            logger.warning("Kubernetes log stream interrupted: %s", exc)
            raise KubernetesClientError("Kubernetes log stream interrupted.") from exc
        finally:
            if hasattr(response, "close"):
                response.close()
            if hasattr(response, "release_conn"):
                response.release_conn()

    def _ensure_configured(self) -> None:
        if KubernetesService._configured:
            return

        try:
            if self.settings.kubeconfig_path or self.settings.kubernetes_context:
                config.load_kube_config(
                    config_file=self.settings.kubeconfig_path,
                    context=self.settings.kubernetes_context,
                )
            else:
                self._load_default_config()
            KubernetesService._configured = True
        except ConfigException as exc:
            raise KubernetesClientError(
                "Unable to load Kubernetes configuration. "
                "Set KUBECONFIG_PATH or run inside a cluster."
            ) from exc

    def _load_default_config(self) -> None:
        try:
            config.load_incluster_config()
        except ConfigException:
            config.load_kube_config()

    def _request(self, operation: Callable[[], Any]) -> Any:
        try:
            return operation()
        except ApiException as exc:
            if exc.status == 404:
                raise KubernetesResourceNotFoundError(
                    exc.reason or "Kubernetes resource not found."
                ) from exc
            logger.warning(
                "Kubernetes API request failed: status=%s reason=%s",
                exc.status,
                exc.reason,
            )
            raise KubernetesClientError(exc.reason or "Kubernetes API request failed.") from exc

    def _build_cluster_summary(self, pods: list[PodRead]) -> ClusterSummaryRead:
        total_pods = len(pods)
        running_pods = sum(1 for pod in pods if pod.phase == "Running")
        pending_pods = sum(1 for pod in pods if pod.phase == "Pending")
        failed_pods = sum(1 for pod in pods if pod.phase == "Failed")
        restart_count = sum(pod.restart_count for pod in pods)
        return ClusterSummaryRead(
            total_pods=total_pods,
            running_pods=running_pods,
            pending_pods=pending_pods,
            failed_pods=failed_pods,
            restart_count=restart_count,
        )

    def _map_deployment(self, deployment: Any) -> DeploymentRead:
        status = deployment.status
        spec = deployment.spec
        metadata = deployment.metadata
        return DeploymentRead(
            name=metadata.name,
            namespace=metadata.namespace,
            desired_replicas=spec.replicas or 0,
            ready_replicas=status.ready_replicas or 0,
            available_replicas=status.available_replicas or 0,
            updated_replicas=status.updated_replicas or 0,
            labels=self._metadata_map(metadata.labels),
            selector=spec.selector.match_labels or {},
        )

    def _map_service(self, service: Any) -> ServiceRead:
        metadata = service.metadata
        spec = service.spec
        return ServiceRead(
            name=metadata.name,
            namespace=metadata.namespace,
            service_type=spec.type,
            cluster_ip=spec.cluster_ip,
            ports=[
                ServicePortRead(
                    name=port.name,
                    protocol=port.protocol,
                    port=port.port,
                    target_port=str(port.target_port) if port.target_port is not None else None,
                    node_port=port.node_port,
                )
                for port in spec.ports or []
            ],
            labels=self._metadata_map(metadata.labels),
        )

    def _map_pod(self, pod: Any) -> PodRead:
        metadata = pod.metadata
        status = pod.status
        container_statuses = status.container_statuses or []
        containers = [self._map_container_status(container) for container in container_statuses]
        return PodRead(
            name=metadata.name,
            namespace=metadata.namespace,
            phase=status.phase or "Unknown",
            node_name=pod.spec.node_name,
            pod_ip=status.pod_ip,
            host_ip=status.host_ip,
            restart_count=self._restart_count(container_statuses),
            ready_containers=sum(1 for container in container_statuses if container.ready),
            total_containers=len(pod.spec.containers or []),
            containers=containers,
            labels=self._metadata_map(metadata.labels),
            annotations=self._metadata_map(metadata.annotations),
            created_at=metadata.creation_timestamp,
        )

    def _map_pod_metric(self, item: dict[str, Any]) -> PodResourceMetricRead:
        metadata = item.get("metadata", {})
        containers = item.get("containers", [])
        cpu_millicores = 0
        memory_mebibytes = 0
        for container in containers:
            usage = container.get("usage", {})
            cpu_millicores += self._cpu_to_millicores(str(usage.get("cpu", "0")))
            memory_mebibytes += self._memory_to_mebibytes(str(usage.get("memory", "0")))

        return PodResourceMetricRead(
            namespace=str(metadata.get("namespace", "default")),
            pod_name=str(metadata.get("name", "unknown")),
            cpu_millicores=cpu_millicores,
            memory_mebibytes=memory_mebibytes,
        )

    def _map_container_status(self, container: Any) -> ContainerStatusRead:
        state, reason = self._container_state(container.state)
        return ContainerStatusRead(
            name=container.name,
            ready=container.ready,
            restart_count=container.restart_count,
            state=state,
            reason=reason,
        )

    def _container_state(self, state: Any) -> tuple[str, str | None]:
        if state is None:
            return "unknown", None
        if state.waiting is not None:
            return "waiting", state.waiting.reason
        if state.running is not None:
            return "running", None
        if state.terminated is not None:
            return "terminated", state.terminated.reason
        return "unknown", None

    def _map_event(self, event: Any) -> PodEventRead:
        return PodEventRead(
            event_type=event.type or "Unknown",
            reason=event.reason or "Unknown",
            message=event.message or "",
            source_component=event.source.component if event.source else None,
            count=event.count or 1,
            first_seen_at=event.first_timestamp,
            last_seen_at=event.last_timestamp or event.event_time,
        )

    def _restart_count(self, container_statuses: list[Any]) -> int:
        return sum(container.restart_count or 0 for container in container_statuses)

    def _metadata_map(self, value: dict[str, str] | None) -> dict[str, str]:
        return dict(value or {})

    def _decode_log_chunk(self, chunk: bytes | str) -> str:
        if isinstance(chunk, bytes):
            return chunk.decode("utf-8", errors="replace")
        return chunk

    def _cpu_to_millicores(self, value: str) -> int:
        if value.endswith("n"):
            return round(int(value[:-1]) / 1_000_000)
        if value.endswith("u"):
            return round(int(value[:-1]) / 1_000)
        if value.endswith("m"):
            return int(value[:-1])
        return round(float(value) * 1000)

    def _memory_to_mebibytes(self, value: str) -> int:
        units = {
            "Ki": 1 / 1024,
            "Mi": 1,
            "Gi": 1024,
            "Ti": 1024 * 1024,
            "K": 1000 / 1024 / 1024,
            "M": 1000 * 1000 / 1024 / 1024,
            "G": 1000 * 1000 * 1000 / 1024 / 1024,
        }
        for suffix, multiplier in units.items():
            if value.endswith(suffix):
                return round(float(value[: -len(suffix)]) * multiplier)
        return round(float(value) / 1024 / 1024)
