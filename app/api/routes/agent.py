from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_agent_service, get_current_user
from app.schemas.agent import AgentResponse, QueryRequest
from app.services.agent import AgentService


router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/query", response_model=AgentResponse)
async def query_agent(
    payload: QueryRequest,
    current_user: dict = Depends(get_current_user),
    agent_service: AgentService = Depends(get_agent_service),
) -> dict:
    return agent_service.answer(
        payload.question,
        thread_id=payload.thread_id,
        company_code=payload.company_code,
        company_name=payload.company_name,
        user_id=current_user['user_id'],
    )
