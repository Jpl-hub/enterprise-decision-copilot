from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings
from app.db import get_connection, init_db


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def main() -> None:
    init_db()
    targets = read_csv(settings.data_dir / 'targets.csv')
    financials = read_csv(settings.processed_dir / 'financial_features.csv')
    reports = read_csv(settings.processed_dir / 'research_reports.csv')
    industry_reports = read_csv(settings.processed_dir / 'industry_reports.csv')
    industry_company_universe = read_csv(settings.processed_dir / 'industry_company_universe.csv')
    macro = read_csv(settings.processed_dir / 'macro_indicators.csv')

    with get_connection() as conn:
        targets.to_sql('companies', conn, if_exists='replace', index=False)
        financials.to_sql('financial_features', conn, if_exists='replace', index=False)
        reports.to_sql('research_reports', conn, if_exists='replace', index=False)
        industry_reports.to_sql('industry_reports', conn, if_exists='replace', index=False)
        industry_company_universe.to_sql('industry_company_universe', conn, if_exists='replace', index=False)
        macro.to_sql('macro_indicators', conn, if_exists='replace', index=False)
        conn.commit()

    print('已完成 CSV -> SQLite 同步：', settings.data_dir / 'app.db')
    print(
        f'companies={len(targets)}, financial_features={len(financials)}, '
        f'research_reports={len(reports)}, industry_reports={len(industry_reports)}, '
        f'industry_company_universe={len(industry_company_universe)}, macro_indicators={len(macro)}'
    )


if __name__ == '__main__':
    main()
