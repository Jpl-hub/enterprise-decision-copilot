from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.universe import IndustryUniverseService

OUT_CSV = ROOT / 'data' / 'processed' / 'target_promotion_candidates.csv'
OUT_JSON = ROOT / 'data' / 'quality' / 'target_promotion_plan.json'


def main() -> None:
    service = IndustryUniverseService()
    payload = service.get_promotion_plan(limit=12, per_industry=2)
    if not payload.get('plan_ready'):
        raise RuntimeError('行业公司池尚未就绪，无法生成目标池扩容计划')

    candidates = pd.DataFrame(payload.get('candidates') or [])
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(OUT_CSV, index=False, encoding='utf-8-sig')
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    print(OUT_CSV)
    print(OUT_JSON)
    print(f"selected={len(candidates)}")


if __name__ == '__main__':
    main()
