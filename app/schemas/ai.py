from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AIHeadlineMetric(BaseModel):
    label: str
    value: str
    tone: str = 'neutral'


class AIEngineMetricSet(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    sample_count: int | None = None
    roc_auc: float | None = None
    model_type: str | None = None
    trained_at: str | None = None
    feature_count: int | None = None
    coverage_ratio: float | None = None
    avg_filled_field_count: float | None = None
    backends: list[str] = Field(default_factory=list)
    extract_report_count: int | None = None
    expected_report_count: int | None = None
    text_extract_report_count: int | None = None
    sft_sample_count: int | None = None
    artifact_count: int | None = None
    warehouse_table_count: int | None = None
    warehouse_row_count: int | None = None
    mart_view_count: int | None = None
    parquet_artifact_count: int | None = None
    tool_count: int | None = None
    official_coverage_ratio: float | None = None
    pending_review_count: int | None = None
    anomaly_company_count: int | None = None


class AIEngineSummary(BaseModel):
    engine_id: str
    name: str
    category: str
    status: str
    stage_label: str | None = None
    readiness_score: float | None = None
    role: str
    primary_inputs: list[str] = Field(default_factory=list)
    primary_outputs: list[str] = Field(default_factory=list)
    headline_metrics: list[AIHeadlineMetric] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    metrics: AIEngineMetricSet | None = None


class AIPillarSummary(BaseModel):
    pillar_id: str
    name: str
    status: str
    stage_label: str
    readiness_score: float
    summary: str
    headline_metrics: list[AIHeadlineMetric] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class AIStackSummaryResponse(BaseModel):
    generated_at: str
    pillars: list[AIPillarSummary] = Field(default_factory=list)
    engines: list[AIEngineSummary] = Field(default_factory=list)
    priority_actions: list[str] = Field(default_factory=list)
    system_story: list[str] = Field(default_factory=list)
    design_choices: list[str] = Field(default_factory=list)


class AIComputeJob(BaseModel):
    job_id: str
    stage: str
    current_engine: str
    spark_ready: bool = False
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    partition_keys: list[str] = Field(default_factory=list)
    goal: str


class AIComputePipelineSummary(BaseModel):
    current_engine: str
    next_engine: str
    warehouse_db: str | None = None
    job_count: int = 0
    spark_ready_job_count: int = 0
    parquet_artifact_count: int = 0
    mart_views: list[str] = Field(default_factory=list)
    jobs: list[AIComputeJob] = Field(default_factory=list)


class AIModelRegistryItem(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    label: str
    status: str
    stage_label: str
    artifact_path: str | None = None
    sample_count: int = 0
    metric_label: str | None = None
    metric_value: str | None = None
    notes: list[str] = Field(default_factory=list)


class AIEngineRoomSummaryResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    generated_at: str
    compute_pipeline: AIComputePipelineSummary
    model_registry: list[AIModelRegistryItem] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class AIModelRegistryResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    generated_at: str
    registry_ready: bool = False
    model_count: int = 0
    active_count: int = 0
    building_count: int = 0
    items: list[AIModelRegistryItem] = Field(default_factory=list)
    priority_actions: list[str] = Field(default_factory=list)
