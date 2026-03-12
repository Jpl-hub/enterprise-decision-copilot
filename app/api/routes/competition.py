from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_audit_service, get_competition_report_service, require_roles
from app.schemas.competition import CompetitionPackageResponse
from app.services.audit import AuditService
from app.services.competition_report import CompetitionReportService


router = APIRouter(prefix="/api/company", tags=["competition"])


@router.get("/{company_code}/competition-package", response_model=CompetitionPackageResponse)
async def get_company_competition_package(
    company_code: str,
    question: str = Query("结合真实数据生成企业运营分析材料", min_length=2),
    persist: bool = Query(True, description="Whether to persist markdown and evidence bundle under data/exports."),
    current_user: dict = Depends(require_roles('admin', 'analyst')),
    competition_report_service: CompetitionReportService = Depends(get_competition_report_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> dict:
    package = competition_report_service.build_company_competition_package(company_code, question=question, persist=persist)
    if package is None:
        raise HTTPException(status_code=404, detail="company not found")
    audit_service.log_event(
        event_type='competition.package.export',
        user_id=current_user['user_id'],
        target_type='company',
        target_id=company_code,
        detail={'question': question, 'persist': persist, 'citation_count': package['citation_count']},
    )
    return package
