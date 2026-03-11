from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from app.api.dependencies import get_analytics_service
from app.config import settings
from app.services.analytics import AnalyticsService
from app.web.dashboard import build_dashboard_context


router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[2] / "templates")


@router.get("/")
async def dashboard(
    request: Request,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> object:
    payload = analytics_service.get_dashboard_payload()
    context = build_dashboard_context(settings.app_name, payload)
    context["request"] = request
    return templates.TemplateResponse("dashboard.html", context)
