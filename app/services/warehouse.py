from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb

from app.config import settings


class WarehouseService:
    def __init__(
        self,
        warehouse_summary_path: Path | None = None,
        warehouse_db_path: Path | None = None,
    ) -> None:
        self.warehouse_summary_path = warehouse_summary_path or (settings.data_dir / 'quality' / 'warehouse_summary.json')
        self.warehouse_db_path = warehouse_db_path

    def _read_summary_payload(self) -> dict:
        if not self.warehouse_summary_path.exists():
            return {}
        return json.loads(self.warehouse_summary_path.read_text(encoding='utf-8'))

    def _resolve_db_path(self, payload: dict) -> Path | None:
        if self.warehouse_db_path is not None:
            return self.warehouse_db_path
        db_path = payload.get('warehouse_db')
        if not db_path:
            return None
        return Path(db_path)

    def _connect(self, db_path: Path):
        return duckdb.connect(str(db_path), read_only=True)

    def _normalize_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized_rows: list[dict[str, Any]] = []
        for row in rows:
            normalized: dict[str, Any] = {}
            for key, value in row.items():
                if key.endswith('_code') and value is not None:
                    try:
                        normalized[key] = str(int(value))
                    except Exception:
                        normalized[key] = str(value)
                elif key in {'report_year', 'positive_reports', 'neutral_reports', 'negative_reports', 'report_coverage', 'report_count', 'positive_count', 'negative_count'} and value is not None:
                    normalized[key] = int(value)
                else:
                    normalized[key] = value
            normalized_rows.append(normalized)
        return normalized_rows

    def _fetch_rows(self, db_path: Path, sql: str, limit: int) -> list[dict[str, Any]]:
        connection = self._connect(db_path)
        try:
            rows = connection.execute(sql, [limit]).fetchdf().to_dict('records')
            return self._normalize_rows(rows)
        finally:
            connection.close()

    def get_summary(self) -> dict:
        payload = self._read_summary_payload()
        db_path = self._resolve_db_path(payload)
        if not payload or db_path is None or not db_path.exists():
            return {
                'warehouse_ready': False,
                'warehouse_db': None,
                'table_count': 0,
                'latest_company_rows': 0,
                'mart_views': [],
                'tables': [],
            }
        return {
            'warehouse_ready': True,
            'warehouse_db': str(db_path),
            'table_count': int(payload.get('table_count') or 0),
            'latest_company_rows': int(payload.get('latest_company_rows') or 0),
            'mart_views': payload.get('mart_views', []),
            'tables': payload.get('tables', []),
        }

    def get_overview(self, limit: int = 8) -> dict:
        summary = self.get_summary()
        if not summary.get('warehouse_ready'):
            return {
                **summary,
                'company_overview': [],
                'industry_heat': [],
                'company_research_heat': [],
            }

        db_path = Path(summary['warehouse_db'])
        company_overview = self._fetch_rows(
            db_path,
            '''
            SELECT company_code, company_name, report_year, revenue_million, net_profit_million,
                   positive_reports, neutral_reports, negative_reports, report_coverage, published_at
            FROM mart.company_overview
            LIMIT ?
            ''',
            limit,
        )
        industry_heat = self._fetch_rows(
            db_path,
            '''
            SELECT industry_name, report_count, positive_count, negative_count, latest_report_date
            FROM mart.industry_heat
            LIMIT ?
            ''',
            limit,
        )
        company_research_heat = self._fetch_rows(
            db_path,
            '''
            SELECT company_code, company_name, report_count, positive_count, negative_count, latest_report_date
            FROM mart.company_research_heat
            LIMIT ?
            ''',
            limit,
        )
        return {
            **summary,
            'company_overview': company_overview,
            'industry_heat': industry_heat,
            'company_research_heat': company_research_heat,
        }
