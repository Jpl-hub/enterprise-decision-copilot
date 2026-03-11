from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_warehouse_service
from app.schemas.warehouse import WarehouseOverviewResponse, WarehouseSummaryResponse
from app.services.warehouse import WarehouseService


router = APIRouter(prefix='/api/warehouse', tags=['warehouse'])


@router.get('/summary', response_model=WarehouseSummaryResponse)
async def get_warehouse_summary(
    warehouse_service: WarehouseService = Depends(get_warehouse_service),
) -> dict:
    return warehouse_service.get_summary()


@router.get('/overview', response_model=WarehouseOverviewResponse)
async def get_warehouse_overview(
    limit: int = Query(8, ge=1, le=20),
    warehouse_service: WarehouseService = Depends(get_warehouse_service),
) -> dict:
    return warehouse_service.get_overview(limit=limit)
