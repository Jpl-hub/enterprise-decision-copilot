from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings
from app.services.quality import DataQualityService


OUT_PATH = settings.data_dir / "quality" / "retrieval_evaluation_summary.json"


def main() -> None:
    service = DataQualityService()
    payload = service.get_retrieval_evaluation_summary()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"retrieval evaluation written to {OUT_PATH}")
    print(
        json.dumps(
            {
                "case_count": payload.get("case_count"),
                "hit_at_3": payload.get("hit_at_3"),
                "hit_at_5": payload.get("hit_at_5"),
                "mrr": payload.get("mrr"),
                "ndcg_at_5": payload.get("ndcg_at_5"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
