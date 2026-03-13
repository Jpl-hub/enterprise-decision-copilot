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

    def _fetch_rows(self, db_path: Path, sql: str, limit: Any) -> list[dict[str, Any]]:
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

    def build_company_sql_playbook(self, company_code: str, company_name: str | None = None) -> dict:
        summary = self.get_summary()
        normalized_code = str(company_code)
        queries = [
            {
                'query_id': 'company-overview',
                'title': '公司财务总览',
                'sql': (
                    "SELECT company_code, company_name, report_year, revenue_million, net_profit_million, "
                    "positive_reports, negative_reports, report_coverage, published_at "
                    "FROM mart.company_overview WHERE company_code = ? ORDER BY report_year DESC LIMIT 4"
                ),
                'params': [normalized_code],
            },
            {
                'query_id': 'research-heat',
                'title': '公司研报热度',
                'sql': (
                    "SELECT company_code, company_name, report_count, positive_count, negative_count, latest_report_date "
                    "FROM mart.company_research_heat WHERE company_code = ? LIMIT 1"
                ),
                'params': [normalized_code],
            },
        ]
        missions = [
            {
                'mission_id': 'finance-drilldown',
                'label': '财务钻取',
                'goal': '快速回放年度财务表现与研报覆盖变化。',
            },
            {
                'mission_id': 'sentiment-shift',
                'label': '观点迁移',
                'goal': '识别正负面研报变化以及最近观点拐点。',
            },
            {
                'mission_id': 'boardroom-followup',
                'label': '会议追问',
                'goal': '把管理层追问沉淀为可复用 SQL 任务。',
            },
        ]
        if not summary.get('warehouse_ready'):
            return {
                'warehouse_ready': False,
                'current_engine': 'python + duckdb',
                'company_code': normalized_code,
                'company_name': company_name,
                'queries': queries,
                'missions': missions,
                'company_overview_rows': [],
                'research_heat_rows': [],
            }

        db_path = Path(summary['warehouse_db'])
        company_overview_rows = self._fetch_rows(
            db_path,
            '''
            SELECT company_code, company_name, report_year, revenue_million, net_profit_million,
                   positive_reports, negative_reports, report_coverage, published_at
            FROM mart.company_overview
            WHERE company_code = ?
            ORDER BY report_year DESC
            LIMIT 4
            ''',
            limit=normalized_code,
        )
        research_heat_rows = self._fetch_rows(
            db_path,
            '''
            SELECT company_code, company_name, report_count, positive_count, negative_count, latest_report_date
            FROM mart.company_research_heat
            WHERE company_code = ?
            LIMIT 1
            ''',
            limit=normalized_code,
        )
        return {
            'warehouse_ready': True,
            'current_engine': 'python + duckdb',
            'warehouse_db': summary.get('warehouse_db'),
            'company_code': normalized_code,
            'company_name': company_name or (company_overview_rows[0]['company_name'] if company_overview_rows else None),
            'queries': queries,
            'missions': missions,
            'company_overview_rows': company_overview_rows,
            'research_heat_rows': research_heat_rows,
        }

    def build_compare_sql_playbook(self, company_codes: list[str]) -> dict:
        normalized_codes = [str(code) for code in company_codes if str(code).strip()]
        return {
            'warehouse_ready': bool(self.get_summary().get('warehouse_ready')),
            'current_engine': 'python + duckdb',
            'company_code': ','.join(normalized_codes) if normalized_codes else None,
            'company_name': None,
            'queries': [
                {
                    'query_id': 'compare-overview',
                    'title': '双企业财务对比',
                    'sql': (
                        "SELECT company_code, company_name, report_year, revenue_million, net_profit_million, "
                        "positive_reports, negative_reports "
                        "FROM mart.company_overview WHERE company_code IN (?, ?) ORDER BY report_year DESC"
                    ),
                    'params': normalized_codes[:2],
                },
                {
                    'query_id': 'compare-research-heat',
                    'title': '双企业研报热度对比',
                    'sql': (
                        "SELECT company_code, company_name, report_count, positive_count, negative_count, latest_report_date "
                        "FROM mart.company_research_heat WHERE company_code IN (?, ?)"
                    ),
                    'params': normalized_codes[:2],
                },
            ],
            'missions': [
                {'mission_id': 'compare-finance', 'label': '财务对抗', 'goal': '拉齐营收、利润、现金流和风险指标，形成双企业对抗视图。'},
                {'mission_id': 'compare-sentiment', 'label': '观点对抗', 'goal': '比较机构观点与行业主题的支持度差异。'},
                {'mission_id': 'compare-boardroom', 'label': '会议对抗', 'goal': '把双企业对比转成管理层对抗会议可复用模板。'},
            ],
            'company_overview_rows': [],
            'research_heat_rows': [],
        }

    def build_industry_sql_playbook(self, topic: str) -> dict:
        normalized_topic = str(topic or '').strip() or '医药赛道'
        return {
            'warehouse_ready': bool(self.get_summary().get('warehouse_ready')),
            'current_engine': 'python + duckdb',
            'company_code': None,
            'company_name': normalized_topic,
            'queries': [
                {
                    'query_id': 'industry-heat',
                    'title': '行业热度总览',
                    'sql': (
                        "SELECT industry_name, report_count, positive_count, negative_count, latest_report_date "
                        "FROM mart.industry_heat ORDER BY report_count DESC LIMIT 8"
                    ),
                    'params': [],
                },
                {
                    'query_id': 'macro-linkage',
                    'title': '行业与宏观联动',
                    'sql': "SELECT period, indicator_name, indicator_value, unit FROM macro_indicators ORDER BY period DESC LIMIT 12",
                    'params': [],
                },
            ],
            'missions': [
                {'mission_id': 'industry-theme-scan', 'label': '主题扫描', 'goal': '识别行业主题、机构正负观点和赛道热度变化。'},
                {'mission_id': 'industry-macro-link', 'label': '宏观联动', 'goal': '把行业判断和宏观脉冲放进同一会议画布。'},
                {'mission_id': 'industry-boardroom', 'label': '专题会议', 'goal': '形成赛道专题会议纪要和后续追问脚本。'},
            ],
            'company_overview_rows': [],
            'research_heat_rows': [],
        }
