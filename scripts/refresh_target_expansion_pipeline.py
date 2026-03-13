from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.data_access import resolve_targets_csv_path
from app.services.llm import SiliconFlowClient


QUALITY_DIR = ROOT / 'data' / 'quality'
SUMMARY_PATH = QUALITY_DIR / 'target_pool_refresh_summary.json'
STRICT_TARGETS_PATH = ROOT / 'data' / 'targets_expanded_strict.csv'
STRICT_SUMMARY_PATH = QUALITY_DIR / 'targets_expanded_strict_summary.json'
EXPANDED_TARGETS_PATH = ROOT / 'data' / 'targets_expanded.csv'
EXPANDED_SUMMARY_PATH = QUALITY_DIR / 'targets_expanded_summary.json'

BASE_SCRIPTS = [
    'scripts/build_target_promotion_plan.py',
    'scripts/fetch_promoted_official_reports.py',
    'scripts/build_official_report_inventory.py',
]

LLM_SCRIPTS = [
    'scripts/extract_official_financial_panel.py',
    'scripts/build_official_financial_features.py',
]


def run_script(script_path: str, *args: str) -> None:
    command = [sys.executable, script_path, *args]
    print('[target-refresh] running', ' '.join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def main() -> None:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)

    for script in BASE_SCRIPTS:
        run_script(script)

    llm_enabled = SiliconFlowClient().is_enabled()
    if llm_enabled:
        for script in LLM_SCRIPTS:
            run_script(script)
    else:
        print('[target-refresh] skip LLM extraction because API key is not configured')

    run_script(
        'scripts/expand_target_pool.py',
        '--coverage-source',
        'financial',
        '--max-total',
        '12',
        '--min-feature-years',
        '2',
        '--output',
        str(EXPANDED_TARGETS_PATH),
        '--summary',
        str(EXPANDED_SUMMARY_PATH),
    )
    run_script(
        'scripts/expand_target_pool.py',
        '--coverage-source',
        'official',
        '--max-total',
        '12',
        '--min-feature-years',
        '1',
        '--output',
        str(STRICT_TARGETS_PATH),
        '--summary',
        str(STRICT_SUMMARY_PATH),
    )

    summary = {
        'core_target_path': str((ROOT / 'data' / 'targets.csv').relative_to(ROOT)),
        'active_target_path': str(resolve_targets_csv_path().relative_to(ROOT)),
        'llm_enabled': llm_enabled,
        'expanded_pool': read_json(EXPANDED_SUMMARY_PATH),
        'strict_pool': read_json(STRICT_SUMMARY_PATH),
        'official_inventory': read_json(ROOT / 'data' / 'quality' / 'official_reports_quality.json'),
        'promotion_plan': read_json(ROOT / 'data' / 'quality' / 'target_promotion_plan.json'),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(SUMMARY_PATH)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
