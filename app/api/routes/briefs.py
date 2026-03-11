from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_decision_service
from app.schemas.brief import DecisionBriefResponse
from app.services.decision import DecisionService


router = APIRouter(prefix="/api/company", tags=["briefs"])


@router.get("/{company_code}/decision-brief", response_model=DecisionBriefResponse)
async def get_company_decision_brief(
    company_code: str,
    question: str = Query("结合真实数据给出经营决策建议", min_length=2),
    decision_service: DecisionService = Depends(get_decision_service),
) -> dict:
    brief = decision_service.build_company_decision_brief(company_code, question)
    if brief is None:
        raise HTTPException(status_code=404, detail="company not found")
    return brief
