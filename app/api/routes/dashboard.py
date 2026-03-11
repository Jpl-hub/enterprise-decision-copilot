from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_analytics_service
from app.services.analytics import AnalyticsService


router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
async def get_dashboard(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> dict:
    return analytics_service.get_dashboard_payload()
