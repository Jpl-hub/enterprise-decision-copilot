from __future__ import annotations

from pydantic import BaseModel, Field


class WarehouseTableItem(BaseModel):
    schema_name: str
    table: str
    rows: int
    parquet_path: str


class WarehouseSummaryResponse(BaseModel):
    warehouse_ready: bool
    warehouse_db: str | None = None
    table_count: int
    latest_company_rows: int
    mart_views: list[str] = Field(default_factory=list)
    tables: list[WarehouseTableItem] = Field(default_factory=list)


class WarehouseCompanyOverviewItem(BaseModel):
    company_code: str
    company_name: str
    report_year: int
    revenue_million: float | None = None
    net_profit_million: float | None = None
    positive_reports: int
    neutral_reports: int
    negative_reports: int
    report_coverage: int
    published_at: str | None = None


class WarehouseIndustryHeatItem(BaseModel):
    industry_name: str
    report_count: int
    positive_count: int
    negative_count: int
    latest_report_date: str | None = None


class WarehouseCompanyResearchHeatItem(BaseModel):
    company_code: str
    company_name: str
    report_count: int
    positive_count: int
    negative_count: int
    latest_report_date: str | None = None


class WarehouseOverviewResponse(WarehouseSummaryResponse):
    company_overview: list[WarehouseCompanyOverviewItem] = Field(default_factory=list)
    industry_heat: list[WarehouseIndustryHeatItem] = Field(default_factory=list)
    company_research_heat: list[WarehouseCompanyResearchHeatItem] = Field(default_factory=list)
