from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings
from app.data_access import load_targets


OUTPUT = settings.raw_dir / "announcements" / "announcement_tasks.csv"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

targets = load_targets().to_dict("records")
rows = []
for item in targets:
    rows.append(
        {
            "company_code": item["company_code"],
            "company_name": item["company_name"],
            "exchange": item["exchange"],
            "base_url": {
                "SSE": "https://www.sse.com.cn/disclosure/listedinfo/regular/",
                "SZSE": "https://www.szse.cn/disclosure/listed/fixed/index.html",
                "BSE": "https://www.bse.cn/disclosure/announcement.html",
            }.get(item["exchange"], ""),
            "status": "pending",
            "note": "后续通过 Playwright 或人工辅助方式抓取定期报告链接",
        }
    )

with OUTPUT.open("w", newline="", encoding="utf-8-sig") as fp:
    writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"已生成公告抓取任务清单：{OUTPUT}")
