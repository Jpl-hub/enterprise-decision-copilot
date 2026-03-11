from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_audit_service, require_roles
from app.schemas.audit import AuditLogListResponse
from app.services.audit import AuditService


router = APIRouter(prefix='/api/audit', tags=['audit'])


@router.get('/logs', response_model=AuditLogListResponse)
async def get_audit_logs(
    limit: int = Query(30, ge=1, le=200),
    _: dict = Depends(require_roles('admin')),
    audit_service: AuditService = Depends(get_audit_service),
) -> dict:
    items = audit_service.list_recent(limit=limit)
    return {
        'total': len(items),
        'items': items,
    }
