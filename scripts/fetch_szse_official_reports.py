from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.data_pipeline_utils import default_report_years, get_target_codes

SZSE_LIST_URL = "https://www.szse.cn/api/disc/announcement/annList"
SZSE_REFERER = "https://www.szse.cn/disclosure/listed/fixed/index.html"
SZSE_STATIC_HOST = "https://disc.static.szse.cn/download"
TARGET_CODES = get_target_codes("SZSE")
YEARS = default_report_years()
OUT_DIR = Path("data/raw/official/szse/pdfs")
MANIFEST = Path("data/raw/official/szse/report_manifest.json")
OUT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": SZSE_REFERER,
    "X-Request-Type": "ajax",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/json",
}


def fetch_announcements(code: str) -> list[dict]:
    payload = {
        "channelCode": ["fixed_disc"],
        "pageSize": 100,
        "pageNum": 1,
        "stock": [code],
        "bigCategoryId": ["010301"],
    }
    response = requests.post(
        f"{SZSE_LIST_URL}?random=0.123456",
        headers=HEADERS,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("data", [])


def pick_full_annual_report(rows: list[dict], year: int) -> dict | None:
    target_year = str(year)
    candidates = []
    for row in rows:
        title = row.get("title", "")
        if target_year not in title:
            continue
        if "年度报告" not in title:
            continue
        if "摘要" in title or "英文" in title or "更正" in title or "取消" in title:
            continue
        candidates.append(row)
    if not candidates:
        return None
    candidates.sort(key=lambda item: item.get("publishTime", ""), reverse=True)
    return candidates[0]


def download_pdf(attach_path: str, target_path: Path) -> None:
    pdf_url = f"{SZSE_STATIC_HOST}{attach_path}"
    response = requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0", "Referer": SZSE_REFERER}, timeout=60)
    response.raise_for_status()
    if not response.content.startswith(b"%PDF"):
        raise RuntimeError(f"非 PDF 响应: {pdf_url}")
    target_path.write_bytes(response.content)


def main() -> None:
    manifest: list[dict] = []
    for code in TARGET_CODES:
        rows = fetch_announcements(code)
        for year in YEARS:
            picked = pick_full_annual_report(rows, year)
            if picked is None:
                manifest.append({"company_code": code, "year": year, "status": "missing"})
                continue

            filename = f"{code}_{year}_annual_szse.pdf"
            path = OUT_DIR / filename
            download_pdf(picked["attachPath"], path)
            manifest.append(
                {
                    "company_code": code,
                    "company_name": picked.get("secName", [""])[0],
                    "year": year,
                    "title": picked.get("title"),
                    "published_at": str(picked.get("publishTime", "")).split(" ")[0],
                    "source_url": f"{SZSE_STATIC_HOST}{picked['attachPath']}",
                    "local_path": str(path),
                    "size_bytes": path.stat().st_size,
                    "status": "downloaded",
                }
            )
            print(code, year, path.name, path.stat().st_size)

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("manifest:", MANIFEST)


if __name__ == "__main__":
    main()
