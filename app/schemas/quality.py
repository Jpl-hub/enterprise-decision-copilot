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


class DataQualitySummaryResponse(BaseModel):
    official_report_coverage_ratio: float
    official_report_downloaded_slots: int
    official_report_expected_slots: int
    missing_report_slots: int
    pending_review_count: int
    anomaly_company_count: int
    multimodal_extract_report_count: int = 0
    multimodal_expected_report_count: int = 0
    multimodal_extract_coverage_ratio: float = 0.0
    multimodal_avg_filled_field_count: float = 0.0
    multimodal_backends: list[str] = Field(default_factory=list)
    multimodal_recent_extracts: list[MultimodalExtractItem] = Field(default_factory=list)
    exchange_status: list[ExchangeQualityStatus] = Field(default_factory=list)
    top_anomalies: list[QualityAnomalyItem] = Field(default_factory=list)
    recent_reviews: list[ManualReviewRecord] = Field(default_factory=list)


class ManualReviewSubmitResponse(BaseModel):
    review: ManualReviewRecord
    summary: dict[str, Any] = Field(default_factory=dict)


class AutoReviewSyncResponse(BaseModel):
    created_count: int
    skipped_count: int
    created: list[ManualReviewRecord] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
