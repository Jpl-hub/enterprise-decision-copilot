from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.data_pipeline_utils import default_report_years, get_target_codes

BSE_LIST_URL = "https://www.bse.cn/disclosureInfoController/companyAnnouncement.do"
BSE_REFERER = "https://www.bse.cn/disclosure/announcement.html"
BSE_STATIC_HOST = "https://www.bse.cn"
TARGET_CODES = get_target_codes("BSE") or ["920047"]
YEARS = default_report_years()
OUT_DIR = Path("data/raw/official/bse/pdfs")
MANIFEST = Path("data/raw/official/bse/report_manifest.json")
OUT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": BSE_REFERER,
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

NEED_FIELDS = [
    "companyCd",
    "companyName",
    "disclosureTitle",
    "disclosurePostTitle",
    "destFilePath",
    "publishDate",
    "xxfcbj",
    "destFilePath",
    "fileExt",
    "xxzrlx",
]


def _parse_jsonp(text: str) -> dict:
    match = re.search(r"^[^(]+\((.*)\)\s*$", text, flags=re.S)
    if not match:
        raise ValueError("failed to parse BSE JSONP response")
    payload = json.loads(match.group(1))
    if isinstance(payload, list) and payload:
        return payload[0]
    if isinstance(payload, dict):
        return payload
    raise ValueError("unexpected BSE response payload")



def _build_payload(code: str, page_index: int) -> list[tuple[str, str]]:
    payload: list[tuple[str, str]] = [
        ("disclosureType[]", "5"),
        ("disclosureSubtype[]", ""),
        ("page", "" if page_index == 0 else str(page_index)),
        ("companyCd", code),
        ("isNewThree", "1"),
        ("keyword", "年度报告"),
        ("xxfcbj[]", "2"),
    ]
    payload.extend(("needFields[]", field) for field in NEED_FIELDS)
    payload.extend(
        [
            ("sortfield", "xxssdq"),
            ("sorttype", "asc"),
        ]
    )
    return payload



def fetch_announcements(code: str, max_pages: int = 6) -> list[dict]:
    rows: list[dict] = []
    for page_index in range(max_pages):
        response = requests.post(
            BSE_LIST_URL,
            params={"callback": "jsonp"},
            headers=HEADERS,
            data=_build_payload(code, page_index),
            timeout=30,
        )
        response.raise_for_status()
        payload = _parse_jsonp(response.text)
        list_info = payload.get("listInfo", {})
        rows.extend(list_info.get("content", []))
        if list_info.get("lastPage", True):
            break
    return rows



def pick_full_annual_report(rows: Iterable[dict], year: int) -> dict | None:
    target = f"{year}年年度报告"
    candidates = []
    for row in rows:
        title = str(row.get("disclosureTitle", ""))
        if target not in title:
            continue
        if "定期报告" not in title or "临时公告" in title:
            continue
        if any(noise in title for noise in ["摘要", "英文", "更正", "取消", "业绩说明会", "预告公告"]):
            continue
        candidates.append(row)
    if not candidates:
        return None
    candidates.sort(key=lambda item: item.get("publishDate", ""), reverse=True)
    return candidates[0]



def download_pdf(dest_file_path: str, target_path: Path) -> None:
    pdf_url = urljoin(BSE_STATIC_HOST, dest_file_path)
    response = requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0", "Referer": BSE_REFERER}, timeout=60)
    response.raise_for_status()
    if not response.content.startswith(b"%PDF"):
        raise RuntimeError(f"non-pdf response from {pdf_url}")
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

            filename = f"{code}_{year}_annual_bse.pdf"
            path = OUT_DIR / filename
            download_pdf(picked["destFilePath"], path)
            manifest.append(
                {
                    "company_code": code,
                    "disclosure_company_code": str(picked.get("companyCd", code)),
                    "company_name": picked.get("companyName"),
                    "year": year,
                    "title": picked.get("disclosureTitle"),
                    "published_at": picked.get("publishDate"),
                    "source_url": urljoin(BSE_STATIC_HOST, picked["destFilePath"]),
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
