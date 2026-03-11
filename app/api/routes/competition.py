from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_competition_report_service
from app.schemas.competition import CompetitionPackageResponse
from app.services.competition_report import CompetitionReportService


router = APIRouter(prefix="/api/company", tags=["competition"])


@router.get("/{company_code}/competition-package", response_model=CompetitionPackageResponse)
async def get_company_competition_package(
    company_code: str,
    question: str = Query("结合真实数据生成企业运营分析答辩稿", min_length=2),
    persist: bool = Query(True, description="Whether to persist markdown and evidence bundle under data/exports."),
    competition_report_service: CompetitionReportService = Depends(get_competition_report_service),
) -> dict:
    package = competition_report_service.build_company_competition_package(company_code, question=question, persist=persist)
    if package is None:
        raise HTTPException(status_code=404, detail="company not found")
    return package
