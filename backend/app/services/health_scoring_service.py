from __future__ import annotations

from app.models.enums import HealthStatus, IncidentSeverity
from app.schemas.kubernetes import PodEventRead, PodLogRead, PodRead
from app.schemas.monitoring import (
    HealthSignalRead,
    NamespaceHealthSummaryRead,
    PodHealthAssessmentRead,
)


CRITICAL_CONTAINER_REASONS = {
    "CrashLoopBackOff",
    "OOMKilled",
    "ImagePullBackOff",
    "ErrImagePull",
}

WARNING_CONTAINER_REASONS = {
    "CreateContainerConfigError",
    "CreateContainerError",
    "RunContainerError",
    "ContainerCannotRun",
}

ERROR_LOG_PATTERNS = (" error ", "exception", "fatal", "panic", "traceback")
TIMEOUT_LOG_PATTERNS = ("timeout", "timed out", "deadline exceeded", "context deadline")
DATABASE_LOG_PATTERNS = (
    "connection refused",
    "database connection",
    "could not connect",
    "sqlstate",
    "postgres",
    "mysql",
    "mongodb",
    "redis",
)


class HealthScoringService:
    def assess_pod(
        self,
        pod: PodRead,
        *,
        events: list[PodEventRead] | None = None,
        logs: PodLogRead | None = None,
    ) -> PodHealthAssessmentRead:
        signals: list[HealthSignalRead] = []
        signals.extend(self._phase_signals(pod))
        signals.extend(self._readiness_signals(pod))
        signals.extend(self._restart_signals(pod))
        signals.extend(self._container_signals(pod))
        signals.extend(self._event_signals(events or []))
        signals.extend(self._log_signals(logs))
        signals = self._deduplicate_signals(signals)

        score = max(0, 100 - sum(signal.score_impact for signal in signals))
        return PodHealthAssessmentRead(
            namespace=pod.namespace,
            pod_name=pod.name,
            phase=pod.phase,
            health_status=self._status_for_score(score),
            health_score=score,
            restart_count=pod.restart_count,
            ready_containers=pod.ready_containers,
            total_containers=pod.total_containers,
            signals=signals,
        )

    def summarize_namespace(
        self,
        namespace: str,
        pods: list[PodHealthAssessmentRead],
    ) -> NamespaceHealthSummaryRead:
        total_pods = len(pods)
        healthy_pods = sum(1 for pod in pods if pod.health_status == HealthStatus.HEALTHY)
        warning_pods = sum(1 for pod in pods if pod.health_status == HealthStatus.WARNING)
        critical_pods = sum(1 for pod in pods if pod.health_status == HealthStatus.CRITICAL)
        average_score = int(
            round(sum(pod.health_score for pod in pods) / total_pods)
        ) if total_pods else 100

        return NamespaceHealthSummaryRead(
            namespace=namespace,
            total_pods=total_pods,
            healthy_pods=healthy_pods,
            warning_pods=warning_pods,
            critical_pods=critical_pods,
            average_health_score=average_score,
            pods=pods,
        )

    def _phase_signals(self, pod: PodRead) -> list[HealthSignalRead]:
        if pod.phase == "Running":
            return []
        if pod.phase == "Failed":
            return [
                HealthSignalRead(
                    code="pod_failed",
                    severity=IncidentSeverity.CRITICAL,
                    message="Pod is in Failed phase.",
                    evidence=f"phase={pod.phase}",
                    score_impact=45,
                )
            ]
        if pod.phase == "Pending":
            return [
                HealthSignalRead(
                    code="pod_pending",
                    severity=IncidentSeverity.WARNING,
                    message="Pod is still pending.",
                    evidence=f"phase={pod.phase}",
                    score_impact=15,
                )
            ]
        if pod.phase == "Unknown":
            return [
                HealthSignalRead(
                    code="pod_unknown",
                    severity=IncidentSeverity.WARNING,
                    message="Pod phase is unknown.",
                    evidence=f"phase={pod.phase}",
                    score_impact=25,
                )
            ]
        return []

    def _readiness_signals(self, pod: PodRead) -> list[HealthSignalRead]:
        if pod.total_containers == 0 or pod.ready_containers >= pod.total_containers:
            return []
        return [
            HealthSignalRead(
                code="pod_not_ready",
                severity=IncidentSeverity.WARNING,
                message="Not all pod containers are ready.",
                evidence=f"{pod.ready_containers}/{pod.total_containers} containers ready",
                score_impact=15,
            )
        ]

    def _restart_signals(self, pod: PodRead) -> list[HealthSignalRead]:
        if pod.restart_count >= 10:
            return [
                HealthSignalRead(
                    code="high_restart_count",
                    severity=IncidentSeverity.CRITICAL,
                    message="Pod has a high restart count.",
                    evidence=f"restart_count={pod.restart_count}",
                    score_impact=min(35, pod.restart_count * 4),
                )
            ]
        if pod.restart_count >= 3:
            return [
                HealthSignalRead(
                    code="restart_count_warning",
                    severity=IncidentSeverity.WARNING,
                    message="Pod has restarted several times.",
                    evidence=f"restart_count={pod.restart_count}",
                    score_impact=min(20, pod.restart_count * 3),
                )
            ]
        return []

    def _container_signals(self, pod: PodRead) -> list[HealthSignalRead]:
        signals: list[HealthSignalRead] = []
        for container in pod.containers:
            if container.reason in CRITICAL_CONTAINER_REASONS:
                signals.append(
                    HealthSignalRead(
                        code=self._code_for_reason(container.reason),
                        severity=IncidentSeverity.CRITICAL,
                        message=f"Container {container.name} is {container.reason}.",
                        evidence=f"container={container.name}, state={container.state}",
                        score_impact=35 if container.reason != "ImagePullBackOff" else 30,
                    )
                )
            elif container.reason in WARNING_CONTAINER_REASONS:
                signals.append(
                    HealthSignalRead(
                        code="container_runtime_error",
                        severity=IncidentSeverity.WARNING,
                        message=f"Container {container.name} has a runtime/config error.",
                        evidence=f"reason={container.reason}",
                        score_impact=20,
                    )
                )
        return signals

    def _event_signals(self, events: list[PodEventRead]) -> list[HealthSignalRead]:
        signals: list[HealthSignalRead] = []
        for event in events:
            reason = event.reason or ""
            message = event.message or ""
            combined = f"{reason} {message}"
            if "CrashLoopBackOff" in combined:
                signals.append(
                    HealthSignalRead(
                        code="crash_loop_back_off",
                        severity=IncidentSeverity.CRITICAL,
                        message="Kubernetes reported CrashLoopBackOff.",
                        evidence=message,
                        score_impact=35,
                    )
                )
            elif "OOMKilled" in combined:
                signals.append(
                    HealthSignalRead(
                        code="oom_killed",
                        severity=IncidentSeverity.CRITICAL,
                        message="Kubernetes reported an OOMKilled container.",
                        evidence=message,
                        score_impact=35,
                    )
                )
            elif "ImagePullBackOff" in combined or "ErrImagePull" in combined:
                signals.append(
                    HealthSignalRead(
                        code="image_pull_back_off",
                        severity=IncidentSeverity.CRITICAL,
                        message="Kubernetes cannot pull the container image.",
                        evidence=message,
                        score_impact=30,
                    )
                )
        return self._deduplicate_signals(signals)

    def _log_signals(self, logs: PodLogRead | None) -> list[HealthSignalRead]:
        if logs is None:
            return []

        normalized_lines = [line.lower() for line in logs.lines]
        error_count = sum(
            1
            for line in normalized_lines
            if any(pattern in f" {line} " for pattern in ERROR_LOG_PATTERNS)
        )
        timeout_count = sum(
            1
            for line in normalized_lines
            if any(pattern in line for pattern in TIMEOUT_LOG_PATTERNS)
        )
        database_count = sum(
            1
            for line in normalized_lines
            if any(pattern in line for pattern in DATABASE_LOG_PATTERNS)
        )

        signals: list[HealthSignalRead] = []
        if error_count >= 5:
            signals.append(
                HealthSignalRead(
                    code="error_log_spike",
                    severity=IncidentSeverity.WARNING,
                    message="Recent logs contain repeated errors.",
                    evidence=f"error_lines={error_count}",
                    score_impact=min(20, error_count * 2),
                )
            )
        if timeout_count:
            signals.append(
                HealthSignalRead(
                    code="timeout_errors",
                    severity=IncidentSeverity.WARNING,
                    message="Recent logs contain timeout errors.",
                    evidence=f"timeout_lines={timeout_count}",
                    score_impact=max(10, min(20, timeout_count * 4)),
                )
            )
        if database_count:
            signals.append(
                HealthSignalRead(
                    code="database_connection_failure",
                    severity=IncidentSeverity.CRITICAL,
                    message="Recent logs suggest a database connectivity problem.",
                    evidence=f"database_error_lines={database_count}",
                    score_impact=max(25, min(30, database_count * 8)),
                )
            )
        return signals

    def _status_for_score(self, score: int) -> HealthStatus:
        if score >= 80:
            return HealthStatus.HEALTHY
        if score >= 50:
            return HealthStatus.WARNING
        return HealthStatus.CRITICAL

    def _code_for_reason(self, reason: str | None) -> str:
        if reason == "CrashLoopBackOff":
            return "crash_loop_back_off"
        if reason == "OOMKilled":
            return "oom_killed"
        if reason in {"ImagePullBackOff", "ErrImagePull"}:
            return "image_pull_back_off"
        return "container_issue"

    def _deduplicate_signals(self, signals: list[HealthSignalRead]) -> list[HealthSignalRead]:
        seen: set[str] = set()
        unique_signals: list[HealthSignalRead] = []
        for signal in signals:
            if signal.code in seen:
                continue
            seen.add(signal.code)
            unique_signals.append(signal)
        return unique_signals
