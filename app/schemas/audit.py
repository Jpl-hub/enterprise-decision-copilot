from __future__ import annotations

from pydantic import BaseModel, Field


class AuditLogItem(BaseModel):
    log_id: str
    user_id: str | None = None
    event_type: str
    target_type: str | None = None
    target_id: str | None = None
    detail: dict = Field(default_factory=dict)
    created_at: str


class AuditLogListResponse(BaseModel):
    total: int
    items: list[AuditLogItem] = Field(default_factory=list)
