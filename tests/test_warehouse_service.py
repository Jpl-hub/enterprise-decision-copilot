import json
import shutil
import uuid
from pathlib import Path

import duckdb

from app.services.warehouse import WarehouseService



def test_warehouse_service_reads_summary_file() -> None:
    base_dir = Path('data/test_warehouse') / uuid.uuid4().hex
    summary_path = base_dir / 'warehouse_summary.json'
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(
            {
                'warehouse_db': str(base_dir / 'missing.duckdb'),
                'table_count': 8,
                'latest_company_rows': 6,
                'mart_views': ['mart.company_latest'],
                'tables': [
                    {'schema_name': 'gold', 'table': 'company_fact', 'rows': 18, 'parquet_path': 'data/lake/gold/company_fact/part-0000.parquet'}
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )
    try:
        payload = WarehouseService(warehouse_summary_path=summary_path).get_summary()
        assert payload['warehouse_ready'] is False
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)



def test_warehouse_service_returns_empty_state_when_missing() -> None:
    payload = WarehouseService(warehouse_summary_path=Path('data/test_warehouse/missing.json')).get_summary()
    assert payload['warehouse_ready'] is False
    assert payload['table_count'] == 0



def test_warehouse_service_overview_queries_duckdb_views() -> None:
    base_dir = Path('data/test_warehouse') / uuid.uuid4().hex
    summary_path = base_dir / 'warehouse_summary.json'
    db_path = base_dir / 'analytics.duckdb'
    base_dir.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(db_path))
    connection.execute('CREATE SCHEMA mart')
    connection.execute(
        '''
        CREATE TABLE mart.company_overview AS
        SELECT * FROM (
            VALUES ('300760', '迈瑞医疗', 2024, 36700.0, 11600.0, 10, 2, 1, 13, '2025-04-29')
        ) AS t(company_code, company_name, report_year, revenue_million, net_profit_million, positive_reports, neutral_reports, negative_reports, report_coverage, published_at)
        '''
    )
    connection.execute(
        '''
        CREATE TABLE mart.industry_heat AS
        SELECT * FROM (
            VALUES ('化学制药', 200, 160, 8, '2026-03-01')
        ) AS t(industry_name, report_count, positive_count, negative_count, latest_report_date)
        '''
    )
    connection.execute(
        '''
        CREATE TABLE mart.company_research_heat AS
        SELECT * FROM (
            VALUES ('300760', '迈瑞医疗', 71, 55, 3, '2026-03-05')
        ) AS t(company_code, company_name, report_count, positive_count, negative_count, latest_report_date)
        '''
    )
    connection.close()

    summary_path.write_text(
        json.dumps(
            {
                'warehouse_db': str(db_path),
                'table_count': 3,
                'latest_company_rows': 1,
                'mart_views': ['mart.company_overview', 'mart.industry_heat', 'mart.company_research_heat'],
                'tables': [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )

    try:
        payload = WarehouseService(warehouse_summary_path=summary_path).get_overview(limit=5)
        assert payload['warehouse_ready'] is True
        assert payload['company_overview'][0]['company_code'] == '300760'
        assert payload['industry_heat'][0]['industry_name'] == '化学制药'
        assert payload['company_research_heat'][0]['report_count'] == 71
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)
