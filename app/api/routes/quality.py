from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_audit_service, get_current_user, get_quality_service, require_roles
from app.schemas.quality import (
    AutoReviewSyncResponse,
    DataFoundationSummaryResponse,
    DataGovernanceSummaryResponse,
    DataPreparationSummaryResponse,
    DataQualitySummaryResponse,
    ManualReviewRequest,
    ManualReviewSubmitResponse,
)
from app.services.audit import AuditService
from app.services.quality import DataQualityService


router = APIRouter(prefix="/api/quality", tags=["quality"])


@router.get("/summary", response_model=DataQualitySummaryResponse)
async def get_quality_summary(
    quality_service: DataQualityService = Depends(get_quality_service),
) -> dict:
    return quality_service.get_quality_summary()


@router.get("/foundation", response_model=DataFoundationSummaryResponse)
async def get_foundation_summary(
    quality_service: DataQualityService = Depends(get_quality_service),
) -> dict:
    return quality_service.get_foundation_summary()


@router.get("/preparation", response_model=DataPreparationSummaryResponse)
async def get_preparation_summary(
    quality_service: DataQualityService = Depends(get_quality_service),
) -> dict:
    return quality_service.get_preparation_summary()


@router.get("/governance", response_model=DataGovernanceSummaryResponse)
async def get_governance_summary(
    quality_service: DataQualityService = Depends(get_quality_service),
) -> dict:
    return quality_service.get_governance_summary()


@router.post("/reviews", response_model=ManualReviewSubmitResponse)
async def submit_manual_review(
    payload: ManualReviewRequest,
    current_user: dict = Depends(require_roles('admin', 'analyst')),
    quality_service: DataQualityService = Depends(get_quality_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> dict:
    review = quality_service.submit_manual_review(
        company_code=payload.company_code,
        report_year=payload.report_year,
        finding_level=payload.finding_level,
        finding_type=payload.finding_type,
        note=payload.note,
    )
    audit_service.log_event(
        event_type='quality.review.submit',
        user_id=current_user['user_id'],
        target_type='manual_review',
        target_id=f"{payload.company_code}-{payload.report_year}",
        detail={'finding_type': payload.finding_type, 'finding_level': payload.finding_level},
    )
    return {
        "review": review,
        "summary": quality_service.get_quality_summary(),
    }


@router.post("/reviews/auto", response_model=AutoReviewSyncResponse)
async def sync_auto_reviews(
    limit: int = Query(12, ge=1, le=100),
    current_user: dict = Depends(require_roles('admin')),
    quality_service: DataQualityService = Depends(get_quality_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> dict:
    payload = quality_service.sync_auto_review_queue(limit=limit)
    payload["summary"] = quality_service.get_quality_summary()
    audit_service.log_event(
        event_type='quality.review.auto_sync',
        user_id=current_user['user_id'],
        target_type='quality_queue',
        target_id='auto',
        detail={'limit': limit, 'created_count': payload['created_count'], 'skipped_count': payload['skipped_count']},
    )
    return payload
