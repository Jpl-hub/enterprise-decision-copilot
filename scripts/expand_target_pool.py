from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
DEFAULT_TARGETS = DATA_DIR / 'targets.csv'
DEFAULT_PROMOTION = PROCESSED_DIR / 'target_promotion_candidates.csv'
DEFAULT_OFFICIAL = PROCESSED_DIR / 'financial_features_official.csv'
DEFAULT_OUTPUT = DATA_DIR / 'targets_expanded.csv'
DEFAULT_SUMMARY = DATA_DIR / 'quality' / 'targets_expanded_summary.json'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='根据候选池与官方财报覆盖扩展目标企业列表。')
    parser.add_argument('--targets', type=Path, default=DEFAULT_TARGETS)
    parser.add_argument('--promotion', type=Path, default=DEFAULT_PROMOTION)
    parser.add_argument('--official', type=Path, default=DEFAULT_OFFICIAL)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--summary', type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument('--max-total', type=int, default=12, help='扩展后目标池总上限。')
    parser.add_argument('--min-feature-years', type=int, default=1, help='新增候选至少具备多少年官方财务特征。')
    parser.add_argument('--per-industry', type=int, default=12, help='每个二级行业最多新增多少家。')
    parser.add_argument(
        '--coverage-source',
        choices=['official', 'financial'],
        default='financial',
        help='使用哪套财务覆盖作为扩池门槛。official 更严格，financial 更适合扩展演示池。',
    )
    return parser.parse_args()


def load_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, dtype={'company_code': str})


def normalize_code(value: object) -> str:
    raw = str(value or '').strip()
    if raw.endswith('.0'):
        raw = raw[:-2]
    return raw.zfill(6) if raw.isdigit() and len(raw) < 6 else raw


def infer_segment(industry_name: str) -> str:
    text = str(industry_name or '').strip()
    mapping = {
        '化学制药': '创新药',
        '生物制品': '生物制品',
        '中药Ⅱ': '中药',
        '中药': '中药',
        '医疗器械': '医疗器械',
        '医疗设备': '医疗器械',
        '医疗美容': '医疗消费',
        '医疗服务': '医疗服务',
        '医药商业': '连锁药房',
    }
    for keyword, segment in mapping.items():
        if keyword in text:
            return segment
    return text or '医药生物'


def build_expanded_targets(
    targets: pd.DataFrame,
    promotion: pd.DataFrame,
    official: pd.DataFrame,
    *,
    max_total: int,
    min_feature_years: int,
    per_industry: int,
    coverage_source: str,
) -> tuple[pd.DataFrame, dict]:
    current = targets.copy()
    current['company_code'] = current['company_code'].map(normalize_code)
    current_codes = set(current['company_code'].tolist())

    candidates = promotion.copy()
    candidates['company_code'] = candidates['company_code'].map(normalize_code)
    candidates = candidates[~candidates['company_code'].isin(current_codes)].copy()

    if official.empty:
        coverage = pd.DataFrame(columns=['company_code', 'feature_year_count', 'latest_report_year'])
    else:
        official = official.copy()
        official['company_code'] = official['company_code'].map(normalize_code)
        official['report_year'] = pd.to_numeric(official['report_year'], errors='coerce')
        coverage = (
            official.groupby('company_code', dropna=False)
            .agg(
                feature_year_count=('report_year', lambda values: int(pd.Series(values).dropna().nunique())),
                latest_report_year=('report_year', 'max'),
            )
            .reset_index()
        )

    candidates = candidates.merge(coverage, on='company_code', how='left')
    candidates['feature_year_count'] = pd.to_numeric(candidates['feature_year_count'], errors='coerce').fillna(0).astype(int)
    candidates['latest_report_year'] = pd.to_numeric(candidates['latest_report_year'], errors='coerce').fillna(0).astype(int)
    candidates = candidates[candidates['feature_year_count'] >= min_feature_years].copy()

    sort_columns = ['feature_year_count', 'candidate_priority_score', 'report_count', 'institution_count', 'company_code']
    ascending = [False, False, False, False, True]
    candidates = candidates.sort_values(sort_columns, ascending=ascending).reset_index(drop=True)

    selected_frames: list[pd.DataFrame] = []
    if not candidates.empty:
        for _, group in candidates.groupby('industry_name', sort=False):
            selected_frames.append(group.head(per_industry))
    selected = pd.concat(selected_frames, ignore_index=True) if selected_frames else candidates.head(0).copy()
    slots_left = max(max_total - len(current), 0)
    selected = selected.sort_values(sort_columns, ascending=ascending).head(slots_left).copy()

    if not selected.empty:
        selected_targets = pd.DataFrame(
            {
                'company_code': selected['company_code'],
                'company_name': selected['company_name'],
                'exchange': selected['exchange'],
                'industry': '医药生物',
                'segment': selected['industry_name'].map(infer_segment),
            }
        )
        expanded = pd.concat([current[['company_code', 'company_name', 'exchange', 'industry', 'segment']], selected_targets], ignore_index=True)
    else:
        expanded = current[['company_code', 'company_name', 'exchange', 'industry', 'segment']].copy()

    summary = {
        'current_target_count': int(len(current)),
        'expanded_target_count': int(len(expanded)),
        'added_target_count': int(len(selected)),
        'coverage_source': coverage_source,
        'min_feature_years': int(min_feature_years),
        'max_total': int(max_total),
        'per_industry': int(per_industry),
        'added_companies': [
            {
                'company_code': row['company_code'],
                'company_name': row['company_name'],
                'exchange': row['exchange'],
                'industry_name': row['industry_name'],
                'segment': infer_segment(row['industry_name']),
                'feature_year_count': int(row['feature_year_count']),
                'latest_report_year': int(row['latest_report_year']) if int(row['latest_report_year']) > 0 else None,
                'candidate_priority_score': round(float(row.get('candidate_priority_score') or 0.0), 2),
                'report_count': int(row.get('report_count') or 0),
                'institution_count': int(row.get('institution_count') or 0),
            }
            for row in selected.to_dict('records')
        ],
    }
    return expanded, summary


def main() -> None:
    args = parse_args()
    targets = load_frame(args.targets)
    promotion = load_frame(args.promotion)
    coverage_frame = load_frame(args.official if args.coverage_source == 'official' else (PROCESSED_DIR / 'financial_features.csv'))
    expanded, summary = build_expanded_targets(
        targets,
        promotion,
        coverage_frame,
        max_total=args.max_total,
        min_feature_years=args.min_feature_years,
        per_industry=args.per_industry,
        coverage_source=args.coverage_source,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    expanded.to_csv(args.output, index=False, encoding='utf-8-sig')
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    print(args.output)
    print(args.summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
