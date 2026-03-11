from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MM_EXTRACT_DIR = ROOT / "data" / "cache" / "official_extract_multimodal"
TEXT_EXTRACT_DIR = ROOT / "data" / "cache" / "official_extract"
OFFICIAL_FEATURE_PATH = ROOT / "data" / "processed" / "financial_features_official.csv"
OUT_DIR = ROOT / "data" / "datasets"

TARGET_FIELDS = [
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
]

SYSTEM_PROMPT = (
    "你是上市公司年报抽取助手。请根据给定页面图像和上下文提取 JSON，"
    "字段包括 company_name, report_year, revenue_million, net_profit_million, gross_margin_pct, "
    "net_margin_pct, rd_ratio_pct, debt_ratio_pct, current_ratio, cash_to_short_debt, "
    "inventory_turnover, receivable_turnover, operating_cashflow_million, roe_pct。"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建多模态财报抽取 SFT 数据集")
    parser.add_argument("--limit", type=int, default=0, help="样本上限，0 表示不限制")
    parser.add_argument("--min-fields", type=int, default=8, help="最少非空字段数")
    parser.add_argument("--out", type=str, default="official_multimodal_sft.jsonl", help="输出文件名")
    return parser.parse_args()


def load_label_map() -> dict[tuple[str, int], dict]:
    if not OFFICIAL_FEATURE_PATH.exists():
        raise FileNotFoundError(f"未找到标签文件: {OFFICIAL_FEATURE_PATH}")
    frame = pd.read_csv(OFFICIAL_FEATURE_PATH, dtype={"company_code": str})
    if frame.empty:
        return {}
    frame["report_year"] = frame["report_year"].astype(int)
    return {
        (str(row["company_code"]), int(row["report_year"])): row.to_dict()
        for _, row in frame.iterrows()
    }


def load_snippet_text(company_code: str, report_year: int) -> str:
    snippet_path = TEXT_EXTRACT_DIR / f"{company_code}_{report_year}_snippets.json"
    if not snippet_path.exists():
        return ""
    snippets = json.loads(snippet_path.read_text(encoding="utf-8"))
    lines: list[str] = []
    for field, values in snippets.items():
        if not values:
            continue
        lines.append(f"## {field}")
        lines.extend(str(v) for v in values[:2])
    return "\n".join(lines)


def count_filled(label: dict) -> int:
    filled = 0
    for field in TARGET_FIELDS:
        if field in {"company_code", "company_name", "report_year"}:
            continue
        value = label.get(field)
        if value is None:
            continue
        if isinstance(value, float) and pd.isna(value):
            continue
        filled += 1
    return filled


def to_label_payload(label_row: dict) -> dict:
    payload = {}
    for field in TARGET_FIELDS:
        value = label_row.get(field)
        if isinstance(value, float) and pd.isna(value):
            payload[field] = None
        elif field == "report_year":
            payload[field] = int(value)
        elif field == "company_code":
            payload[field] = str(value)
        else:
            payload[field] = value
    return payload


def main() -> None:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    label_map = load_label_map()
    if not MM_EXTRACT_DIR.exists():
        raise FileNotFoundError(f"未找到多模态抽取结果目录: {MM_EXTRACT_DIR}")

    rows: list[dict] = []
    for path in sorted(MM_EXTRACT_DIR.glob("*_*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        company_code = str(record.get("company_code") or "")
        report_year = int(record.get("report_year") or 0)
        if not company_code or report_year <= 0:
            continue

        label_row = label_map.get((company_code, report_year))
        if label_row is None:
            continue
        if count_filled(label_row) < args.min_fields:
            continue

        image_paths = [str(item) for item in (record.get("page_images") or [])]
        if not image_paths:
            continue

        context_text = load_snippet_text(company_code, report_year)
        user_text = "\n".join(
            [
                f"company_code: {company_code}",
                f"report_year_target: {report_year}",
                "请基于页面图像抽取关键财务字段。",
                "辅助文本证据：",
                context_text or "暂无",
            ]
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": {
                    "text": user_text,
                    "images": image_paths,
                },
            },
            {"role": "assistant", "content": json.dumps(to_label_payload(label_row), ensure_ascii=False)},
        ]

        rows.append(
            {
                "id": f"{company_code}_{report_year}",
                "company_code": company_code,
                "report_year": report_year,
                "messages": messages,
                "label": to_label_payload(label_row),
                "image_paths": image_paths,
            }
        )

        if args.limit > 0 and len(rows) >= args.limit:
            break

    output_path = OUT_DIR / args.out
    with output_path.open("w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(json.dumps({"output": str(output_path), "samples": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
