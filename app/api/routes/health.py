from __future__ import annotations

from fastapi import APIRouter

from app.config import settings


router = APIRouter(tags=["health"])


@router.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok", "app": settings.app_name}
