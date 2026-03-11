from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "data" / "processed" / "industry_reports.csv"
BOARD_API_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
REPORT_API_URL = "https://reportapi.eastmoney.com/report/list"
REFERER = "https://data.eastmoney.com/report/industry.jshtml"

TARGET_KEYWORDS = ["医药", "医疗", "制药", "药店", "CXO", "中药", "生物"]
HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": REFERER}

POSITIVE_RATINGS = {"买入", "增持", "推荐", "看好", "优于大市", "跑赢行业"}
NEGATIVE_RATINGS = {"卖出", "减持", "回避", "弱于大市"}


def infer_sentiment(rating: str | None) -> str:
    rating = (rating or "").strip()
    if rating in POSITIVE_RATINGS:
        return "positive"
    if rating in NEGATIVE_RATINGS:
        return "negative"
    return "neutral"


def load_medical_industries() -> pd.DataFrame:
    params = {
        "reportName": "RPT_EMBOARD_ALL",
        "columns": "BOARD_CODE,BOARD_NAME,BOARD_CODE_BK,BOARD_LEVEL,BOARD_TYPE,BOARD_TYPE_NAME,FIRST_LETTER",
        "quoteColumns": "",
        "sortColumns": "FIRST_LETTER",
        "sortTypes": "1",
        "source": "WEB",
        "client": "WEB",
        "filter": "(BOARD_TYPE=2)",
        "pageNumber": "1",
        "pageSize": "5000",
    }
    response = requests.get(BOARD_API_URL, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    rows = response.json()["result"]["data"]
    df = pd.DataFrame(rows)
    mask = df["BOARD_NAME"].astype(str).apply(lambda name: any(keyword in name for keyword in TARGET_KEYWORDS))
    return df.loc[mask, ["BOARD_CODE", "BOARD_NAME"]].drop_duplicates().reset_index(drop=True)


def fetch_reports_for_industry(industry_code: str, begin_time: str, end_time: str, max_pages: int = 4) -> list[dict]:
    records: list[dict] = []
    for page_no in range(1, max_pages + 1):
        params = {
            "cb": f"datatable{industry_code}{page_no}",
            "industryCode": industry_code,
            "pageSize": 50,
            "industry": "*",
            "rating": "*",
            "ratingChange": "*",
            "beginTime": begin_time,
            "endTime": end_time,
            "pageNo": page_no,
            "fields": "",
            "qType": 1,
            "orgCode": "",
            "rcode": "",
            "_": "1772958056931",
        }
        response = requests.get(REPORT_API_URL, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()
        match = re.search(r"^[^(]+\((.*)\)$", response.text, re.S)
        if not match:
            raise RuntimeError(f"无法解析行业研报 JSONP: {industry_code} page {page_no}")
        payload = json.loads(match.group(1))
        rows = payload.get("data") or []
        if not rows:
            break
        records.extend(rows)
        if page_no >= int(payload.get("TotalPage") or 1):
            break
    return records


def build_source_url(info_code: str) -> str:
    return f"https://data.eastmoney.com/report/info/{info_code}.html"


def build_content(row: dict) -> str:
    parts = [
        f"机构：{row.get('orgSName') or row.get('orgName') or ''}",
        f"行业：{row.get('industryName') or ''}",
        f"评级：{row.get('emRatingName') or row.get('sRatingName') or '未披露'}",
    ]
    if row.get("researcher"):
        parts.append(f"作者：{row.get('researcher')}")
    if row.get("attachPages"):
        parts.append(f"页数：{row.get('attachPages')}")
    parts.append(f"信息编号：{row.get('infoCode')}")
    return "；".join(part for part in parts if part and not part.endswith("："))


def normalize_row(board_name: str, row: dict) -> dict:
    rating = row.get("emRatingName") or row.get("sRatingName") or ""
    return {
        "industry_code": str(row.get("industryCode") or ""),
        "industry_name": board_name or row.get("industryName") or "",
        "report_date": str(row.get("publishDate", "")).split(" ")[0],
        "title": row.get("title", ""),
        "institution": row.get("orgSName") or row.get("orgName") or "",
        "sentiment": infer_sentiment(rating),
        "content": build_content(row),
        "source_url": build_source_url(row.get("infoCode", "")),
    }


def main() -> None:
    begin_time = "2024-01-01"
    end_time = date.today().isoformat()
    boards = load_medical_industries()
    records: list[dict] = []

    for _, board in boards.iterrows():
        code = str(board["BOARD_CODE"])
        name = str(board["BOARD_NAME"])
        rows = fetch_reports_for_industry(code, begin_time, end_time)
        for row in rows:
            records.append(normalize_row(name, row))
        print(code, name, len(rows))

    if not records:
        raise RuntimeError("未获取到行业研报数据")

    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["industry_code", "title", "report_date", "institution"]).reset_index(drop=True)
    df = df.sort_values(["industry_name", "report_date"], ascending=[True, False]).reset_index(drop=True)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(OUT_PATH)
    print(f"rows={len(df)}")


if __name__ == "__main__":
    main()
