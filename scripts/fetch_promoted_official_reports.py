from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.data_pipeline_utils import default_report_years
from scripts.fetch_bse_official_reports import (
    BSE_REFERER,
    BSE_STATIC_HOST,
    download_pdf as bse_download_pdf,
    fetch_announcements as bse_fetch_announcements,
    pick_full_annual_report as bse_pick_full_annual_report,
)
from scripts.fetch_sse_official_reports import (
    MANIFEST as SSE_MANIFEST,
    OUT_DIR as SSE_OUT_DIR,
    STATIC_HOST as SSE_STATIC_HOST,
    download_via_browser as sse_download_pdf,
    fetch_page as sse_fetch_page,
    flatten_groups as sse_flatten_groups,
    pick_full_annual_report as sse_pick_full_annual_report,
)
from scripts.fetch_szse_official_reports import (
    MANIFEST as SZSE_MANIFEST,
    OUT_DIR as SZSE_OUT_DIR,
    SZSE_STATIC_HOST,
    download_pdf as szse_download_pdf,
    fetch_announcements as szse_fetch_announcements,
    pick_full_annual_report as szse_pick_full_annual_report,
)

PROMOTION_CANDIDATES_PATH = ROOT / 'data' / 'processed' / 'target_promotion_candidates.csv'
YEARS = default_report_years()
BSE_MANIFEST = ROOT / 'data' / 'raw' / 'official' / 'bse' / 'report_manifest.json'
SUMMARY_PATH = ROOT / 'data' / 'quality' / 'promoted_official_reports_summary.json'


def load_candidate_codes() -> dict[str, list[str]]:
    if not PROMOTION_CANDIDATES_PATH.exists():
        raise RuntimeError('缺少 target_promotion_candidates.csv，请先运行 scripts/build_target_promotion_plan.py')
    frame = pd.read_csv(PROMOTION_CANDIDATES_PATH, dtype={'company_code': str})
    frame['company_code'] = frame['company_code'].astype(str).str.strip()
    frame['exchange'] = frame['exchange'].astype(str).str.upper().str.strip()
    grouped: dict[str, list[str]] = {}
    for exchange, group in frame.groupby('exchange'):
        grouped[exchange] = group['company_code'].dropna().drop_duplicates().tolist()
    return grouped


def load_manifest(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding='utf-8'))


def manifest_index(items: list[dict]) -> dict[tuple[str, int], dict]:
    indexed: dict[tuple[str, int], dict] = {}
    for item in items:
        code = str(item.get('company_code') or item.get('query_company_code') or '').strip()
        year = item.get('year')
        if not code or year in (None, ''):
            continue
        indexed[(code, int(year))] = item
    return indexed


def save_manifest(path: Path, indexed: dict[tuple[str, int], dict]) -> None:
    rows = sorted(indexed.values(), key=lambda item: (str(item.get('company_code') or ''), int(item.get('year') or 0)))
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')


def process_sse(codes: list[str]) -> dict[str, int]:
    indexed = manifest_index(load_manifest(SSE_MANIFEST))
    downloaded = 0
    skipped = 0
    missing = 0
    for code in codes:
        payload = sse_fetch_page(code, '年度报告', 1)
        total_pages = int(payload['pageHelp'].get('pageCount', 1))
        rows = sse_flatten_groups(payload['pageHelp']['data'])
        for page_no in range(2, min(total_pages, 6) + 1):
            rows.extend(sse_flatten_groups(sse_fetch_page(code, '年度报告', page_no)['pageHelp']['data']))
        for year in YEARS:
            existing = indexed.get((code, year))
            if existing and existing.get('status') == 'downloaded' and Path(existing.get('local_path', '')).exists():
                skipped += 1
                continue
            picked = sse_pick_full_annual_report(rows, year)
            if not picked:
                indexed[(code, year)] = {'company_code': code, 'year': year, 'status': 'missing'}
                missing += 1
                continue
            filename = f"{code}_{year}_annual_sse.pdf"
            path = SSE_OUT_DIR / filename
            pdf_url = urljoin(SSE_STATIC_HOST, picked['URL'])
            sse_download_pdf(pdf_url, path)
            indexed[(code, year)] = {
                'company_code': code,
                'company_name': picked.get('SECURITY_NAME'),
                'year': year,
                'title': picked.get('TITLE'),
                'published_at': picked.get('SSEDATE'),
                'source_url': pdf_url,
                'local_path': str(path),
                'size_bytes': path.stat().st_size,
                'status': 'downloaded',
            }
            downloaded += 1
            print('SSE', code, year, path.name, path.stat().st_size)
    save_manifest(SSE_MANIFEST, indexed)
    return {'downloaded': downloaded, 'skipped': skipped, 'missing': missing}


def process_szse(codes: list[str]) -> dict[str, int]:
    indexed = manifest_index(load_manifest(SZSE_MANIFEST))
    downloaded = 0
    skipped = 0
    missing = 0
    for code in codes:
        rows = szse_fetch_announcements(code)
        for year in YEARS:
            existing = indexed.get((code, year))
            if existing and existing.get('status') == 'downloaded' and Path(existing.get('local_path', '')).exists():
                skipped += 1
                continue
            picked = szse_pick_full_annual_report(rows, year)
            if not picked:
                indexed[(code, year)] = {'company_code': code, 'year': year, 'status': 'missing'}
                missing += 1
                continue
            filename = f"{code}_{year}_annual_szse.pdf"
            path = SZSE_OUT_DIR / filename
            szse_download_pdf(picked['attachPath'], path)
            indexed[(code, year)] = {
                'company_code': code,
                'company_name': picked.get('secName', [''])[0],
                'year': year,
                'title': picked.get('title'),
                'published_at': str(picked.get('publishTime', '')).split(' ')[0],
                'source_url': f"{SZSE_STATIC_HOST}{picked['attachPath']}",
                'local_path': str(path),
                'size_bytes': path.stat().st_size,
                'status': 'downloaded',
            }
            downloaded += 1
            print('SZSE', code, year, path.name, path.stat().st_size)
    save_manifest(SZSE_MANIFEST, indexed)
    return {'downloaded': downloaded, 'skipped': skipped, 'missing': missing}


def process_bse(codes: list[str]) -> dict[str, int]:
    indexed = manifest_index(load_manifest(BSE_MANIFEST))
    downloaded = 0
    skipped = 0
    missing = 0
    for code in codes:
        rows = bse_fetch_announcements(code)
        for year in YEARS:
            existing = indexed.get((code, year))
            if existing and existing.get('status') == 'downloaded' and Path(existing.get('local_path', '')).exists():
                skipped += 1
                continue
            picked = bse_pick_full_annual_report(rows, year)
            if not picked:
                indexed[(code, year)] = {'company_code': code, 'year': year, 'status': 'missing'}
                missing += 1
                continue
            filename = f"{code}_{year}_annual_bse.pdf"
            path = Path('data/raw/official/bse/pdfs') / filename
            bse_download_pdf(picked['destFilePath'], path)
            indexed[(code, year)] = {
                'company_code': code,
                'disclosure_company_code': str(picked.get('companyCd', code)),
                'company_name': picked.get('companyName'),
                'year': year,
                'title': picked.get('disclosureTitle'),
                'published_at': picked.get('publishDate'),
                'source_url': urljoin(BSE_STATIC_HOST, picked['destFilePath']),
                'local_path': str(path),
                'size_bytes': path.stat().st_size,
                'status': 'downloaded',
            }
            downloaded += 1
            print('BSE', code, year, path.name, path.stat().st_size)
    save_manifest(BSE_MANIFEST, indexed)
    return {'downloaded': downloaded, 'skipped': skipped, 'missing': missing}


def main() -> None:
    candidates = load_candidate_codes()
    summary = {
        'sse': process_sse(candidates.get('SSE', [])),
        'szse': process_szse(candidates.get('SZSE', [])),
        'bse': process_bse(candidates.get('BSE', [])),
        'years': YEARS,
        'candidate_codes': candidates,
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(SUMMARY_PATH)
    print(summary)


if __name__ == '__main__':
    main()
