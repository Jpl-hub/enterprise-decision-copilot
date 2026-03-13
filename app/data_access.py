from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.config import settings
from app.db import get_connection, table_has_rows


TARGET_COLUMNS = ['company_code', 'company_name', 'exchange', 'industry', 'segment']
FINANCIAL_COLUMNS = [
    'company_code',
    'company_name',
    'report_year',
    'revenue_million',
    'net_profit_million',
    'gross_margin_pct',
    'net_margin_pct',
    'rd_ratio_pct',
    'debt_ratio_pct',
    'current_ratio',
    'cash_to_short_debt',
    'inventory_turnover',
    'receivable_turnover',
    'operating_cashflow_million',
    'roe_pct',
    'source_url',
    'published_at',
]
REPORT_COLUMNS = [
    'company_code',
    'company_name',
    'report_date',
    'title',
    'analyst_view',
    'institution',
    'sentiment',
    'content',
    'source_url',
]
INDUSTRY_REPORT_COLUMNS = [
    'industry_code',
    'industry_name',
    'report_date',
    'title',
    'institution',
    'sentiment',
    'content',
    'source_url',
]
INDUSTRY_UNIVERSE_COLUMNS = [
    'company_code',
    'company_name',
    'exchange',
    'market',
    'industry_code',
    'industry_name',
    'report_count',
    'institution_count',
    'positive_count',
    'neutral_count',
    'negative_count',
    'latest_report_date',
    'earliest_report_date',
    'in_target_pool',
    'latest_report_title',
    'latest_source_url',
]
MACRO_COLUMNS = ['period', 'indicator_name', 'indicator_value', 'unit', 'source_url']
OFFICIAL_PERIODIC_SNAPSHOT_COLUMNS = [
    'exchange',
    'company_code',
    'company_name',
    'period_type',
    'period_label',
    'report_year',
    'title',
    'published_at',
    'source_url',
]
MULTIMODAL_EXTRACT_COLUMNS = [
    'company_code',
    'company_name',
    'report_year',
    'source_url',
    'published_at',
    'backend',
    'model_id',
    'page_images',
    'field_sources',
    'notes',
]


def _read_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=columns)


def _read_table_if_available(table_name: str, columns: list[str]) -> pd.DataFrame:
    if table_has_rows(table_name):
        with get_connection() as conn:
            query = f"SELECT {', '.join(columns)} FROM {table_name}"
            return pd.read_sql_query(query, conn)
    return pd.DataFrame(columns=columns)


def resolve_targets_csv_path() -> Path:
    if settings.target_pool_path.strip():
        return Path(settings.target_pool_path.strip())
    if settings.target_pool_mode.strip().lower() == 'expanded':
        expanded = settings.data_dir / 'targets_expanded.csv'
        if expanded.exists():
            return expanded
    return settings.data_dir / 'targets.csv'


def load_targets() -> pd.DataFrame:
    frame = _read_table_if_available('companies', TARGET_COLUMNS)
    if frame.empty:
        frame = _read_csv(resolve_targets_csv_path(), TARGET_COLUMNS)
    if not frame.empty:
        frame = frame[TARGET_COLUMNS].copy()
        frame['company_code'] = frame['company_code'].astype(str)
    return frame


def load_financial_features() -> pd.DataFrame:
    frame = _read_table_if_available('financial_features', FINANCIAL_COLUMNS)
    if frame.empty:
        frame = _read_csv(settings.processed_dir / 'financial_features.csv', FINANCIAL_COLUMNS)
    if not frame.empty:
        frame['report_year'] = frame['report_year'].astype(int)
    return frame


def load_research_reports() -> pd.DataFrame:
    frame = _read_table_if_available('research_reports', REPORT_COLUMNS)
    if not frame.empty:
        return frame[REPORT_COLUMNS]
    return _read_csv(settings.processed_dir / 'research_reports.csv', REPORT_COLUMNS)


def load_industry_reports() -> pd.DataFrame:
    frame = _read_table_if_available('industry_reports', INDUSTRY_REPORT_COLUMNS)
    if not frame.empty:
        return frame[INDUSTRY_REPORT_COLUMNS]
    return _read_csv(settings.processed_dir / 'industry_reports.csv', INDUSTRY_REPORT_COLUMNS)


def load_industry_company_universe() -> pd.DataFrame:
    frame = _read_table_if_available('industry_company_universe', INDUSTRY_UNIVERSE_COLUMNS)
    if not frame.empty:
        return frame[INDUSTRY_UNIVERSE_COLUMNS]
    return _read_csv(settings.processed_dir / 'industry_company_universe.csv', INDUSTRY_UNIVERSE_COLUMNS)


def load_macro_indicators() -> pd.DataFrame:
    frame = _read_table_if_available('macro_indicators', MACRO_COLUMNS)
    if not frame.empty:
        return frame[MACRO_COLUMNS]
    return _read_csv(settings.processed_dir / 'macro_indicators.csv', MACRO_COLUMNS)


def load_official_periodic_snapshots() -> pd.DataFrame:
    frame = _read_csv(settings.processed_dir / 'official_periodic_snapshots.csv', OFFICIAL_PERIODIC_SNAPSHOT_COLUMNS)
    if not frame.empty and 'report_year' in frame.columns:
        frame['report_year'] = pd.to_numeric(frame['report_year'], errors='coerce').astype('Int64')
    return frame


def load_multimodal_extracts() -> pd.DataFrame:
    extract_dir = settings.cache_dir / 'official_extract_multimodal'
    if not extract_dir.exists():
        return pd.DataFrame(columns=MULTIMODAL_EXTRACT_COLUMNS)

    records: list[dict] = []
    for path in sorted(extract_dir.glob('*.json')):
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            continue
        company_code = str(payload.get('company_code') or '').strip()
        report_year = pd.to_numeric(payload.get('report_year'), errors='coerce')
        if not company_code or pd.isna(report_year):
            continue
        normalized = dict(payload)
        normalized['company_code'] = company_code
        normalized['report_year'] = int(report_year)
        normalized['company_name'] = str(payload.get('company_name') or '').strip() or None
        normalized['source_url'] = str(payload.get('source_url') or '').strip() or None
        normalized['published_at'] = str(payload.get('published_at') or '').strip() or None
        normalized['backend'] = str(payload.get('backend') or '').strip() or None
        normalized['model_id'] = str(payload.get('model_id') or '').strip() or None
        normalized['page_images'] = list(payload.get('page_images') or [])
        normalized['field_sources'] = payload.get('field_sources') or {}
        notes = payload.get('notes') or []
        normalized['notes'] = notes if isinstance(notes, list) else [str(notes)]
        records.append(normalized)

    if not records:
        return pd.DataFrame(columns=MULTIMODAL_EXTRACT_COLUMNS)

    frame = pd.DataFrame(records)
    frame['company_code'] = frame['company_code'].astype(str)
    frame['report_year'] = pd.to_numeric(frame['report_year'], errors='coerce').astype('Int64')
    return frame
