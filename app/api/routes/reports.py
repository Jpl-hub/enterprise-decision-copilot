from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_analytics_service
from app.schemas.compare import CompanyCompareResponse
from app.schemas.report import CompanyReportResponse
from app.services.analytics import AnalyticsService


router = APIRouter(prefix="/api/company", tags=["reports"])


@router.get("/{company_code}/report", response_model=CompanyReportResponse)
async def get_company_report(
    company_code: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> dict:
    report = analytics_service.get_company_report(company_code)
    if report is None:
        raise HTTPException(status_code=404, detail="company not found")
    return report


@router.get("/compare", response_model=CompanyCompareResponse)
async def compare_companies(
    company_codes: list[str] = Query(..., description="Repeat company_codes to compare multiple companies."),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
) -> dict:
    normalized_codes = list(dict.fromkeys(code.strip() for code in company_codes if code.strip()))
    if len(normalized_codes) < 2:
        raise HTTPException(status_code=400, detail="at least two company codes are required")

    comparison = analytics_service.compare_companies(normalized_codes)
    if comparison is None:
        raise HTTPException(status_code=404, detail="not enough companies found")
    return comparison
