from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai,
    analytics,
    auth,
    health,
    incidents,
    kubernetes,
    metrics,
    monitoring,
)

api_router = APIRouter()
api_router.include_router(ai.router, tags=["AI Assistant"])
api_router.include_router(analytics.router, tags=["Analytics"])
api_router.include_router(auth.router, tags=["Auth"])
api_router.include_router(health.router, tags=["System"])
api_router.include_router(kubernetes.router, tags=["Kubernetes"])
api_router.include_router(metrics.router, tags=["Metrics"])
api_router.include_router(monitoring.router, tags=["Monitoring"])
api_router.include_router(incidents.router, tags=["Incidents"])
