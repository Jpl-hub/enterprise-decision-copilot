from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CompanyComparisonRow(BaseModel):
    company_code: str
    company_name: str
    total_score: float
    risk_level: str
    revenue_million: float
    net_profit_million: float
    net_margin_pct: float | None = None
    roe_pct: float | None = None
    rd_ratio_pct: float | None = None
    revenue_cagr_pct: float | None = None
    profit_cagr_pct: float | None = None
    research_report_count: int
    industry_report_count: int


class ComparisonDimensionValue(BaseModel):
    company_code: str
    company_name: str
    value: float


class ComparisonDimension(BaseModel):
    dimension: str
    winner_company_code: str
    winner_company_name: str
    conclusion: str
    values: list[ComparisonDimensionValue] = Field(default_factory=list)


class CompanyCompareResponse(BaseModel):
    report_year: int
    winner_company_code: str
    winner_company_name: str
    summary: str
    highlights: list[str] = Field(default_factory=list)
    comparison_rows: list[CompanyComparisonRow] = Field(default_factory=list)
    dimensions: list[ComparisonDimension] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
