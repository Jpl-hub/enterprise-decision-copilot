from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings


OUTPUT = settings.processed_dir / "macro_indicators.csv"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

fields = ["period", "indicator_name", "indicator_value", "unit", "source_url"]
with OUTPUT.open("w", newline="", encoding="utf-8-sig") as fp:
    writer = csv.DictWriter(fp, fieldnames=fields)
    writer.writeheader()

print(f"已初始化宏观指标文件：{OUTPUT}")
print("建议先录入国家统计局中的 CPI、医疗保健 CPI、社零、固定资产投资等指标。")
