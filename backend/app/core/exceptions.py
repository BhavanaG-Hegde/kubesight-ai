from __future__ import annotations


class KubeSightError(Exception):
    """Base exception for expected KubeSight AI domain errors."""


class KubernetesClientError(KubeSightError):
    """Raised when the backend cannot communicate with Kubernetes."""


class IncidentDetectionError(KubeSightError):
    """Raised when incident detection cannot complete safely."""


class AIAnalysisError(KubeSightError):
    """Raised when Ollama analysis fails or returns an unusable response."""
