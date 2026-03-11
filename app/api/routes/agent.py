from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_agent_service
from app.schemas.agent import AgentResponse, QueryRequest
from app.services.agent import AgentService


router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/query", response_model=AgentResponse)
async def query_agent(
    payload: QueryRequest,
    agent_service: AgentService = Depends(get_agent_service),
) -> dict:
    return agent_service.answer(payload.question)
