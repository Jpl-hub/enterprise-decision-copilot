from __future__ import annotations

from pydantic import BaseModel, Field


class AIEngineMetricSet(BaseModel):
    sample_count: int | None = None
    roc_auc: float | None = None
    model_type: str | None = None
    coverage_ratio: float | None = None
    avg_filled_field_count: float | None = None
    backends: list[str] = Field(default_factory=list)
    official_coverage_ratio: float | None = None
    pending_review_count: int | None = None
    anomaly_company_count: int | None = None


class AIEngineSummary(BaseModel):
    engine_id: str
    name: str
    category: str
    status: str
    role: str
    primary_inputs: list[str] = Field(default_factory=list)
    primary_outputs: list[str] = Field(default_factory=list)
    metrics: AIEngineMetricSet | None = None


class AIStackSummaryResponse(BaseModel):
    engines: list[AIEngineSummary] = Field(default_factory=list)
    design_choices: list[str] = Field(default_factory=list)
