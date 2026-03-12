from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.data_pipeline_utils import load_targets


OUT_PATH = ROOT / "data" / "processed" / "official_periodic_snapshots.csv"
QUALITY_PATH = ROOT / "data" / "quality" / "official_periodic_snapshot_quality.json"

SSE_LIST_URL = "https://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do"
SSE_REFERER = "https://www.sse.com.cn/disclosure/listedinfo/regular/"
SZSE_LIST_URL = "https://www.szse.cn/api/disc/announcement/annList"
SZSE_REFERER = "https://www.szse.cn/disclosure/listed/fixed/index.html"
BSE_LIST_URL = "https://www.bse.cn/disclosureInfoController/companyAnnouncement.do"
BSE_REFERER = "https://www.bse.cn/disclosure/announcement.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

PERIOD_SPECS = [
    {
        "period_type": "annual",
        "label": "年报",
        "sse_keyword": "年度报告",
        "bse_keyword": "年度报告",
        "aliases": ["年度报告", "年报"],
    },
    {
        "period_type": "q1",
        "label": "一季报",
        "sse_keyword": "第一季度报告",
        "bse_keyword": "第一季度报告",
        "aliases": ["第一季度报告", "一季度报告", "1季度报告", "一季报"],
    },
    {
        "period_type": "h1",
        "label": "半年报",
        "sse_keyword": "半年度报告",
        "bse_keyword": "半年度报告",
        "aliases": ["半年度报告", "半年报", "中报"],
    },
    {
        "period_type": "q3",
        "label": "三季报",
        "sse_keyword": "第三季度报告",
        "bse_keyword": "第三季度报告",
        "aliases": ["第三季度报告", "三季度报告", "3季度报告", "三季报"],
    },
]

NOISE_TOKENS = ("摘要", "英文", "更正", "取消", "提示性公告", "业绩预告", "说明会", "公告")
PERIOD_PATTERNS = {
    "annual": re.compile(r"(20\d{2}年)?年度报告"),
    "q1": re.compile(r"(第一季度报告|一季度报告|1季度报告|一季报)"),
    "h1": re.compile(r"(半年度报告|半年报|中报)"),
    "q3": re.compile(r"(第三季度报告|三季度报告|3季度报告|三季报)"),
}


@dataclass(slots=True)
class SnapshotRecord:
    exchange: str
    company_code: str
    company_name: str
    period_type: str
    period_label: str
    report_year: int | None
    title: str
    published_at: str
    source_url: str

    def as_dict(self) -> dict:
        return {
            "exchange": self.exchange,
            "company_code": self.company_code,
            "company_name": self.company_name,
            "period_type": self.period_type,
            "period_label": self.period_label,
            "report_year": self.report_year,
            "title": self.title,
            "published_at": self.published_at,
            "source_url": self.source_url,
        }


def _title_matches_period(title: str, period_type: str, aliases: Iterable[str]) -> bool:
    normalized = str(title or "").strip()
    if not normalized:
        return False
    if any(token in normalized for token in NOISE_TOKENS):
        return False
    pattern = PERIOD_PATTERNS.get(period_type)
    if pattern is not None and not pattern.search(normalized):
        return False
    if period_type == "annual" and any(token in normalized for token in ("半年度", "第一季度", "一季度", "第三季度", "三季度")):
        return False
    return any(alias in normalized for alias in aliases)


def _extract_report_year(title: str) -> int | None:
    match = re.search(r"(20\d{2})年", str(title or ""))
    if not match:
        return None
    return int(match.group(1))


def _sort_key(record: dict) -> tuple[int, str]:
    return (int(record.get("report_year") or 0), str(record.get("published_at") or ""))


def _flatten_sse_groups(groups: list) -> list[dict]:
    rows: list[dict] = []
    for group in groups:
        if isinstance(group, list):
            rows.extend(group)
        elif isinstance(group, dict):
            rows.append(group)
    return rows


def _parse_bse_jsonp(text: str) -> dict:
    match = re.search(r"^[^(]+\((.*)\)\s*$", text, flags=re.S)
    if not match:
        raise ValueError("failed to parse BSE JSONP response")
    payload = json.loads(match.group(1))
    if isinstance(payload, list) and payload:
        return payload[0]
    if isinstance(payload, dict):
        return payload
    raise ValueError("unexpected BSE payload")


def fetch_sse_rows(code: str, keyword: str, max_pages: int = 4) -> list[dict]:
    rows: list[dict] = []
    headers = {**HEADERS, "Referer": SSE_REFERER}
    for page_no in range(1, max_pages + 1):
        response = requests.get(
            SSE_LIST_URL,
            params={
                "jsonCallBack": "jsonpCallback",
                "isPagination": "true",
                "pageHelp.pageSize": 25,
                "pageHelp.cacheSize": 1,
                "pageHelp.pageNo": page_no,
                "SECURITY_CODE": code,
                "TITLE": keyword,
                "BULLETIN_TYPE": "",
                "stockType": "",
                "_": "1741410000000",
            },
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        match = re.search(r"jsonpCallback\((.*)\)$", response.text)
        if not match:
            raise ValueError(f"failed to parse SSE JSONP for {code} page {page_no}")
        payload = json.loads(match.group(1))
        page_rows = _flatten_sse_groups((payload.get("pageHelp") or {}).get("data") or [])
        rows.extend(page_rows)
        if page_no >= int((payload.get("pageHelp") or {}).get("pageCount") or 1):
            break
    return rows


def fetch_szse_rows(code: str, max_pages: int = 3) -> list[dict]:
    rows: list[dict] = []
    headers = {
        **HEADERS,
        "Referer": SZSE_REFERER,
        "X-Request-Type": "ajax",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/json",
    }
    page_size = 100
    for page_num in range(1, max_pages + 1):
        response = requests.post(
            f"{SZSE_LIST_URL}?random=0.123456",
            headers=headers,
            json={
                "channelCode": ["fixed_disc"],
                "pageSize": page_size,
                "pageNum": page_num,
                "stock": [code],
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        page_rows = payload.get("data", [])
        if not page_rows:
            break
        rows.extend(page_rows)
        announce_count = int(payload.get("announceCount") or 0)
        if len(rows) >= announce_count or len(page_rows) < page_size:
            break
    return rows


def fetch_bse_rows(code: str, keyword: str, max_pages: int = 4) -> list[dict]:
    need_fields = [
        "companyCd",
        "companyName",
        "disclosureTitle",
        "destFilePath",
        "publishDate",
        "xxfcbj",
        "fileExt",
        "xxzrlx",
    ]
    rows: list[dict] = []
    for page_index in range(max_pages):
        response = requests.post(
            BSE_LIST_URL,
            params={"callback": "jsonp"},
            headers={
                **HEADERS,
                "Referer": BSE_REFERER,
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            data=[
                ("disclosureType[]", "5"),
                ("disclosureSubtype[]", ""),
                ("page", "" if page_index == 0 else str(page_index)),
                ("companyCd", code),
                ("isNewThree", "1"),
                ("keyword", keyword),
                ("xxfcbj[]", "2"),
                *[("needFields[]", field) for field in need_fields],
                ("sortfield", "xxssdq"),
                ("sorttype", "asc"),
            ],
            timeout=30,
        )
        response.raise_for_status()
        payload = _parse_bse_jsonp(response.text)
        list_info = payload.get("listInfo", {})
        rows.extend(list_info.get("content", []))
        if list_info.get("lastPage", True):
            break
    return rows


def pick_sse_snapshot(code: str, company_name: str, period_spec: dict) -> SnapshotRecord | None:
    rows = fetch_sse_rows(code, str(period_spec["sse_keyword"]))
    candidates = []
    for row in rows:
        title = str(row.get("TITLE") or "")
        if not _title_matches_period(title, str(period_spec["period_type"]), period_spec["aliases"]):
            continue
        candidates.append(
            {
                "title": title,
                "published_at": str(row.get("SSEDATE") or ""),
                "report_year": _extract_report_year(title),
                "source_url": f"https://static.sse.com.cn{row.get('URL')}",
            }
        )
    if not candidates:
        return None
    winner = sorted(candidates, key=_sort_key, reverse=True)[0]
    return SnapshotRecord(
        exchange="SSE",
        company_code=code,
        company_name=company_name,
        period_type=str(period_spec["period_type"]),
        period_label=str(period_spec["label"]),
        report_year=winner["report_year"],
        title=winner["title"],
        published_at=winner["published_at"],
        source_url=winner["source_url"],
    )


def pick_szse_snapshot(code: str, company_name: str, rows: list[dict], period_spec: dict) -> SnapshotRecord | None:
    candidates = []
    for row in rows:
        title = str(row.get("title") or "")
        if not _title_matches_period(title, str(period_spec["period_type"]), period_spec["aliases"]):
            continue
        attach_path = str(row.get("attachPath") or "")
        if not attach_path:
            continue
        candidates.append(
            {
                "title": title,
                "published_at": str(row.get("publishTime") or "").split(" ")[0],
                "report_year": _extract_report_year(title),
                "source_url": f"https://disc.static.szse.cn/download{attach_path}",
            }
        )
    if not candidates:
        return None
    winner = sorted(candidates, key=_sort_key, reverse=True)[0]
    return SnapshotRecord(
        exchange="SZSE",
        company_code=code,
        company_name=company_name,
        period_type=str(period_spec["period_type"]),
        period_label=str(period_spec["label"]),
        report_year=winner["report_year"],
        title=winner["title"],
        published_at=winner["published_at"],
        source_url=winner["source_url"],
    )


def pick_bse_snapshot(code: str, company_name: str, period_spec: dict) -> SnapshotRecord | None:
    rows = fetch_bse_rows(code, str(period_spec["bse_keyword"]))
    candidates = []
    for row in rows:
        title = str(row.get("disclosureTitle") or "")
        if not _title_matches_period(title, str(period_spec["period_type"]), period_spec["aliases"]):
            continue
        path = str(row.get("destFilePath") or "")
        if not path:
            continue
        candidates.append(
            {
                "title": title,
                "published_at": str(row.get("publishDate") or ""),
                "report_year": _extract_report_year(title),
                "source_url": f"https://www.bse.cn{path}",
            }
        )
    if not candidates:
        return None
    winner = sorted(candidates, key=_sort_key, reverse=True)[0]
    return SnapshotRecord(
        exchange="BSE",
        company_code=code,
        company_name=company_name,
        period_type=str(period_spec["period_type"]),
        period_label=str(period_spec["label"]),
        report_year=winner["report_year"],
        title=winner["title"],
        published_at=winner["published_at"],
        source_url=winner["source_url"],
    )


def build_quality(frame: pd.DataFrame, targets: pd.DataFrame) -> dict:
    target_count = int(targets["company_code"].astype(str).nunique()) if not targets.empty else 0
    period_summaries = []
    missing_slots: list[dict] = []
    for period_spec in PERIOD_SPECS:
        period_type = str(period_spec["period_type"])
        scoped = frame[frame["period_type"] == period_type].copy() if not frame.empty else pd.DataFrame()
        covered = int(scoped["company_code"].astype(str).nunique()) if not scoped.empty else 0
        coverage_ratio = round(covered / target_count, 4) if target_count else 0.0
        latest_row = (
            scoped.sort_values(["report_year", "published_at"], ascending=[False, False]).head(1).to_dict("records")[0]
            if not scoped.empty
            else None
        )
        if not targets.empty:
            covered_codes = set(scoped["company_code"].astype(str).tolist()) if not scoped.empty else set()
            for row in targets[["company_code", "company_name", "exchange"]].drop_duplicates().to_dict("records"):
                if str(row["company_code"]) not in covered_codes:
                    missing_slots.append(
                        {
                            "company_code": str(row["company_code"]),
                            "company_name": str(row["company_name"]),
                            "exchange": str(row["exchange"]),
                            "period_type": period_type,
                            "period_label": str(period_spec["label"]),
                        }
                    )
        period_summaries.append(
            {
                "period_type": period_type,
                "period_label": str(period_spec["label"]),
                "covered_companies": covered,
                "coverage_ratio": coverage_ratio,
                "latest_report_year": int(latest_row["report_year"]) if latest_row and latest_row.get("report_year") else None,
                "latest_published_at": latest_row.get("published_at") if latest_row else None,
                "latest_company_name": latest_row.get("company_name") if latest_row else None,
            }
        )

    latest_row = (
        frame.sort_values(["published_at", "report_year"], ascending=[False, False]).head(1).to_dict("records")[0]
        if not frame.empty
        else None
    )
    return {
        "rows": int(len(frame)),
        "target_count": target_count,
        "period_summaries": period_summaries,
        "latest_disclosure": latest_row,
        "missing_slots": missing_slots,
    }


def main() -> None:
    targets = load_targets()
    records: list[dict] = []

    if not targets.empty:
        for exchange in ("SSE", "SZSE", "BSE"):
            scoped_targets = targets[targets["exchange"].astype(str).str.upper() == exchange].copy()
            if scoped_targets.empty:
                continue
            for row in scoped_targets[["company_code", "company_name"]].drop_duplicates().to_dict("records"):
                code = str(row["company_code"])
                company_name = str(row["company_name"])
                if exchange == "SSE":
                    for period_spec in PERIOD_SPECS:
                        item = pick_sse_snapshot(code, company_name, period_spec)
                        if item is not None:
                            records.append(item.as_dict())
                elif exchange == "SZSE":
                    rows = fetch_szse_rows(code)
                    for period_spec in PERIOD_SPECS:
                        item = pick_szse_snapshot(code, company_name, rows, period_spec)
                        if item is not None:
                            records.append(item.as_dict())
                else:
                    for period_spec in PERIOD_SPECS:
                        item = pick_bse_snapshot(code, company_name, period_spec)
                        if item is not None:
                            records.append(item.as_dict())

    frame = pd.DataFrame(records)
    if frame.empty:
        frame = pd.DataFrame(
            columns=[
                "exchange",
                "company_code",
                "company_name",
                "period_type",
                "period_label",
                "report_year",
                "title",
                "published_at",
                "source_url",
            ]
        )
    else:
        frame = frame.sort_values(
            ["exchange", "company_code", "period_type", "report_year", "published_at"],
            ascending=[True, True, True, False, False],
        ).reset_index(drop=True)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUALITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    QUALITY_PATH.write_text(
        json.dumps(build_quality(frame, targets), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(OUT_PATH)
    print(QUALITY_PATH)


if __name__ == "__main__":
    main()
