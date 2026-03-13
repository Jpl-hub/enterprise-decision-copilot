from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QualityAnomalyItem(BaseModel):
    company_code: str
    company_name: str
    report_year: int
    field_coverage_ratio: float
    critical_fields_missing: list[str] = Field(default_factory=list)
    anomaly_flags: list[str] = Field(default_factory=list)
    anomaly_score: int
    exchange: str | None = None
    financial_source_url: str | None = None


class ExchangeQualityStatus(BaseModel):
    exchange: str
    manifest_exists: bool
    rows: int
    downloaded_rows: int
    file_missing_rows: int
    companies: list[str] = Field(default_factory=list)


class ManualReviewRequest(BaseModel):
    company_code: str = Field(..., min_length=4)
    report_year: int = Field(..., ge=2000, le=2100)
    finding_level: str = Field(..., min_length=1)
    finding_type: str = Field(..., min_length=1)
    note: str = Field(..., min_length=4, max_length=1000)


class ManualReviewRecord(BaseModel):
    company_code: str
    report_year: int
    finding_level: str
    finding_type: str
    note: str
    status: str
    created_at: str


class MultimodalExtractItem(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    company_code: str
    report_year: int
    company_name: str | None = None
    backend: str
    model_id: str | None = None
    source_url: str | None = None
    page_images: list[str] = Field(default_factory=list)
    field_source_count: int
    filled_field_count: int
    notes: list[str] = Field(default_factory=list)


class QualityIssueBreakdown(BaseModel):
    missing_reports: int = 0
    field_gaps: int = 0
    multimodal_missing: int = 0
    multimodal_low_coverage: int = 0


class DataQualitySummaryResponse(BaseModel):
    official_report_coverage_ratio: float
    official_report_downloaded_slots: int
    official_report_expected_slots: int
    missing_report_slots: int
    target_pool_company_count: int = 0
    target_pool_ready: bool = False
    universe_report_downloaded_slots: int = 0
    universe_report_expected_slots: int = 0
    universe_report_coverage_ratio: float = 0.0
    pending_review_count: int
    anomaly_company_count: int
    issue_breakdown: QualityIssueBreakdown = Field(default_factory=QualityIssueBreakdown)
    multimodal_extract_report_count: int = 0
    multimodal_expected_report_count: int = 0
    multimodal_extract_coverage_ratio: float = 0.0
    multimodal_avg_filled_field_count: float = 0.0
    multimodal_backends: list[str] = Field(default_factory=list)
    multimodal_recent_extracts: list[MultimodalExtractItem] = Field(default_factory=list)
    exchange_status: list[ExchangeQualityStatus] = Field(default_factory=list)
    top_anomalies: list[QualityAnomalyItem] = Field(default_factory=list)
    recent_reviews: list[ManualReviewRecord] = Field(default_factory=list)


class DataFoundationHotspotField(BaseModel):
    table: str
    field: str
    null_ratio: float


class DataFoundationDatasetProfile(BaseModel):
    table: str
    rows: int
    columns: int
    duplicate_rows: int
    max_null_ratio: float
    hotspot_fields: list[DataFoundationHotspotField] = Field(default_factory=list)


class DataFoundationLayerProfile(BaseModel):
    layer: str
    table_count: int
    row_count: int


class DataFoundationSummaryResponse(BaseModel):
    warehouse_db: str | None = None
    warehouse_table_count: int = 0
    mart_views: list[str] = Field(default_factory=list)
    csv_artifact_count: int = 0
    parquet_artifact_count: int = 0
    total_warehouse_rows: int = 0
    lake_layers: list[DataFoundationLayerProfile] = Field(default_factory=list)
    dataset_profiles: list[DataFoundationDatasetProfile] = Field(default_factory=list)
    top_null_fields: list[DataFoundationHotspotField] = Field(default_factory=list)
    official_inventory_rows: int = 0
    multimodal_extract_report_count: int = 0


class GovernanceSourceEntry(BaseModel):
    source_type: str
    source_name: str
    domain: str
    entry_url: str
    usage_scope: str
    compliance_note: str
    priority: str


class GovernanceCompanyCoverageItem(BaseModel):
    company_code: str
    company_name: str
    exchange: str
    industry: str | None = None
    annual_years: list[int] = Field(default_factory=list)
    annual_report_count: int = 0
    periodic_report_count: int = 0
    research_report_count: int = 0
    multimodal_extract_count: int = 0
    latest_disclosure: str | None = None
    latest_research_report: str | None = None


class GovernanceFieldQualityItem(BaseModel):
    dataset: str
    field: str
    source_type: str
    extraction_method: str
    null_ratio: float = 0.0
    review_status: str
    usage_scope: str


class GovernanceEvidenceMappingItem(BaseModel):
    module: str
    output_label: str
    primary_sources: list[str] = Field(default_factory=list)
    evidence_fields: list[str] = Field(default_factory=list)
    verification_rule: str


class DataGovernanceSummaryResponse(BaseModel):
    generated_at: str | None = None
    source_catalog: list[GovernanceSourceEntry] = Field(default_factory=list)
    company_coverage: list[GovernanceCompanyCoverageItem] = Field(default_factory=list)
    field_quality: list[GovernanceFieldQualityItem] = Field(default_factory=list)
    evidence_mapping: list[GovernanceEvidenceMappingItem] = Field(default_factory=list)


class PreparationSourceStatus(BaseModel):
    source_key: str
    label: str
    rows: int
    latest: str | None = None
    coverage_note: str | None = None


class PreparationCandidate(BaseModel):
    company_code: str
    company_name: str
    industry_name: str | None = None
    report_count: int = 0
    institution_count: int = 0
    latest_report_date: str | None = None
    priority_score: float = 0.0


class PreparationPromotionExchangeStatus(BaseModel):
    exchange: str
    selected_companies: int = 0
    downloaded_reports: int = 0
    missing_reports: int = 0


class PreparationPromotionCompany(BaseModel):
    company_code: str
    company_name: str
    exchange: str
    industry_name: str | None = None
    priority_score: float = 0.0
    downloaded_reports: int = 0
    downloaded_years: list[int] = Field(default_factory=list)
    missing_years: list[int] = Field(default_factory=list)
    latest_published_at: str | None = None


class DataPreparationSummaryResponse(BaseModel):
    generated_at: str | None = None
    source_count: int = 0
    processed_dataset_count: int = 0
    target_pool_company_count: int = 0
    universe_company_count: int = 0
    annual_years: list[int] = Field(default_factory=list)
    latest_macro_period: str | None = None
    latest_stock_report_date: str | None = None
    latest_industry_report_date: str | None = None
    periodic_report_rows: int = 0
    promotion_candidate_count: int = 0
    selected_candidate_count: int = 0
    promotion_years: list[int] = Field(default_factory=list)
    promoted_report_download_count: int = 0
    promoted_report_missing_count: int = 0
    promoted_ready_company_count: int = 0
    promoted_partial_company_count: int = 0
    multimodal_sft_sample_count: int = 0
    multimodal_extract_count: int = 0
    risk_model_file_count: int = 0
    source_status: list[PreparationSourceStatus] = Field(default_factory=list)
    top_candidates: list[PreparationCandidate] = Field(default_factory=list)
    promoted_exchange_status: list[PreparationPromotionExchangeStatus] = Field(default_factory=list)
    promoted_companies: list[PreparationPromotionCompany] = Field(default_factory=list)
    preparation_notes: list[str] = Field(default_factory=list)


class ManualReviewSubmitResponse(BaseModel):
    review: ManualReviewRecord
    summary: dict[str, Any] = Field(default_factory=dict)


class AutoReviewSyncResponse(BaseModel):
    created_count: int
    skipped_count: int
    created: list[ManualReviewRecord] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class RetrievalEvalCaseResult(BaseModel):
    case_id: str
    scope: str
    query: str
    target_code: str | None = None
    relevant_keywords: list[str] = Field(default_factory=list)
    hit_at_3: bool = False
    hit_at_5: bool = False
    reciprocal_rank: float = 0.0
    ndcg_at_5: float = 0.0
    top_titles: list[str] = Field(default_factory=list)
    matched_titles: list[str] = Field(default_factory=list)


class RetrievalEvaluationSummaryResponse(BaseModel):
    generated_at: str | None = None
    case_count: int = 0
    hit_at_3: float = 0.0
    hit_at_5: float = 0.0
    mrr: float = 0.0
    ndcg_at_5: float = 0.0
    retrieval_mode: str | None = None
    strategy_labels: list[str] = Field(default_factory=list)
    cases: list[RetrievalEvalCaseResult] = Field(default_factory=list)
