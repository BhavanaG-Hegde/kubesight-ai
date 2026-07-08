from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.analytics import AnalyticsOverviewResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(
    prefix="/analytics",
    dependencies=[Depends(get_current_user)],
)


def get_analytics_service(db: Annotated[Session, Depends(get_db)]) -> AnalyticsService:
    return AnalyticsService(db)


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_analytics_overview(
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    days: int = Query(default=30, ge=1, le=90),
) -> AnalyticsOverviewResponse:
    return service.get_overview(days=days)
