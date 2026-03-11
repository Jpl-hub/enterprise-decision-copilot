from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
TARGETS_PATH = ROOT / 'data' / 'targets.csv'
OUT_PATH = ROOT / 'data' / 'processed' / 'industry_company_universe.csv'
RAW_OUT_PATH = ROOT / 'data' / 'processed' / 'industry_company_universe_reports.csv'
QUALITY_PATH = ROOT / 'data' / 'quality' / 'industry_company_universe_quality.json'
API_URL = 'https://reportapi.eastmoney.com/report/list2'
REFERER = 'https://data.eastmoney.com/report/stock.jshtml'

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': REFERER,
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Content-Type': 'application/json',
}

TARGET_SUBINDUSTRIES = [
    '中药Ⅱ',
    '化学制药',
    '医疗美容',
    '生物制品',
    '医药商业',
    '医疗服务',
    '医疗器械',
]

MARKET_TO_EXCHANGE = {
    'SHANGHAI': 'SSE',
    'SHENZHEN': 'SZSE',
    'BEIJING': 'BSE',
}

POSITIVE_RATINGS = {'买入', '增持', '推荐', '强烈推荐', '优于大市', '跑赢行业', '审慎增持'}
NEGATIVE_RATINGS = {'卖出', '减持', '回避', '弱于大市'}


def infer_sentiment(rating: str | None) -> str:
    rating = (rating or '').strip()
    if rating in POSITIVE_RATINGS:
        return 'positive'
    if rating in NEGATIVE_RATINGS:
        return 'negative'
    return 'neutral'


def build_source_url(info_code: str) -> str:
    return f'https://data.eastmoney.com/report/info/{info_code}.html'


def fetch_page(*, industry_code: str, page_no: int, begin_time: str, end_time: str, company_code: str = '') -> dict:
    payload = {
        'beginTime': begin_time,
        'endTime': end_time,
        'industryCode': industry_code,
        'ratingChange': None,
        'rating': None,
        'orgCode': None,
        'code': company_code,
        'rcode': '',
        'pageSize': 50,
        'pageNo': page_no,
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def discover_industry_codes(begin_time: str, end_time: str, target_frame: pd.DataFrame, max_pages: int = 16) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for page_no in range(1, max_pages + 1):
        payload = fetch_page(industry_code='*', page_no=page_no, begin_time=begin_time, end_time=end_time)
        rows = payload.get('data') or []
        if not rows:
            break
        for row in rows:
            industry_name = str(row.get('indvInduName') or '').strip()
            industry_code = str(row.get('indvInduCode') or '').strip()
            if industry_name in TARGET_SUBINDUSTRIES and industry_code and industry_name not in mapping:
                mapping[industry_name] = industry_code
        if len(mapping) == len(TARGET_SUBINDUSTRIES):
            break
        total_pages = int(payload.get('TotalPage') or 1)
        if page_no >= total_pages:
            break

    missing = [name for name in TARGET_SUBINDUSTRIES if name not in mapping]
    if missing and not target_frame.empty:
        for _, target in target_frame.iterrows():
            target_code = str(target.get('company_code') or '').strip()
            if not target_code:
                continue
            payload = fetch_page(industry_code='*', page_no=1, begin_time=begin_time, end_time=end_time, company_code=target_code)
            rows = payload.get('data') or []
            for row in rows:
                industry_name = str(row.get('indvInduName') or '').strip()
                industry_code = str(row.get('indvInduCode') or '').strip()
                if industry_name in TARGET_SUBINDUSTRIES and industry_code and industry_name not in mapping:
                    mapping[industry_name] = industry_code
            missing = [name for name in TARGET_SUBINDUSTRIES if name not in mapping]
            if not missing:
                break
    return mapping


def fetch_reports_for_industry(industry_code: str, begin_time: str, end_time: str, max_pages: int = 10) -> list[dict]:
    first = fetch_page(industry_code=industry_code, page_no=1, begin_time=begin_time, end_time=end_time)
    total_pages = int(first.get('TotalPage') or 1)
    rows = list(first.get('data') or [])
    for page_no in range(2, min(total_pages, max_pages) + 1):
        payload = fetch_page(industry_code=industry_code, page_no=page_no, begin_time=begin_time, end_time=end_time)
        rows.extend(payload.get('data') or [])
    return rows


def normalize_report_row(row: dict, target_codes: set[str]) -> dict:
    rating = row.get('emRatingName') or row.get('sRatingName') or ''
    company_code = str(row.get('stockCode') or '').strip()
    market = str(row.get('market') or '').strip().upper()
    exchange = MARKET_TO_EXCHANGE.get(market, market or '')
    return {
        'company_code': company_code,
        'company_name': str(row.get('stockName') or '').strip(),
        'exchange': exchange,
        'market': market,
        'industry_code': str(row.get('indvInduCode') or '').strip(),
        'industry_name': str(row.get('indvInduName') or '').strip(),
        'report_date': str(row.get('publishDate') or '').split(' ')[0],
        'title': str(row.get('title') or '').strip(),
        'institution': str(row.get('orgSName') or row.get('orgName') or '').strip(),
        'sentiment': infer_sentiment(rating),
        'source_url': build_source_url(str(row.get('infoCode') or '').strip()),
        'in_target_pool': company_code in target_codes,
    }


def build_company_universe(raw_reports: pd.DataFrame) -> pd.DataFrame:
    if raw_reports.empty:
        return raw_reports
    sorted_reports = raw_reports.sort_values(['company_code', 'report_date', 'title'], ascending=[True, False, True]).reset_index(drop=True)
    latest_rows = sorted_reports.drop_duplicates(subset=['company_code'], keep='first').copy()

    grouped = sorted_reports.groupby(['company_code', 'company_name', 'exchange', 'market', 'industry_code', 'industry_name'], dropna=False)
    summary = grouped.agg(
        report_count=('title', 'count'),
        institution_count=('institution', pd.Series.nunique),
        positive_count=('sentiment', lambda s: int((s == 'positive').sum())),
        neutral_count=('sentiment', lambda s: int((s == 'neutral').sum())),
        negative_count=('sentiment', lambda s: int((s == 'negative').sum())),
        latest_report_date=('report_date', 'max'),
        earliest_report_date=('report_date', 'min'),
        in_target_pool=('in_target_pool', 'max'),
    ).reset_index()

    latest_rows = latest_rows[['company_code', 'title', 'source_url']].rename(columns={'title': 'latest_report_title', 'source_url': 'latest_source_url'})
    summary = summary.merge(latest_rows, on='company_code', how='left')
    summary['report_count'] = summary['report_count'].astype(int)
    summary['institution_count'] = summary['institution_count'].astype(int)
    summary['positive_count'] = summary['positive_count'].astype(int)
    summary['neutral_count'] = summary['neutral_count'].astype(int)
    summary['negative_count'] = summary['negative_count'].astype(int)
    summary['in_target_pool'] = summary['in_target_pool'].astype(bool)
    return summary.sort_values(['report_count', 'institution_count', 'company_code'], ascending=[False, False, True]).reset_index(drop=True)


def main() -> None:
    begin_time = '2024-01-01'
    end_time = date.today().isoformat()
    targets = pd.read_csv(TARGETS_PATH, dtype={'company_code': str})
    target_codes = set(targets['company_code'].astype(str).tolist())

    discovered_codes = discover_industry_codes(begin_time, end_time, targets)
    if not discovered_codes:
        raise RuntimeError('未发现目标医药子行业代码，无法构建行业公司池')

    records: list[dict] = []
    fetched_industries: list[dict] = []
    for industry_name in TARGET_SUBINDUSTRIES:
        industry_code = discovered_codes.get(industry_name)
        if not industry_code:
            continue
        rows = fetch_reports_for_industry(industry_code, begin_time, end_time)
        normalized = [normalize_report_row(row, target_codes) for row in rows if str(row.get('stockCode') or '').strip()]
        records.extend(normalized)
        fetched_industries.append({'industry_name': industry_name, 'industry_code': industry_code, 'report_rows': len(normalized)})
        print(industry_code, industry_name, len(normalized))

    if not records:
        raise RuntimeError('未获取到行业公司池数据')

    raw_df = pd.DataFrame(records)
    raw_df = raw_df.drop_duplicates(subset=['company_code', 'report_date', 'title', 'institution']).reset_index(drop=True)
    raw_df = raw_df.sort_values(['industry_name', 'company_code', 'report_date'], ascending=[True, True, False]).reset_index(drop=True)

    summary_df = build_company_universe(raw_df)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUALITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(OUT_PATH, index=False, encoding='utf-8-sig')
    raw_df.to_csv(RAW_OUT_PATH, index=False, encoding='utf-8-sig')

    quality = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'source': API_URL,
        'begin_time': begin_time,
        'end_time': end_time,
        'industry_code_map': discovered_codes,
        'industries': fetched_industries,
        'company_count': int(summary_df['company_code'].nunique()),
        'industry_count': int(summary_df['industry_name'].nunique()),
        'report_count': int(len(raw_df)),
        'target_overlap_count': int(summary_df[summary_df['in_target_pool']]['company_code'].nunique()),
        'top_companies': summary_df[['company_code', 'company_name', 'report_count', 'industry_name']].head(10).to_dict('records'),
    }
    QUALITY_PATH.write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding='utf-8')

    print(OUT_PATH)
    print(RAW_OUT_PATH)
    print(QUALITY_PATH)
    print(f"companies={len(summary_df)}, reports={len(raw_df)}")


if __name__ == '__main__':
    main()
