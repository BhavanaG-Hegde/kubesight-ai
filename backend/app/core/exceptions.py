from __future__ import annotations


class KubeSightError(Exception):
    """Base exception for expected KubeSight AI domain errors."""


class UserAlreadyExistsError(KubeSightError):
    """Raised when registration attempts to reuse an existing email address."""


class InvalidCredentialsError(KubeSightError):
    """Raised when a login attempt uses an unknown email or invalid password."""


class InactiveUserError(KubeSightError):
    """Raised when an inactive account tries to access the platform."""


class UnauthorizedError(KubeSightError):
    """Raised when a request cannot be authenticated."""


class KubernetesClientError(KubeSightError):
    """Raised when the backend cannot communicate with Kubernetes."""


class IncidentDetectionError(KubeSightError):
    """Raised when incident detection cannot complete safely."""


class AIAnalysisError(KubeSightError):
    """Raised when Ollama analysis fails or returns an unusable response."""
