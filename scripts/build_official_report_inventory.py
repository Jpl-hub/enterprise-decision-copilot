from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_OFFICIAL_DIR = ROOT / "data" / "raw" / "official"
QUALITY_DIR = ROOT / "data" / "quality"
TARGETS_PATH = ROOT / "data" / "targets.csv"
INVENTORY_PATH = RAW_OFFICIAL_DIR / "report_inventory.csv"
QUALITY_PATH = QUALITY_DIR / "official_reports_quality.json"
YEARS = [2022, 2023, 2024]

MANIFEST_SPECS = [
    ("SSE", RAW_OFFICIAL_DIR / "sse" / "report_manifest.json"),
    ("SZSE", RAW_OFFICIAL_DIR / "szse" / "report_manifest.json"),
    ("BSE", RAW_OFFICIAL_DIR / "bse" / "report_manifest.json"),
]



def load_manifest_rows() -> list[dict]:
    rows: list[dict] = []
    for exchange, path in MANIFEST_SPECS:
        if not path.exists():
            continue
        items = json.loads(path.read_text(encoding="utf-8"))
        for item in items:
            local_path = str(item.get("local_path") or "")
            absolute_local_path = ROOT / local_path if local_path else None
            file_exists = bool(absolute_local_path and absolute_local_path.exists())
            size_bytes = item.get("size_bytes")
            if size_bytes in (None, "") and file_exists and absolute_local_path is not None:
                size_bytes = absolute_local_path.stat().st_size
            rows.append(
                {
                    "exchange": exchange,
                    "company_code": str(item.get("company_code") or item.get("query_company_code") or ""),
                    "disclosure_company_code": str(item.get("disclosure_company_code") or item.get("company_code") or ""),
                    "company_name": str(item.get("company_name") or ""),
                    "year": int(item.get("year")) if item.get("year") not in (None, "") else None,
                    "title": str(item.get("title") or ""),
                    "published_at": str(item.get("published_at") or ""),
                    "source_url": str(item.get("source_url") or ""),
                    "local_path": local_path,
                    "file_exists": file_exists,
                    "size_bytes": int(size_bytes) if size_bytes not in (None, "") else None,
                    "status": str(item.get("status") or "unknown"),
                    "manifest_path": str(path.relative_to(ROOT)),
                }
            )
    return rows



def build_target_coverage(inventory_df: pd.DataFrame) -> dict:
    if not TARGETS_PATH.exists():
        return {
            "expected_slots": 0,
            "downloaded_slots": 0,
            "coverage_ratio": 0.0,
            "missing_slots": [],
        }

    targets = pd.read_csv(TARGETS_PATH, dtype={"company_code": str})
    if targets.empty:
        return {
            "expected_slots": 0,
            "downloaded_slots": 0,
            "coverage_ratio": 0.0,
            "missing_slots": [],
        }

    downloaded = inventory_df[
        (inventory_df["status"] == "downloaded") & inventory_df["file_exists"]
    ] if not inventory_df.empty else pd.DataFrame(columns=["company_code", "year", "exchange"])

    missing_slots: list[dict] = []
    downloaded_slots = 0
    for _, row in targets[["company_code", "company_name", "exchange"]].drop_duplicates().iterrows():
        code = str(row["company_code"])
        for year in YEARS:
            matched = downloaded[
                (downloaded["company_code"].astype(str) == code)
                & (downloaded["year"].astype("Int64") == year)
            ]
            if matched.empty:
                missing_slots.append(
                    {
                        "company_code": code,
                        "company_name": str(row["company_name"]),
                        "exchange": str(row["exchange"]),
                        "year": year,
                    }
                )
            else:
                downloaded_slots += 1

    expected_slots = len(targets[["company_code"]].drop_duplicates()) * len(YEARS)
    coverage_ratio = round(downloaded_slots / expected_slots, 4) if expected_slots else 0.0
    return {
        "expected_slots": expected_slots,
        "downloaded_slots": downloaded_slots,
        "coverage_ratio": coverage_ratio,
        "missing_slots": missing_slots,
    }



def main() -> None:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    RAW_OFFICIAL_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_manifest_rows()
    inventory_df = pd.DataFrame(rows)
    if inventory_df.empty:
        inventory_df = pd.DataFrame(
            columns=[
                "exchange",
                "company_code",
                "disclosure_company_code",
                "company_name",
                "year",
                "title",
                "published_at",
                "source_url",
                "local_path",
                "file_exists",
                "size_bytes",
                "status",
                "manifest_path",
            ]
        )
    else:
        inventory_df = inventory_df.sort_values(["exchange", "company_code", "year", "published_at"]).reset_index(drop=True)

    inventory_df.to_csv(INVENTORY_PATH, index=False, encoding="utf-8-sig")

    exchange_summary = []
    for exchange, path in MANIFEST_SPECS:
        exchange_df = inventory_df[inventory_df["exchange"] == exchange]
        exchange_summary.append(
            {
                "exchange": exchange,
                "manifest_exists": path.exists(),
                "rows": int(len(exchange_df)),
                "downloaded_rows": int((exchange_df["status"] == "downloaded").sum()) if not exchange_df.empty else 0,
                "file_missing_rows": int(((exchange_df["status"] == "downloaded") & (~exchange_df["file_exists"])).sum()) if not exchange_df.empty else 0,
                "companies": sorted(exchange_df["company_code"].dropna().astype(str).unique().tolist()),
            }
        )

    missing_local_files = []
    if not inventory_df.empty:
        missing_df = inventory_df[(inventory_df["status"] == "downloaded") & (~inventory_df["file_exists"])]
        missing_local_files = missing_df[["exchange", "company_code", "year", "local_path"]].to_dict("records")

    quality = {
        "inventory_rows": int(len(inventory_df)),
        "downloaded_rows": int((inventory_df["status"] == "downloaded").sum()) if not inventory_df.empty else 0,
        "exchanges": exchange_summary,
        "target_coverage": build_target_coverage(inventory_df),
        "missing_local_files": missing_local_files,
        "inventory_path": str(INVENTORY_PATH.relative_to(ROOT)),
    }
    QUALITY_PATH.write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")

    print(INVENTORY_PATH)
    print(QUALITY_PATH)


if __name__ == "__main__":
    main()
