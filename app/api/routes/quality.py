from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_quality_service
from app.schemas.quality import (
    AutoReviewSyncResponse,
    DataQualitySummaryResponse,
    ManualReviewRequest,
    ManualReviewSubmitResponse,
)
from app.services.quality import DataQualityService


router = APIRouter(prefix="/api/quality", tags=["quality"])


@router.get("/summary", response_model=DataQualitySummaryResponse)
async def get_quality_summary(
    quality_service: DataQualityService = Depends(get_quality_service),
) -> dict:
    return quality_service.get_quality_summary()


@router.post("/reviews", response_model=ManualReviewSubmitResponse)
async def submit_manual_review(
    payload: ManualReviewRequest,
    quality_service: DataQualityService = Depends(get_quality_service),
) -> dict:
    review = quality_service.submit_manual_review(
        company_code=payload.company_code,
        report_year=payload.report_year,
        finding_level=payload.finding_level,
        finding_type=payload.finding_type,
        note=payload.note,
    )
    return {
        "review": review,
        "summary": quality_service.get_quality_summary(),
    }


@router.post("/reviews/auto", response_model=AutoReviewSyncResponse)
async def sync_auto_reviews(
    limit: int = Query(12, ge=1, le=100),
    quality_service: DataQualityService = Depends(get_quality_service),
) -> dict:
    payload = quality_service.sync_auto_review_queue(limit=limit)
    payload["summary"] = quality_service.get_quality_summary()
    return payload
