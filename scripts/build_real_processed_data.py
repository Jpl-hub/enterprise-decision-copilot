from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

TARGETS = {
    '600276': {
        'exchange': 'SSE',
        'industry': '医药生物',
        'segment': '创新药',
        'source_url': 'https://static.cninfo.com.cn/finalpage/2025-03-31/1222961962.PDF',
        'published_at': '2025-03-31',
    },
    '300760': {
        'exchange': 'SZSE',
        'industry': '医药生物',
        'segment': '医疗器械',
        'source_url': 'https://static.cninfo.com.cn/finalpage/2025-04-29/1223371149.PDF',
        'published_at': '2025-04-29',
    },
    '300015': {
        'exchange': 'SZSE',
        'industry': '医药生物',
        'segment': '医疗服务',
        'source_url': 'https://static.cninfo.com.cn/finalpage/2025-04-25/1223271221.PDF',
        'published_at': '2025-04-25',
    },
    '603939': {
        'exchange': 'SSE',
        'industry': '医药生物',
        'segment': '连锁药房',
        'source_url': 'https://static.cninfo.com.cn/finalpage/2025-05-22/1223626059.PDF',
        'published_at': '2025-05-22',
    },
    '688271': {
        'exchange': 'SSE',
        'industry': '医药生物',
        'segment': '医疗器械',
        'source_url': 'https://static.cninfo.com.cn/finalpage/2025-04-29/1223362977.PDF',
        'published_at': '2025-04-29',
    },
    '603259': {
        'exchange': 'SSE',
        'industry': '医药生物',
        'segment': 'CXO',
        'source_url': 'https://static.cninfo.com.cn/finalpage/2025-03-18/1222822845.PDF',
        'published_at': '2025-03-18',
    },
}

CACHE_FILES = {
    '600276': '600276_2024_annual_cninfo.json',
    '300760': '300760_2024_annual_summary_cninfo.json',
    '300015': '300015_2024_annual_cninfo.json',
    '603939': '603939_2024_agm_financials_cninfo.json',
    '688271': '688271_2024_annual_cninfo.json',
    '603259': '603259_2024_annual_summary_cninfo.json',
}


def load_financials() -> pd.DataFrame:
    rows = []
    for code, meta in TARGETS.items():
        data = json.loads(Path('data/cache', CACHE_FILES[code]).read_text(encoding='utf-8'))
        revenue = data.get('revenue_million')
        profit = data.get('net_profit_million')
        net_margin = data.get('net_margin_pct')
        if net_margin is None and revenue and profit:
            net_margin = round(profit / revenue * 100, 2)
        rows.append(
            {
                'company_code': code,
                'company_name': data.get('company_name'),
                'report_year': data.get('report_year'),
                'revenue_million': revenue,
                'net_profit_million': profit,
                'gross_margin_pct': data.get('gross_margin_pct'),
                'net_margin_pct': net_margin,
                'rd_ratio_pct': data.get('rd_ratio_pct'),
                'debt_ratio_pct': data.get('debt_ratio_pct'),
                'current_ratio': data.get('current_ratio'),
                'cash_to_short_debt': data.get('cash_to_short_debt'),
                'inventory_turnover': data.get('inventory_turnover'),
                'receivable_turnover': data.get('receivable_turnover'),
                'operating_cashflow_million': data.get('operating_cashflow_million'),
                'roe_pct': data.get('roe_pct'),
                'source_url': meta['source_url'],
                'published_at': meta['published_at'],
            }
        )
    return pd.DataFrame(rows)


def load_research_summaries() -> pd.DataFrame:
    url = 'https://datacenter-web.eastmoney.com/api/data/v1/get'
    rows = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for code, meta in TARGETS.items():
        market = 'SZ' if meta['exchange'] == 'SZSE' else 'SH'
        params = {
            'reportName': 'RPT_WEB_RESPREDICT',
            'columns': 'ALL',
            'filter': f'(SECUCODE="{code}.{market}")',
            'pageNumber': 1,
            'pageSize': 10,
            'source': 'WEB',
            'client': 'WEB',
        }
        response = requests.get(url, params=params, timeout=30, headers=headers)
        response.raise_for_status()
        payload = response.json()
        item = payload['result']['data'][0]
        buy_num = item.get('RATING_BUY_NUM') or 0
        add_num = item.get('RATING_ADD_NUM') or 0
        neutral_num = item.get('RATING_NEUTRAL_NUM') or 0
        reduce_num = item.get('RATING_REDUCE_NUM') or 0
        sale_num = item.get('RATING_SALE_NUM') or 0
        sentiment = 'positive' if buy_num + add_num >= max(neutral_num + reduce_num + sale_num, 1) else 'neutral'
        rows.append(
            {
                'company_code': code,
                'company_name': item.get('SECURITY_NAME_ABBR') or code,
                'report_date': '2026-03-08',
                'title': '东方财富机构评级汇总',
                'analyst_view': f"买入{buy_num}家，增持{add_num}家",
                'institution': '东方财富研报中心',
                'sentiment': sentiment,
                'content': (
                    f"截至2026年3月8日，东方财富机构评级汇总显示，{item.get('SECURITY_NAME_ABBR')}"
                    f"共有{item.get('RATING_ORG_NUM')}家机构覆盖，其中买入{buy_num}家、增持{add_num}家、"
                    f"中性{neutral_num if neutral_num is not None else 0}家、减持{reduce_num if reduce_num is not None else 0}家、卖出{sale_num if sale_num is not None else 0}家。"
                    f"2025年一致预期EPS为{item.get('EPS2')}，2026年一致预期EPS为{item.get('EPS3')}。"
                ),
                'source_url': 'https://data.eastmoney.com/report/stock.jshtml',
            }
        )
    return pd.DataFrame(rows)


def load_macro() -> pd.DataFrame:
    rows = [
        {
            'period': '2024',
            'indicator_name': '全年居民消费价格指数同比',
            'indicator_value': 0.2,
            'unit': '%',
            'source_url': 'https://www.stats.gov.cn/sj/zxfb/202501/t20250117_1957976.html',
        },
        {
            'period': '2024',
            'indicator_name': '全年核心CPI同比',
            'indicator_value': 0.5,
            'unit': '%',
            'source_url': 'https://www.stats.gov.cn/sj/zxfb/202501/t20250117_1957976.html',
        },
        {
            'period': '2024',
            'indicator_name': '全年居民人均医疗保健消费支出',
            'indicator_value': 2547,
            'unit': '元',
            'source_url': 'https://www.stats.gov.cn/sj/zxfb/202501/t20250117_1957979.html',
        },
        {
            'period': '2024',
            'indicator_name': '全年居民人均医疗保健消费支出增长',
            'indicator_value': 3.6,
            'unit': '%',
            'source_url': 'https://www.stats.gov.cn/sj/zxfb/202501/t20250117_1957979.html',
        },
    ]
    return pd.DataFrame(rows)


def main() -> None:
    processed = Path('data/processed')
    processed.mkdir(parents=True, exist_ok=True)

    financials = load_financials()
    reports = load_research_summaries()
    macro = load_macro()

    financials.to_csv(processed / 'financial_features.csv', index=False, encoding='utf-8-sig')
    reports.to_csv(processed / 'research_reports.csv', index=False, encoding='utf-8-sig')
    macro.to_csv(processed / 'macro_indicators.csv', index=False, encoding='utf-8-sig')

    print('financial_features', len(financials))
    print('research_reports', len(reports))
    print('macro_indicators', len(macro))


if __name__ == '__main__':
    main()
