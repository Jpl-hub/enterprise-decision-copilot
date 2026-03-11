from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_industry_universe_service
from app.schemas.universe import UniversePromotionPlanResponse, UniverseSummaryResponse
from app.services.universe import IndustryUniverseService


router = APIRouter(prefix='/api/universe', tags=['universe'])


@router.get('/summary', response_model=UniverseSummaryResponse)
async def get_universe_summary(
    universe_service: IndustryUniverseService = Depends(get_industry_universe_service),
) -> dict:
    return universe_service.get_summary()


@router.get('/promotion-plan', response_model=UniversePromotionPlanResponse)
async def get_universe_promotion_plan(
    limit: int = Query(12, ge=1, le=30),
    per_industry: int = Query(2, ge=1, le=5),
    universe_service: IndustryUniverseService = Depends(get_industry_universe_service),
) -> dict:
    return universe_service.get_promotion_plan(limit=limit, per_industry=per_industry)
