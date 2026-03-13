from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_ai_stack_service
from app.schemas.ai import AIEngineRoomSummaryResponse, AIStackSummaryResponse
from app.services.ai_stack import AIStackService


router = APIRouter(prefix='/api/ai', tags=['ai'])


@router.get('/stack', response_model=AIStackSummaryResponse)
async def get_ai_stack(
    ai_stack_service: AIStackService = Depends(get_ai_stack_service),
) -> dict:
    return ai_stack_service.get_stack_summary()


@router.get('/engine-room', response_model=AIEngineRoomSummaryResponse)
async def get_ai_engine_room(
    ai_stack_service: AIStackService = Depends(get_ai_stack_service),
) -> dict:
    return ai_stack_service.get_engine_room_summary()
