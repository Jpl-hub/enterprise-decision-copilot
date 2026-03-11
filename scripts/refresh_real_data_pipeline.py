from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.llm import SiliconFlowClient


BASE_SCRIPTS = [
    'scripts/fetch_sse_official_reports.py',
    'scripts/fetch_szse_official_reports.py',
    'scripts/fetch_bse_official_reports.py',
    'scripts/build_official_report_inventory.py',
    'scripts/fetch_eastmoney_stock_reports.py',
    'scripts/fetch_eastmoney_industry_reports.py',
    'scripts/fetch_industry_company_universe.py',
    'scripts/fetch_official_macro_indicators.py',
]

LLM_SCRIPTS = [
    'scripts/extract_official_financial_panel.py',
    'scripts/build_official_financial_features.py',
]

FINAL_SCRIPTS = [
    'scripts/build_data_lake.py',
    'scripts/sync_csv_to_db.py',
]


def run_script(script_path: str) -> None:
    print(f'[refresh] running {script_path}')
    subprocess.run([sys.executable, script_path], cwd=ROOT, check=True)


if __name__ == '__main__':
    for script in BASE_SCRIPTS:
        run_script(script)

    if SiliconFlowClient().is_enabled():
        for script in LLM_SCRIPTS:
            run_script(script)
    else:
        print('[refresh] skip LLM extraction because API key is not configured')

    for script in FINAL_SCRIPTS:
        run_script(script)
    print('[refresh] completed')
