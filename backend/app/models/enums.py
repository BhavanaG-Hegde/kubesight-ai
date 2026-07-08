from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    VIEWER = "viewer"


class ClusterStatus(StrEnum):
    CONNECTED = "connected"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"


class PodPhase(StrEnum):
    RUNNING = "Running"
    PENDING = "Pending"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


class HealthStatus(StrEnum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class LogSeverity(StrEnum):
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class IncidentSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class IncidentStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class IncidentType(StrEnum):
    CRASH_LOOP_BACK_OFF = "crash_loop_back_off"
    OOM_KILLED = "oom_killed"
    IMAGE_PULL_BACK_OFF = "image_pull_back_off"
    HIGH_RESTART_COUNT = "high_restart_count"
    HIGH_CPU = "high_cpu"
    HIGH_MEMORY = "high_memory"
    TIMEOUT_ERRORS = "timeout_errors"
    DATABASE_CONNECTION_FAILURE = "database_connection_failure"
    ERROR_LOG_SPIKE = "error_log_spike"
    POD_NOT_READY = "pod_not_ready"


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_cls]
