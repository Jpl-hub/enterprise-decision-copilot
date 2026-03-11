from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
PROCESSED = DATA_DIR / 'processed'
LAKE = DATA_DIR / 'lake'
BRONZE = LAKE / 'bronze'
SILVER = LAKE / 'silver'
GOLD = LAKE / 'gold'
WAREHOUSE_DIR = DATA_DIR / 'warehouse'
WAREHOUSE_DB = WAREHOUSE_DIR / 'analytics.duckdb'
QUALITY = DATA_DIR / 'quality'
WAREHOUSE_SUMMARY = QUALITY / 'warehouse_summary.json'
OFFICIAL_INVENTORY = DATA_DIR / 'raw' / 'official' / 'report_inventory.csv'
INDUSTRY_UNIVERSE = PROCESSED / 'industry_company_universe.csv'
INDUSTRY_UNIVERSE_REPORTS = PROCESSED / 'industry_company_universe_reports.csv'

for path in [BRONZE, SILVER, GOLD, WAREHOUSE_DIR, QUALITY]:
    path.mkdir(parents=True, exist_ok=True)


def write_partitioned_csv(df: pd.DataFrame, out_dir: Path, name: str) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'{name}.csv'
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    return str(out_path)


def write_partitioned_parquet(df: pd.DataFrame, out_dir: Path, name: str) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'{name}.parquet'
    escaped = out_path.as_posix().replace("'", "''")
    connection = duckdb.connect()
    try:
        connection.register('frame', df)
        connection.execute(f"COPY frame TO '{escaped}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        connection.unregister('frame')
    finally:
        connection.close()
    return str(out_path)


def profile_table(name: str, df: pd.DataFrame, keys: list[str] | None = None) -> dict:
    keys = keys or []
    duplicates = 0
    if keys and not df.empty:
        duplicates = int(df.duplicated(subset=keys).sum())
    null_ratio = {col: round(float(df[col].isna().mean()), 4) for col in df.columns}
    return {
        'table': name,
        'rows': int(len(df)),
        'columns': list(df.columns),
        'duplicate_rows': duplicates,
        'null_ratio': null_ratio,
    }


def build_gold_company_view(financials: pd.DataFrame, reports: pd.DataFrame) -> pd.DataFrame:
    report_agg = pd.DataFrame(columns=['company_code', 'positive_reports', 'neutral_reports', 'negative_reports'])
    if not reports.empty:
        report_agg = reports.groupby('company_code').agg(
            positive_reports=('sentiment', lambda s: int((s == 'positive').sum())),
            neutral_reports=('sentiment', lambda s: int((s == 'neutral').sum())),
            negative_reports=('sentiment', lambda s: int((s == 'negative').sum())),
        ).reset_index()
    return financials.merge(report_agg, on='company_code', how='left').fillna({
        'positive_reports': 0,
        'neutral_reports': 0,
        'negative_reports': 0,
    })


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def build_duckdb_warehouse(layouts: list[tuple[str, str, Path]]) -> dict:
    if WAREHOUSE_DB.exists():
        WAREHOUSE_DB.unlink()

    connection = duckdb.connect(str(WAREHOUSE_DB))
    tables = []
    mart_views = [
        'mart.company_latest',
        'mart.report_sentiment',
        'mart.company_overview',
        'mart.industry_heat',
        'mart.company_research_heat',
    ]
    try:
        for schema_name, table, parquet_path in layouts:
            escaped = parquet_path.as_posix().replace("'", "''")
            connection.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_name}')
            connection.execute(f"CREATE OR REPLACE TABLE {schema_name}.{table} AS SELECT * FROM read_parquet('{escaped}')")
            row_count = int(connection.execute(f'SELECT COUNT(*) FROM {schema_name}.{table}').fetchone()[0])
            tables.append({'schema_name': schema_name, 'table': table, 'rows': row_count, 'parquet_path': str(parquet_path)})

        connection.execute('CREATE SCHEMA IF NOT EXISTS mart')
        connection.execute(
            '''
            CREATE OR REPLACE VIEW mart.company_latest AS
            SELECT *
            FROM gold.company_fact
            QUALIFY ROW_NUMBER() OVER (PARTITION BY company_code ORDER BY report_year DESC) = 1
            '''
        )
        connection.execute(
            '''
            CREATE OR REPLACE VIEW mart.report_sentiment AS
            SELECT company_code, positive_reports, neutral_reports, negative_reports
            FROM mart.company_latest
            '''
        )
        connection.execute(
            '''
            CREATE OR REPLACE VIEW mart.company_overview AS
            SELECT
                company_code,
                company_name,
                report_year,
                revenue_million,
                net_profit_million,
                positive_reports,
                neutral_reports,
                negative_reports,
                positive_reports + neutral_reports + negative_reports AS report_coverage,
                source_url,
                published_at
            FROM mart.company_latest
            ORDER BY revenue_million DESC NULLS LAST, company_code ASC
            '''
        )
        connection.execute(
            '''
            CREATE OR REPLACE VIEW mart.industry_heat AS
            SELECT
                industry_name,
                COUNT(*) AS report_count,
                SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) AS positive_count,
                SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) AS negative_count,
                MAX(report_date) AS latest_report_date
            FROM silver.industry_reports
            GROUP BY industry_name
            ORDER BY report_count DESC, industry_name ASC
            '''
        )
        connection.execute(
            '''
            CREATE OR REPLACE VIEW mart.company_research_heat AS
            SELECT
                company_code,
                company_name,
                COUNT(*) AS report_count,
                SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) AS positive_count,
                SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) AS negative_count,
                MAX(report_date) AS latest_report_date
            FROM silver.research_reports
            GROUP BY company_code, company_name
            ORDER BY report_count DESC, company_code ASC
            '''
        )
        if any(table == 'industry_company_universe' for _, table, _ in layouts):
            connection.execute(
                '''
                CREATE OR REPLACE VIEW mart.industry_company_universe AS
                SELECT
                    industry_name,
                    exchange,
                    company_code,
                    company_name,
                    report_count,
                    institution_count,
                    positive_count,
                    negative_count,
                    latest_report_date,
                    in_target_pool,
                    latest_source_url
                FROM silver.industry_company_universe
                ORDER BY report_count DESC, institution_count DESC, company_code ASC
                '''
            )
            mart_views.append('mart.industry_company_universe')
        latest_count = int(connection.execute('SELECT COUNT(*) FROM mart.company_latest').fetchone()[0])
    finally:
        connection.close()

    summary = {
        'warehouse_db': str(WAREHOUSE_DB),
        'table_count': len(tables),
        'mart_views': mart_views,
        'latest_company_rows': latest_count,
        'tables': tables,
    }
    WAREHOUSE_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary


def main() -> None:
    financials = pd.read_csv(PROCESSED / 'financial_features.csv')
    reports = pd.read_csv(PROCESSED / 'research_reports.csv')
    industry_reports = pd.read_csv(PROCESSED / 'industry_reports.csv')
    macro = pd.read_csv(PROCESSED / 'macro_indicators.csv')
    sources = pd.read_csv(DATA_DIR / 'source_registry.csv')
    official_inventory = read_csv_if_exists(OFFICIAL_INVENTORY)
    industry_universe = read_csv_if_exists(INDUSTRY_UNIVERSE)
    industry_universe_reports = read_csv_if_exists(INDUSTRY_UNIVERSE_REPORTS)

    financials_silver = financials.drop_duplicates(subset=['company_code', 'report_year']).copy()
    reports_silver = reports.drop_duplicates().copy()
    industry_reports_silver = industry_reports.drop_duplicates().copy()
    macro_silver = macro.drop_duplicates().copy()
    sources_silver = sources.drop_duplicates().copy()
    official_inventory_silver = official_inventory.drop_duplicates().copy() if not official_inventory.empty else official_inventory.copy()
    industry_universe_silver = industry_universe.drop_duplicates(subset=['company_code']).copy() if not industry_universe.empty else industry_universe.copy()
    industry_universe_reports_silver = industry_universe_reports.drop_duplicates().copy() if not industry_universe_reports.empty else industry_universe_reports.copy()
    gold_company = build_gold_company_view(financials_silver, reports_silver)

    specs = [
        ('bronze', 'financial_features', financials, BRONZE / 'financial_features'),
        ('bronze', 'research_reports', reports, BRONZE / 'research_reports'),
        ('bronze', 'industry_reports', industry_reports, BRONZE / 'industry_reports'),
        ('bronze', 'macro_indicators', macro, BRONZE / 'macro_indicators'),
        ('bronze', 'source_registry', sources, BRONZE / 'source_registry'),
        ('silver', 'financial_features', financials_silver, SILVER / 'financial_features'),
        ('silver', 'research_reports', reports_silver, SILVER / 'research_reports'),
        ('silver', 'industry_reports', industry_reports_silver, SILVER / 'industry_reports'),
        ('silver', 'macro_indicators', macro_silver, SILVER / 'macro_indicators'),
        ('silver', 'source_registry', sources_silver, SILVER / 'source_registry'),
        ('gold', 'company_fact', gold_company, GOLD / 'company_fact'),
    ]
    if not official_inventory.empty:
        specs.extend(
            [
                ('bronze', 'official_report_inventory', official_inventory, BRONZE / 'official_report_inventory'),
                ('silver', 'official_report_inventory', official_inventory_silver, SILVER / 'official_report_inventory'),
            ]
        )
    if not industry_universe.empty:
        specs.extend(
            [
                ('bronze', 'industry_company_universe', industry_universe, BRONZE / 'industry_company_universe'),
                ('silver', 'industry_company_universe', industry_universe_silver, SILVER / 'industry_company_universe'),
            ]
        )
    if not industry_universe_reports.empty:
        specs.extend(
            [
                ('bronze', 'industry_company_universe_reports', industry_universe_reports, BRONZE / 'industry_company_universe_reports'),
                ('silver', 'industry_company_universe_reports', industry_universe_reports_silver, SILVER / 'industry_company_universe_reports'),
            ]
        )

    csv_outputs: list[str] = []
    parquet_outputs: list[str] = []
    warehouse_layouts: list[tuple[str, str, Path]] = []
    for schema_name, table, df, out_dir in specs:
        csv_outputs.append(write_partitioned_csv(df, out_dir, 'part-0000'))
        parquet_path = Path(write_partitioned_parquet(df, out_dir, 'part-0000'))
        parquet_outputs.append(str(parquet_path))
        warehouse_layouts.append((schema_name, table, parquet_path))

    warehouse_summary = build_duckdb_warehouse(warehouse_layouts)

    quality_report = {
        'financial_features': profile_table('financial_features', financials_silver, ['company_code', 'report_year']),
        'research_reports': profile_table('research_reports', reports_silver),
        'industry_reports': profile_table('industry_reports', industry_reports_silver),
        'macro_indicators': profile_table('macro_indicators', macro_silver, ['period', 'indicator_name']),
        'source_registry': profile_table('source_registry', sources_silver, ['source_type', 'source_name']),
        'company_fact': profile_table('company_fact', gold_company, ['company_code', 'report_year']),
        'artifacts': csv_outputs,
        'parquet_artifacts': parquet_outputs,
        'warehouse': warehouse_summary,
    }
    if not official_inventory.empty:
        quality_report['official_report_inventory'] = profile_table(
            'official_report_inventory',
            official_inventory_silver,
            ['exchange', 'company_code', 'year', 'source_url'],
        )
    if not industry_universe.empty:
        quality_report['industry_company_universe'] = profile_table(
            'industry_company_universe',
            industry_universe_silver,
            ['company_code'],
        )
    if not industry_universe_reports.empty:
        quality_report['industry_company_universe_reports'] = profile_table(
            'industry_company_universe_reports',
            industry_universe_reports_silver,
            ['company_code', 'report_date', 'title', 'institution'],
        )

    (QUALITY / 'quality_report.json').write_text(json.dumps(quality_report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('bronze/silver/gold data lake built')
    print('warehouse summary:', WAREHOUSE_SUMMARY)
    print('quality report:', QUALITY / 'quality_report.json')


if __name__ == '__main__':
    main()
