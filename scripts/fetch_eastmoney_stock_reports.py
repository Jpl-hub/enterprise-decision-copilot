from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
TARGETS_PATH = ROOT / "data" / "targets.csv"
OUT_PATH = ROOT / "data" / "processed" / "research_reports.csv"
API_URL = "https://reportapi.eastmoney.com/report/list2"
REFERER = "https://data.eastmoney.com/report/stock.jshtml"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": REFERER,
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/json",
}

POSITIVE_RATINGS = {"买入", "增持", "推荐", "强烈推荐", "优于大市", "跑赢行业", "审慎增持"}
NEGATIVE_RATINGS = {"卖出", "减持", "回避", "弱于大市"}


def infer_sentiment(rating: str | None) -> str:
    rating = (rating or "").strip()
    if rating in POSITIVE_RATINGS:
        return "positive"
    if rating in NEGATIVE_RATINGS:
        return "negative"
    return "neutral"


def build_source_url(info_code: str) -> str:
    return f"https://data.eastmoney.com/report/info/{info_code}.html"


def fetch_one_page(code: str, page_no: int, begin_time: str, end_time: str) -> dict:
    payload = {
        "beginTime": begin_time,
        "endTime": end_time,
        "industryCode": "*",
        "ratingChange": None,
        "rating": None,
        "orgCode": None,
        "code": code,
        "rcode": "",
        "pageSize": 50,
        "pageNo": page_no,
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_reports_for_code(code: str, begin_time: str, end_time: str, max_pages: int = 6) -> list[dict]:
    first = fetch_one_page(code, 1, begin_time, end_time)
    total_pages = int(first.get("TotalPage") or 1)
    rows = list(first.get("data") or [])
    for page_no in range(2, min(total_pages, max_pages) + 1):
        payload = fetch_one_page(code, page_no, begin_time, end_time)
        rows.extend(payload.get("data") or [])
    return rows


def build_content(row: dict) -> str:
    parts = [
        f"机构：{row.get('orgSName') or row.get('orgName') or ''}",
        f"评级：{row.get('emRatingName') or row.get('sRatingName') or '未披露'}",
    ]
    if row.get("lastEmRatingName"):
        parts.append(f"上次评级：{row.get('lastEmRatingName')}")
    if row.get("researcher"):
        parts.append(f"作者：{row.get('researcher')}")
    if row.get("indvInduName"):
        parts.append(f"细分行业：{row.get('indvInduName')}")
    if row.get("indvAimPriceT"):
        parts.append(f"目标价上限：{row.get('indvAimPriceT')}")
    if row.get("predictThisYearEps"):
        parts.append(f"今年EPS预测：{row.get('predictThisYearEps')}")
    if row.get("predictNextYearEps"):
        parts.append(f"明年EPS预测：{row.get('predictNextYearEps')}")
    if row.get("predictNextTwoYearEps"):
        parts.append(f"后年EPS预测：{row.get('predictNextTwoYearEps')}")
    parts.append(f"信息编号：{row.get('infoCode')}")
    return "；".join(part for part in parts if part and not part.endswith("："))


def normalize_row(company_code: str, company_name: str, row: dict) -> dict:
    rating = row.get("emRatingName") or row.get("sRatingName") or ""
    rating_change = row.get("ratingChange")
    analyst_view = rating if rating else "未披露评级"
    if rating_change not in (None, "", 3):
        analyst_view = f"{analyst_view}（评级变动:{rating_change}）"
    return {
        "company_code": company_code,
        "company_name": company_name,
        "report_date": str(row.get("publishDate", "")).split(" ")[0],
        "title": row.get("title", ""),
        "analyst_view": analyst_view,
        "institution": row.get("orgSName") or row.get("orgName") or "",
        "sentiment": infer_sentiment(rating),
        "content": build_content(row),
        "source_url": build_source_url(row.get("infoCode", "")),
    }


def main() -> None:
    targets = pd.read_csv(TARGETS_PATH, dtype={"company_code": str})
    begin_time = "2024-01-01"
    end_time = date.today().isoformat()
    records: list[dict] = []

    for _, target in targets.iterrows():
        code = str(target["company_code"])
        company_name = str(target["company_name"])
        rows = fetch_reports_for_code(code, begin_time, end_time)
        for row in rows:
            records.append(normalize_row(code, company_name, row))
        print(code, company_name, len(rows))

    if not records:
        raise RuntimeError("未获取到东方财富个股研报数据")

    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["company_code", "title", "report_date", "institution"]).reset_index(drop=True)
    df = df.sort_values(["company_code", "report_date"], ascending=[True, False]).reset_index(drop=True)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(OUT_PATH)
    print(f"rows={len(df)}")


if __name__ == "__main__":
    main()
