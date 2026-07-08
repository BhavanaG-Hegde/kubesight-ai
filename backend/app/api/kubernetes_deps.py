from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException, status

from app.core.exceptions import KubernetesClientError, KubernetesResourceNotFoundError
from app.services.kubernetes_service import KubernetesService


def get_kubernetes_service() -> KubernetesService:
    try:
        return KubernetesService()
    except KubernetesClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


def raise_kubernetes_http_error(exc: KubernetesClientError) -> NoReturn:
    if isinstance(exc, KubernetesResourceNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=str(exc),
    ) from exc
