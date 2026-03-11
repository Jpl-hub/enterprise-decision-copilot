from __future__ import annotations

import csv
import re
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "data" / "processed" / "macro_indicators.csv"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

SOURCES = {
    "cpi_release_2026_01": "https://www.stats.gov.cn/sj/zxfbhjd/202602/t20260211_1962588.html",
    "cpi_comment_2026_01": "https://www.stats.gov.cn/sj/zxfbhjd/202602/t20260211_1962586.html",
    "income_consumption_2025": "https://www.stats.gov.cn/zwfwck/sjfb/202601/t20260119_1962321.html",
    "bulletin_2025": "https://www.stats.gov.cn/sj/zxfbhjd/202602/t20260228_1962662.html",
}


def fetch_text(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    text = re.sub(r"<[^>]+>", " ", response.text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def extract_float(pattern: str, text: str, label: str) -> float:
    match = re.search(pattern, text, re.S)
    if not match:
        raise RuntimeError(f"未匹配到字段：{label}")
    return float(match.group(1))


def main() -> None:
    texts = {name: fetch_text(url) for name, url in SOURCES.items()}

    rows = [
        {
            "period": "2026-01",
            "indicator_name": "居民消费价格指数同比",
            "indicator_value": extract_float(r"2026年1月份居民消费价格同比上涨\s*([0-9.]+)%", texts["cpi_release_2026_01"], "2026-01 CPI同比"),
            "unit": "%",
            "source_url": SOURCES["cpi_release_2026_01"],
        },
        {
            "period": "2026-01",
            "indicator_name": "医疗保健类价格同比",
            "indicator_value": extract_float(r"衣着、医疗保健价格分别上涨\s*[0-9.]+%\s*和\s*([0-9.]+)%", texts["cpi_release_2026_01"], "2026-01 医疗保健价格同比"),
            "unit": "%",
            "source_url": SOURCES["cpi_release_2026_01"],
        },
        {
            "period": "2026-01",
            "indicator_name": "核心CPI同比",
            "indicator_value": extract_float(r"核心\s*CPI\s*同比上涨\s*([0-9.]+)%", texts["cpi_comment_2026_01"], "2026-01 核心CPI同比"),
            "unit": "%",
            "source_url": SOURCES["cpi_comment_2026_01"],
        },
        {
            "period": "2025",
            "indicator_name": "居民人均消费支出",
            "indicator_value": extract_float(r"全国居民人均消费支出\s*([0-9.]+)\s*元", texts["income_consumption_2025"], "2025 居民人均消费支出"),
            "unit": "元",
            "source_url": SOURCES["income_consumption_2025"],
        },
        {
            "period": "2025",
            "indicator_name": "居民人均医疗保健消费支出",
            "indicator_value": extract_float(r"人均医疗保健消费支出\s*([0-9.]+)\s*元", texts["income_consumption_2025"], "2025 居民人均医疗保健消费支出"),
            "unit": "元",
            "source_url": SOURCES["income_consumption_2025"],
        },
        {
            "period": "2025",
            "indicator_name": "居民人均医疗保健消费支出增长",
            "indicator_value": extract_float(r"人均医疗保健消费支出\s*[0-9.]+\s*元[，,]\s*增长\s*([0-9.]+)%", texts["income_consumption_2025"], "2025 居民人均医疗保健消费支出增长"),
            "unit": "%",
            "source_url": SOURCES["income_consumption_2025"],
        },
        {
            "period": "2025",
            "indicator_name": "国内生产总值增长",
            "indicator_value": extract_float(r"全年国内生产总值.*?比上年增长\s*([0-9.]+)%", texts["bulletin_2025"], "2025 GDP增长"),
            "unit": "%",
            "source_url": SOURCES["bulletin_2025"],
        },
        {
            "period": "2025",
            "indicator_name": "全年居民消费价格同比",
            "indicator_value": extract_float(r"居民消费价格\s*([0-9.\-]+)\s*[0-9.\-]+\s*[0-9.\-]+\s*其中：食品烟酒", texts["bulletin_2025"], "2025 全年居民消费价格同比"),
            "unit": "%",
            "source_url": SOURCES["bulletin_2025"],
        },
        {
            "period": "2025",
            "indicator_name": "全年医疗保健价格同比",
            "indicator_value": extract_float(r"医疗保健\s*([0-9.\-]+)\s*[0-9.\-]+\s*[0-9.\-]+", texts["bulletin_2025"], "2025 全年医疗保健价格同比"),
            "unit": "%",
            "source_url": SOURCES["bulletin_2025"],
        },
        {
            "period": "2025",
            "indicator_name": "医疗卫生机构总数",
            "indicator_value": extract_float(r"年末全国共有医疗卫生机构\s*([0-9.]+)\s*万个", texts["bulletin_2025"], "2025 医疗卫生机构总数"),
            "unit": "万个",
            "source_url": SOURCES["bulletin_2025"],
        },
        {
            "period": "2025",
            "indicator_name": "医院数量",
            "indicator_value": extract_float(r"其中医院\s*([0-9.]+)\s*万个", texts["bulletin_2025"], "2025 医院数量"),
            "unit": "万个",
            "source_url": SOURCES["bulletin_2025"],
        },
    ]

    with OUT_PATH.open("w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.DictWriter(fp, fieldnames=["period", "indicator_name", "indicator_value", "unit", "source_url"])
        writer.writeheader()
        writer.writerows(rows)

    print(OUT_PATH)
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()
