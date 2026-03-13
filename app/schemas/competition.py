from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CompetitionCitation(BaseModel):
    citation_id: str
    source_type: str
    title: str
    source_url: str | None = None
    report_date: str | None = None
    institution: str | None = None
    excerpt: str | None = None


class CompetitionPackageSection(BaseModel):
    title: str
    content: str


class CompetitionPackageResponse(BaseModel):
    company_code: str
    company_name: str
    report_year: int
    question: str
    exported_at: str
    summary: str
    brief_verdict: str | None = None
    risk_level: str | None = None
    citation_count: int
    export_dir: str | None = None
    markdown_path: str | None = None
    evidence_path: str | None = None
    evidence_digest: dict[str, Any] = Field(default_factory=dict)
    sections: list[CompetitionPackageSection] = Field(default_factory=list)
    citations: list[CompetitionCitation] = Field(default_factory=list)
    quality_snapshot: dict[str, Any] = Field(default_factory=dict)
    markdown_content: str
