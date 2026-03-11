from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings


OUTPUT = settings.processed_dir / "financial_features.csv"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

fields = [
    "company_code",
    "company_name",
    "report_year",
    "revenue_million",
    "net_profit_million",
    "gross_margin_pct",
    "net_margin_pct",
    "rd_ratio_pct",
    "debt_ratio_pct",
    "current_ratio",
    "cash_to_short_debt",
    "inventory_turnover",
    "receivable_turnover",
    "operating_cashflow_million",
    "roe_pct",
    "source_url",
    "published_at",
]

with OUTPUT.open("w", newline="", encoding="utf-8-sig") as fp:
    writer = csv.DictWriter(fp, fieldnames=fields)
    writer.writeheader()

print(f"已生成财报结构化结果模板：{OUTPUT}")
print("后续可将 LLM 抽取结果或人工校验结果写入此文件。")
