from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_risk_model_service, get_risk_service
from app.schemas.risk import RiskForecastResponse, RiskModelSummaryResponse
from app.services.risk import RiskService
from app.services.risk_model import RiskModelService


router = APIRouter(tags=["risk"])


@router.get("/api/company/{company_code}/risk-forecast", response_model=RiskForecastResponse)
async def get_company_risk_forecast(
    company_code: str,
    risk_service: RiskService = Depends(get_risk_service),
) -> dict:
    forecast = risk_service.build_company_risk_forecast(company_code)
    if forecast is None:
        raise HTTPException(status_code=404, detail="company not found")
    return forecast


@router.get("/api/risk/model-summary", response_model=RiskModelSummaryResponse)
async def get_risk_model_summary(
    risk_model_service: RiskModelService = Depends(get_risk_model_service),
) -> dict:
    return risk_model_service.get_summary()
