from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReportSection(BaseModel):
    title: str
    content: str


class CompanyReportResponse(BaseModel):
    company_code: str
    company_name: str
    report_year: int
    summary: str
    sections: list[ReportSection] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
