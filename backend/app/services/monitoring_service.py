from __future__ import annotations

import logging

from app.core.exceptions import KubernetesClientError
from app.schemas.kubernetes import PodEventRead, PodLogRead, PodRead
from app.schemas.monitoring import (
    IncidentDetectionResponse,
    NamespaceHealthSummaryRead,
    PodHealthAssessmentRead,
)
from app.services.health_scoring_service import HealthScoringService
from app.services.incident_detection_service import IncidentDetectionService
from app.services.kubernetes_service import KubernetesService

logger = logging.getLogger(__name__)


class MonitoringService:
    def __init__(
        self,
        kubernetes_service: KubernetesService,
        health_scoring_service: HealthScoringService | None = None,
        incident_detection_service: IncidentDetectionService | None = None,
    ) -> None:
        self.kubernetes = kubernetes_service
        self.health_scoring = health_scoring_service or HealthScoringService()
        self.incident_detection = incident_detection_service or IncidentDetectionService()

    def get_namespace_health(
        self,
        namespace: str,
        *,
        include_logs: bool,
        tail_lines: int,
    ) -> NamespaceHealthSummaryRead:
        pods = self.kubernetes.list_pods(namespace)
        assessments = [
            self._assess_pod(
                pod,
                include_logs=include_logs,
                tail_lines=tail_lines,
            )
            for pod in pods
        ]
        return self.health_scoring.summarize_namespace(namespace, assessments)

    def get_pod_health(
        self,
        namespace: str,
        pod_name: str,
        *,
        include_logs: bool,
        tail_lines: int,
    ) -> PodHealthAssessmentRead:
        pod = self.kubernetes.get_pod(namespace, pod_name)
        return self._assess_pod(
            pod,
            include_logs=include_logs,
            tail_lines=tail_lines,
        )

    def detect_namespace_incidents(
        self,
        namespace: str,
        *,
        include_logs: bool,
        tail_lines: int,
    ) -> IncidentDetectionResponse:
        health = self.get_namespace_health(
            namespace,
            include_logs=include_logs,
            tail_lines=tail_lines,
        )
        incidents = [
            incident
            for pod in health.pods
            for incident in self.incident_detection.detect_from_assessment(pod)
        ]
        return IncidentDetectionResponse(
            namespace=namespace,
            scanned_pods=health.total_pods,
            incidents=incidents,
        )

    def detect_pod_incidents(
        self,
        namespace: str,
        pod_name: str,
        *,
        include_logs: bool,
        tail_lines: int,
    ) -> IncidentDetectionResponse:
        assessment = self.get_pod_health(
            namespace,
            pod_name,
            include_logs=include_logs,
            tail_lines=tail_lines,
        )
        return IncidentDetectionResponse(
            namespace=namespace,
            pod_name=pod_name,
            scanned_pods=1,
            incidents=self.incident_detection.detect_from_assessment(assessment),
        )

    def _assess_pod(
        self,
        pod: PodRead,
        *,
        include_logs: bool,
        tail_lines: int,
    ) -> PodHealthAssessmentRead:
        events = self._safe_events(pod)
        logs = self._safe_logs(pod, tail_lines) if include_logs else None
        return self.health_scoring.assess_pod(pod, events=events, logs=logs)

    def _safe_events(self, pod: PodRead) -> list[PodEventRead]:
        try:
            return self.kubernetes.list_pod_events(pod.namespace, pod.name)
        except KubernetesClientError as exc:
            logger.info(
                "Unable to read events for pod %s/%s: %s",
                pod.namespace,
                pod.name,
                exc,
            )
            return []

    def _safe_logs(self, pod: PodRead, tail_lines: int) -> PodLogRead | None:
        try:
            return self.kubernetes.get_pod_logs(
                pod.namespace,
                pod.name,
                container=None,
                tail_lines=tail_lines,
                previous=False,
                timestamps=True,
            )
        except KubernetesClientError as exc:
            logger.info(
                "Unable to read logs for pod %s/%s: %s",
                pod.namespace,
                pod.name,
                exc,
            )
            return None
