from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings
from app.data_access import load_targets


OUTPUT = settings.processed_dir / "research_reports.csv"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

fields = [
    "company_code",
    "company_name",
    "report_date",
    "title",
    "analyst_view",
    "institution",
    "sentiment",
    "content",
    "source_url",
]

with OUTPUT.open("w", newline="", encoding="utf-8-sig") as fp:
    writer = csv.DictWriter(fp, fieldnames=fields)
    writer.writeheader()

print(f"已初始化研报结构化文件：{OUTPUT}")
print("建议后续通过东方财富列表页抓取标题、日期、机构、观点与正文摘要。")
print("当前目标企业：")
for row in load_targets().to_dict("records"):
    print(row["company_name"])
