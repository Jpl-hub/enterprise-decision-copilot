from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
from PyPDF2 import PdfReader

from app.data_access import resolve_targets_csv_path


ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data" / "cache" / "official_extract"
INVENTORY_PATH = ROOT / "data" / "raw" / "official" / "report_inventory.csv"
TARGETS_PATH = ROOT / "data" / "targets.csv"
OFFICIAL_OUT_PATH = ROOT / "data" / "processed" / "financial_features_official.csv"
MASTER_OUT_PATH = ROOT / "data" / "processed" / "financial_features.csv"
QUALITY_PATH = ROOT / "data" / "quality" / "financial_features_official_quality.csv"

FIELDS = [
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

QUALITY_FIELDS = [
    "company_code",
    "company_name",
    "report_year",
    "filled_fields",
    "field_coverage_ratio",
    "critical_fields_missing",
    "anomaly_flags",
]

METRIC_FIELDS = [
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

AMOUNT_FIELDS = [
    "revenue_million",
    "net_profit_million",
    "operating_cashflow_million",
    "current_assets_million",
    "current_liabilities_million",
    "monetary_funds_million",
    "short_term_debt_million",
]

PAIR_REQUIRED_LABELS = {
    "货币资金",
    "应收账款",
    "存货",
    "流动资产合计",
    "流动负债合计",
    "资产总计",
    "负债合计",
}



def _load_manifest_records() -> list[dict]:
    if INVENTORY_PATH.exists():
        inventory = pd.read_csv(INVENTORY_PATH, dtype={"company_code": str, "disclosure_company_code": str})
        if inventory.empty:
            return []
        inventory = inventory[(inventory["status"] == "downloaded") & (inventory["file_exists"] == True)].copy()
        return inventory.to_dict("records")

    manifest_records: list[dict] = []
    legacy_paths = [
        ROOT / "data" / "raw" / "official" / "sse" / "report_manifest.json",
        ROOT / "data" / "raw" / "official" / "szse" / "report_manifest.json",
        ROOT / "data" / "raw" / "official" / "bse" / "report_manifest.json",
    ]
    for manifest_path in legacy_paths:
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest:
            if item.get("status") == "downloaded":
                manifest_records.append(item)
    return manifest_records
def _load_target_names() -> dict[str, str]:
    target_path = resolve_targets_csv_path()
    if not target_path.exists():
        return {}
    df = pd.read_csv(target_path, dtype={"company_code": str})
    return {
        str(row["company_code"]): str(row["company_name"])
        for _, row in df[["company_code", "company_name"]].drop_duplicates().iterrows()
    }


def _load_existing_rows(path: Path, sort_fields: list[str]) -> dict[tuple[str, int], dict]:
    if not path.exists():
        return {}
    df = pd.read_csv(path, dtype={"company_code": str})
    if df.empty:
        return {}
    df["company_code"] = df["company_code"].astype(str)
    df["report_year"] = df["report_year"].astype(int)
    return {
        (str(row["company_code"]), int(row["report_year"])): row.to_dict()
        for _, row in df.sort_values(sort_fields).iterrows()
    }


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_million(raw_value: float | None) -> float | None:
    if raw_value is None:
        return None
    return raw_value / 1_000_000


def _round_metric(value: float | None, digits: int = 2) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), digits)


def _compact(text: str) -> str:
    text = _normalize_chinese_spacing(text)
    return re.sub(r"\s+", " ", text)


def _normalize_chinese_spacing(text: str) -> str:
    normalized = text
    while True:
        updated = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", normalized)
        if updated == normalized:
            return updated
        normalized = updated


def _section(text: str, marker: str, span: int, end_markers: list[str] | None = None) -> str:
    start = text.find(marker)
    if start == -1:
        return ""
    end = min(len(text), start + span)
    for end_marker in end_markers or []:
        idx = text.find(end_marker, start + len(marker))
        if idx != -1:
            end = min(end, idx)
    return text[start:end]


def _read_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join((page.extract_text() or "").replace("\u2022", " ") for page in reader.pages)


def _extract_compact_value(section_text: str, pattern: str, amount: bool = False) -> float | None:
    if not section_text:
        return None
    match = re.search(pattern, _compact(section_text))
    if not match:
        return None
    value = float(match.group(1).replace(",", ""))
    return _to_million(value) if amount else value


def _extract_amount_pair_from_line(section_text: str, label: str) -> tuple[float | None, float | None]:
    if not section_text:
        return None, None

    for line in section_text.splitlines():
        normalized = _normalize_chinese_spacing(re.sub(r"\s+", " ", line)).strip()
        if not normalized.startswith(label):
            continue

        tokens = re.findall(r"-?[0-9][0-9,]*(?:\.\d+)?", normalized)
        amounts = [float(token.replace(",", "")) for token in tokens if "," in token or abs(float(token)) >= 1000]
        if not amounts:
            continue
        if label in PAIR_REQUIRED_LABELS and len(amounts) < 2:
            continue
        first = _to_million(amounts[0])
        second = _to_million(amounts[1]) if len(amounts) > 1 else None
        return first, second

    return None, None


def _sum_numbers(*values: float | None) -> float | None:
    usable = [value for value in values if value is not None]
    if not usable:
        return None
    return sum(usable)


def _derive_ratio(numerator: float | None, denominator: float | None, scale: float = 1.0) -> float | None:
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return numerator / denominator * scale


def _fix_amount_scale(row: dict, anomaly_flags: list[str]) -> None:
    for field in AMOUNT_FIELDS:
        value = _safe_float(row.get(field))
        if value is None:
            continue
        if abs(value) > 500_000:
            row[field] = value / 1000
            anomaly_flags.append(f"{field}:scaled_down_1000")


def _pick_preferred_value(
    field: str,
    raw_value: float | None,
    deterministic_value: float | None,
    anomaly_flags: list[str],
    lower_bound: float = 0.6,
    upper_bound: float = 1.67,
) -> float | None:
    if deterministic_value is None:
        return raw_value
    if raw_value is None:
        return deterministic_value
    if raw_value == 0:
        return deterministic_value

    ratio = abs(deterministic_value / raw_value)
    if ratio < lower_bound or ratio > upper_bound:
        anomaly_flags.append(f"{field}:use_llm_due_layout")
        return raw_value
    return deterministic_value


def _extract_deterministic_metrics(pdf_path: Path) -> dict[str, float | None]:
    text = _read_pdf_text(pdf_path)
    metric_section = _section(
        text,
        "主要会计数据和财务指标",
        6_000,
        end_markers=[
            "报告期末公司前三年主要会计数据和财务指标的说明",
            "分季度主要财务数据",
            "季度数据与已披露定期报告数据差异说明",
            "境内外会计准则下会计数据差异",
        ],
    ) or _section(
        text,
        "主要会计数据",
        6_000,
        end_markers=[
            "报告期末公司前三年主要会计数据和财务指标的说明",
            "分季度主要财务数据",
            "季度数据与已披露定期报告数据差异说明",
            "境内外会计准则下会计数据差异",
        ],
    )
    balance_section = _section(text, "合并资产负债表", 18_000)
    profit_section = _section(text, "利润表及现金流量表相关科目变动分析表", 6_000)

    revenue_million = _extract_compact_value(metric_section, r"营业收入\s+(-?[0-9,]+\.\d+)", amount=True)
    net_profit_million = _extract_compact_value(
        metric_section,
        r"归属于上市公司股\s*东的净利润\s+(-?[0-9,]+\.\d+)",
        amount=True,
    )
    operating_cashflow_million = _extract_compact_value(
        metric_section,
        r"经营活动产生的现\s*金流量净额\s+(-?[0-9,]+\.\d+)",
        amount=True,
    )
    roe_pct = _extract_compact_value(metric_section, r"加权平均净资产收益率（?\s*%\s*）?\s+(-?[0-9,]+(?:\.\d+)?)")
    rd_ratio_pct = _extract_compact_value(
        text,
        r"研发投入(?:总额)?占营业收入(?:比例)?[^\d-]{0,40}(-?[0-9,]+(?:\.\d+)?)",
    )

    monetary_funds_million, _ = _extract_amount_pair_from_line(balance_section, "货币资金")
    receivable_end_million, receivable_begin_million = _extract_amount_pair_from_line(balance_section, "应收账款")
    inventory_end_million, inventory_begin_million = _extract_amount_pair_from_line(balance_section, "存货")
    current_assets_million, _ = _extract_amount_pair_from_line(balance_section, "流动资产合计")
    current_liabilities_million, _ = _extract_amount_pair_from_line(balance_section, "流动负债合计")
    total_assets_million, _ = _extract_amount_pair_from_line(balance_section, "资产总计")
    total_liabilities_million, _ = _extract_amount_pair_from_line(balance_section, "负债合计")
    short_borrow_million, _ = _extract_amount_pair_from_line(balance_section, "短期借款")
    current_noncurrent_debt_million, _ = _extract_amount_pair_from_line(balance_section, "一年内到期的非流动负债")
    operating_cost_million = _extract_compact_value(profit_section, r"营业成本\s+(-?[0-9,]+\.\d+)", amount=True)

    return {
        "revenue_million": revenue_million,
        "net_profit_million": net_profit_million,
        "operating_cashflow_million": operating_cashflow_million,
        "roe_pct": roe_pct,
        "rd_ratio_pct": rd_ratio_pct,
        "monetary_funds_million": monetary_funds_million,
        "receivable_end_million": receivable_end_million,
        "receivable_begin_million": receivable_begin_million,
        "inventory_end_million": inventory_end_million,
        "inventory_begin_million": inventory_begin_million,
        "current_assets_million": current_assets_million,
        "current_liabilities_million": current_liabilities_million,
        "total_assets_million": total_assets_million,
        "total_liabilities_million": total_liabilities_million,
        "short_borrow_million": short_borrow_million,
        "current_noncurrent_debt_million": current_noncurrent_debt_million,
        "operating_cost_million": operating_cost_million,
    }


def _merge_existing_master(official_df: pd.DataFrame) -> pd.DataFrame:
    if MASTER_OUT_PATH.exists():
        existing = pd.read_csv(MASTER_OUT_PATH, dtype={"company_code": str})
    else:
        existing = pd.DataFrame(columns=FIELDS)

    if not existing.empty:
        existing["report_year"] = existing["report_year"].astype(int)
        existing = existing[~existing["company_code"].astype(str).isin(official_df["company_code"].astype(str).unique())]

    merged = pd.concat([existing[FIELDS], official_df[FIELDS]], ignore_index=True)
    merged["company_code"] = merged["company_code"].astype(str)
    merged["report_year"] = merged["report_year"].astype(int)
    return merged.sort_values(["company_code", "report_year"]).reset_index(drop=True)


def main() -> None:
    manifest_map: dict[tuple[str, int], dict] = {}
    for item in _load_manifest_records():
        manifest_map[(str(item["company_code"]), int(item["year"]))] = item
        disclosure_code = str(item.get("disclosure_company_code") or "")
        if disclosure_code and disclosure_code != str(item["company_code"]):
            manifest_map[(disclosure_code, int(item["year"]))] = item
    target_names = _load_target_names()
    existing_official_rows = _load_existing_rows(OFFICIAL_OUT_PATH, ["company_code", "report_year"])
    existing_quality_rows = _load_existing_rows(QUALITY_PATH, ["company_code", "report_year"])

    records: list[dict] = []
    quality_rows: list[dict] = []
    reused_count = 0
    rebuilt_count = 0

    for path in sorted(CACHE_DIR.glob("[0-9]*_[0-9][0-9][0-9][0-9].json")):
        obj = json.loads(path.read_text(encoding="utf-8"))
        company_code = str(obj.get("company_code"))
        report_year = int(obj.get("report_year"))
        manifest_item = manifest_map.get((company_code, report_year))
        if manifest_item is None:
            continue

        existing_row = existing_official_rows.get((company_code, report_year))
        existing_quality_row = existing_quality_rows.get((company_code, report_year))
        if (
            existing_row is not None
            and existing_quality_row is not None
            and str(existing_row.get("source_url") or "") == str(manifest_item.get("source_url") or "")
            and str(existing_row.get("published_at") or "") == str(manifest_item.get("published_at") or "")
        ):
            records.append({field: existing_row.get(field) for field in FIELDS})
            quality_rows.append({field: existing_quality_row.get(field) for field in QUALITY_FIELDS})
            reused_count += 1
            continue

        pdf_path = ROOT / manifest_item["local_path"]
        deterministic = _extract_deterministic_metrics(pdf_path)
        anomaly_flags: list[str] = []

        row = {field: obj.get(field) for field in FIELDS}
        row["company_code"] = company_code
        row["company_name"] = target_names.get(company_code, str(row.get("company_name") or "").strip())
        row["report_year"] = report_year
        row["source_url"] = manifest_item["source_url"]
        row["published_at"] = manifest_item["published_at"]

        for field in ["revenue_million", "net_profit_million", "operating_cashflow_million", "roe_pct", "rd_ratio_pct"]:
            row[field] = _pick_preferred_value(
                field,
                _safe_float(obj.get(field)),
                _safe_float(deterministic.get(field)),
                anomaly_flags,
            )

        for field in [
            "current_assets_million",
            "current_liabilities_million",
            "monetary_funds_million",
        ]:
            if deterministic.get(field) is not None:
                row[field] = deterministic[field]

        raw_short_term_debt_million = _safe_float(obj.get("short_term_debt_million"))
        short_term_debt_million = _sum_numbers(
            deterministic.get("short_borrow_million"),
            deterministic.get("current_noncurrent_debt_million"),
        )
        if deterministic.get("short_borrow_million") is None and raw_short_term_debt_million is not None:
            short_term_debt_million = raw_short_term_debt_million
        elif short_term_debt_million is None:
            short_term_debt_million = raw_short_term_debt_million

        row["current_assets_million"] = _safe_float(row.get("current_assets_million"))
        row["current_liabilities_million"] = _safe_float(row.get("current_liabilities_million"))
        row["monetary_funds_million"] = _safe_float(row.get("monetary_funds_million"))
        row["short_term_debt_million"] = short_term_debt_million

        _fix_amount_scale(row, anomaly_flags)

        revenue = _safe_float(row.get("revenue_million"))
        net_profit = _safe_float(row.get("net_profit_million"))
        operating_cost = _safe_float(deterministic.get("operating_cost_million"))
        total_assets = _safe_float(deterministic.get("total_assets_million"))
        total_liabilities = _safe_float(deterministic.get("total_liabilities_million"))
        inventory_end = _safe_float(deterministic.get("inventory_end_million"))
        inventory_begin = _safe_float(deterministic.get("inventory_begin_million"))
        receivable_end = _safe_float(deterministic.get("receivable_end_million"))
        receivable_begin = _safe_float(deterministic.get("receivable_begin_million"))

        if row.get("gross_margin_pct") is None and revenue is not None and operating_cost is not None:
            row["gross_margin_pct"] = _derive_ratio(revenue - operating_cost, revenue, 100)

        row["net_margin_pct"] = _derive_ratio(net_profit, revenue, 100)
        row["debt_ratio_pct"] = _derive_ratio(total_liabilities, total_assets, 100)
        row["current_ratio"] = _derive_ratio(
            _safe_float(row.get("current_assets_million")),
            _safe_float(row.get("current_liabilities_million")),
            1,
        )
        row["cash_to_short_debt"] = _derive_ratio(
            _safe_float(row.get("monetary_funds_million")),
            _safe_float(row.get("short_term_debt_million")),
            1,
        )

        avg_inventory = _safe_float(_sum_numbers(inventory_end, inventory_begin))
        if avg_inventory is not None:
            avg_inventory /= 2
        avg_receivable = _safe_float(_sum_numbers(receivable_end, receivable_begin))
        if avg_receivable is not None:
            avg_receivable /= 2

        row["inventory_turnover"] = _derive_ratio(operating_cost, avg_inventory, 1)
        row["receivable_turnover"] = _derive_ratio(revenue, avg_receivable, 1)

        if _safe_float(row.get("gross_margin_pct")) is None and revenue is not None and net_profit is not None:
            row["gross_margin_pct"] = _safe_float(obj.get("gross_margin_pct"))

        for field in [
            "gross_margin_pct",
            "net_margin_pct",
            "rd_ratio_pct",
            "debt_ratio_pct",
            "current_ratio",
            "cash_to_short_debt",
            "inventory_turnover",
            "receivable_turnover",
            "roe_pct",
        ]:
            row[field] = _round_metric(_safe_float(row.get(field)))

        for field in ["revenue_million", "net_profit_million", "operating_cashflow_million"]:
            row[field] = _round_metric(_safe_float(row.get(field)), 6)

        if revenue is not None and abs(revenue) > 100_000:
            anomaly_flags.append("revenue_million:outlier_high")
        if _safe_float(row.get("net_margin_pct")) is not None and abs(_safe_float(row.get("net_margin_pct"))) > 80:
            anomaly_flags.append("net_margin_pct:outlier")
        if _safe_float(row.get("inventory_turnover")) is not None and _safe_float(row.get("inventory_turnover")) > 30:
            anomaly_flags.append("inventory_turnover:outlier")
        if _safe_float(row.get("receivable_turnover")) is not None and _safe_float(row.get("receivable_turnover")) > 30:
            anomaly_flags.append("receivable_turnover:outlier")

        metric_filled = sum(1 for field in METRIC_FIELDS if _safe_float(row.get(field)) is not None)
        critical_missing = [
            field
            for field in [
                "revenue_million",
                "net_profit_million",
                "net_margin_pct",
                "debt_ratio_pct",
                "current_ratio",
                "operating_cashflow_million",
                "roe_pct",
            ]
            if _safe_float(row.get(field)) is None
        ]

        records.append({field: row.get(field) for field in FIELDS})
        quality_rows.append(
            {
                "company_code": row["company_code"],
                "company_name": row["company_name"],
                "report_year": row["report_year"],
                "filled_fields": metric_filled,
                "field_coverage_ratio": round(metric_filled / len(METRIC_FIELDS), 4),
                "critical_fields_missing": ",".join(critical_missing),
                "anomaly_flags": ",".join(dict.fromkeys(anomaly_flags)),
            }
        )
        rebuilt_count += 1

    if not records:
        raise RuntimeError("未找到官方抽取结果，请先运行 scripts/extract_official_financial_panel.py")

    official_df = pd.DataFrame(records).sort_values(["company_code", "report_year"]).reset_index(drop=True)
    master_df = _merge_existing_master(official_df)
    quality_df = pd.DataFrame(quality_rows).sort_values(["company_code", "report_year"]).reset_index(drop=True)

    OFFICIAL_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUALITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    official_df.to_csv(OFFICIAL_OUT_PATH, index=False, encoding="utf-8-sig")
    master_df.to_csv(MASTER_OUT_PATH, index=False, encoding="utf-8-sig")
    quality_df[QUALITY_FIELDS].to_csv(QUALITY_PATH, index=False, encoding="utf-8-sig")

    print(OFFICIAL_OUT_PATH)
    print(MASTER_OUT_PATH)
    print(QUALITY_PATH)
    print({"reused": reused_count, "rebuilt": rebuilt_count})


if __name__ == "__main__":
    main()

