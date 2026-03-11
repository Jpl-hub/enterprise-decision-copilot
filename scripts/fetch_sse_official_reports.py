from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.data_pipeline_utils import default_report_years, get_target_codes

SSE_LIST_URL = 'https://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do'
SSE_REFERER = 'https://www.sse.com.cn/disclosure/listedinfo/regular/'
STATIC_HOST = 'https://static.sse.com.cn'
TARGET_CODES = get_target_codes("SSE")
YEARS = default_report_years()
OUT_DIR = Path('data/raw/official/sse/pdfs')
MANIFEST = Path('data/raw/official/sse/report_manifest.json')
OUT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST.parent.mkdir(parents=True, exist_ok=True)


def fetch_page(code: str, title: str, page_no: int) -> dict:
    params = {
        'jsonCallBack': 'jsonpCallback',
        'isPagination': 'true',
        'pageHelp.pageSize': 25,
        'pageHelp.cacheSize': 1,
        'pageHelp.pageNo': page_no,
        'SECURITY_CODE': code,
        'TITLE': title,
        'BULLETIN_TYPE': '',
        'stockType': '',
        '_': '1741410000000',
    }
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': SSE_REFERER}
    response = requests.get(SSE_LIST_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    match = re.search(r'jsonpCallback\((.*)\)$', response.text)
    if not match:
        raise ValueError(f'Failed to parse JSONP for {code} page {page_no}')
    return json.loads(match.group(1))


def flatten_groups(groups: list) -> list[dict]:
    rows = []
    for group in groups:
        if isinstance(group, list):
            rows.extend(group)
        elif isinstance(group, dict):
            rows.append(group)
    return rows


def pick_full_annual_report(rows: list[dict], year: int) -> dict | None:
    target_year = str(year)
    candidates = []
    for row in rows:
        title = row.get('TITLE', '')
        if row.get('BULLETIN_TYPE_DESC') != '年报':
            continue
        if target_year not in title:
            continue
        if '摘要' in title or '英文' in title or '取消' in title or '更正' in title:
            continue
        if re.search(rf'{target_year}年年度报告$', title):
            candidates.append(row)
    if candidates:
        candidates = sorted(candidates, key=lambda x: x.get('SSEDATE', ''), reverse=True)
        return candidates[0]
    return None


def download_via_browser(pdf_url: str, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(SSE_REFERER, wait_until='networkidle', timeout=60000)
        with page.expect_download(timeout=90000) as download_info:
            page.goto(pdf_url, wait_until='commit', timeout=60000)
        download = download_info.value
        temp_path = download.path()
        if temp_path is None:
            raise RuntimeError(f'Failed to download {pdf_url}')
        target_path.write_bytes(Path(temp_path).read_bytes())
        browser.close()


def main() -> None:
    manifest = []
    for code in TARGET_CODES:
        payload = fetch_page(code, '年度报告', 1)
        total_pages = int(payload['pageHelp'].get('pageCount', 1))
        rows = flatten_groups(payload['pageHelp']['data'])
        for page_no in range(2, min(total_pages, 6) + 1):
            more = fetch_page(code, '年度报告', page_no)
            rows.extend(flatten_groups(more['pageHelp']['data']))
        for year in YEARS:
            picked = pick_full_annual_report(rows, year)
            if not picked:
                manifest.append({'company_code': code, 'year': year, 'status': 'missing'})
                continue
            filename = f"{code}_{year}_annual_sse.pdf"
            path = OUT_DIR / filename
            pdf_url = urljoin(STATIC_HOST, picked['URL'])
            download_via_browser(pdf_url, path)
            manifest.append({
                'company_code': code,
                'company_name': picked.get('SECURITY_NAME'),
                'year': year,
                'title': picked.get('TITLE'),
                'published_at': picked.get('SSEDATE'),
                'source_url': pdf_url,
                'local_path': str(path),
                'size_bytes': path.stat().st_size,
                'status': 'downloaded',
            })
            print(code, year, path.name, path.stat().st_size)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('manifest:', MANIFEST)


if __name__ == '__main__':
    main()
