from __future__ import annotations

from pydantic import BaseModel, Field


class UniverseExchangeItem(BaseModel):
    exchange: str
    company_count: int
    report_count: int


class UniverseIndustryItem(BaseModel):
    industry_code: str | None = None
    industry_name: str
    company_count: int
    report_count: int


class UniverseCompanyItem(BaseModel):
    company_code: str
    company_name: str
    exchange: str
    market: str | None = None
    industry_code: str | None = None
    industry_name: str
    report_count: int
    institution_count: int
    positive_count: int
    neutral_count: int
    negative_count: int
    latest_report_date: str | None = None
    earliest_report_date: str | None = None
    in_target_pool: bool = False
    latest_report_title: str | None = None
    latest_source_url: str | None = None


class UniverseCandidateRecommendationItem(UniverseCompanyItem):
    candidate_priority_score: float
    recommendation_reasons: list[str] = Field(default_factory=list)


class UniversePromotionIndustryItem(BaseModel):
    industry_name: str
    selected_count: int


class UniverseFinancialReadinessItem(BaseModel):
    company_code: str
    company_name: str
    exchange: str
    industry_name: str
    candidate_priority_score: float
    feature_year_count: int
    report_years: list[str] = Field(default_factory=list)
    latest_report_year: int | None = None
    readiness_status: str
    year_coverage_ratio: float


class UniverseFinancialReadinessSummary(BaseModel):
    promotion_candidate_count: int = 0
    official_feature_company_count: int = 0
    official_feature_row_count: int = 0
    ready_candidate_count: int = 0
    partial_candidate_count: int = 0
    pending_candidate_count: int = 0
    average_year_coverage_ratio: float = 0.0
    candidates: list[UniverseFinancialReadinessItem] = Field(default_factory=list)


class UniversePromotionPlanResponse(BaseModel):
    plan_ready: bool
    generated_at: str | None = None
    limit: int
    per_industry_limit: int
    candidate_count: int
    selected_count: int
    industries: list[UniversePromotionIndustryItem] = Field(default_factory=list)
    candidates: list[UniverseCandidateRecommendationItem] = Field(default_factory=list)


class UniverseSummaryResponse(BaseModel):
    universe_ready: bool
    generated_at: str | None = None
    company_count: int
    industry_count: int
    total_report_count: int
    target_overlap_count: int
    exchanges: list[UniverseExchangeItem] = Field(default_factory=list)
    industries: list[UniverseIndustryItem] = Field(default_factory=list)
    top_companies: list[UniverseCompanyItem] = Field(default_factory=list)
    recommended_candidates: list[UniverseCandidateRecommendationItem] = Field(default_factory=list)
    industry_code_map: dict[str, str] = Field(default_factory=dict)
    financial_readiness: UniverseFinancialReadinessSummary = Field(default_factory=UniverseFinancialReadinessSummary)
