from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RiskBaseModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())


class RiskModelMetricSummary(RiskBaseModel):
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    roc_auc: float | None = None
    positive_rate: float | None = None


class RiskModelSummaryResponse(RiskBaseModel):
    model_ready: bool
    model_type: str | None = None
    trained_at: str | None = None
    sample_count: int = 0
    positive_samples: int = 0
    metrics: RiskModelMetricSummary = Field(default_factory=RiskModelMetricSummary)
    feature_columns: list[str] = Field(default_factory=list)


class RiskContributionItem(RiskBaseModel):
    feature: str
    contribution: float
    direction: str


class RiskModelPredictionResponse(RiskBaseModel):
    company_code: str
    report_year: int
    high_risk_probability: float
    predicted_score: float
    top_contributions: list[RiskContributionItem] = Field(default_factory=list)
    model_summary: RiskModelSummaryResponse


class RiskForecastResponse(RiskBaseModel):
    company_code: str
    company_name: str
    risk_score: float
    risk_level: str
    summary: str
    drivers: list[str] = Field(default_factory=list)
    monitoring_items: list[str] = Field(default_factory=list)
    heuristic_score: float
    model_prediction: RiskModelPredictionResponse | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
