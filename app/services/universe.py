from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.config import settings
from app.data_access import load_industry_company_universe


class IndustryUniverseService:
    def __init__(
        self,
        universe_path: Path | None = None,
        quality_path: Path | None = None,
        promotion_candidates_path: Path | None = None,
        official_features_path: Path | None = None,
    ) -> None:
        self.universe_path = universe_path or (settings.processed_dir / 'industry_company_universe.csv')
        self.quality_path = quality_path or (settings.data_dir / 'quality' / 'industry_company_universe_quality.json')
        self.promotion_candidates_path = promotion_candidates_path or (settings.processed_dir / 'target_promotion_candidates.csv')
        self.official_features_path = official_features_path or (settings.processed_dir / 'financial_features_official.csv')

    def _normalize_company_code(self, code: object, exchange: object) -> str:
        raw = '' if code is None else str(code).strip()
        if not raw:
            return raw
        if raw.endswith('.0'):
            raw = raw[:-2]
        exchange_text = '' if exchange is None else str(exchange).strip().upper()
        if exchange_text in {'SSE', 'SZSE', 'BSE'} and raw.isdigit() and len(raw) < 6:
            return raw.zfill(6)
        return raw

    def _load_frame(self) -> pd.DataFrame:
        if self.universe_path == settings.processed_dir / 'industry_company_universe.csv':
            frame = load_industry_company_universe().copy()
        elif self.universe_path.exists():
            frame = pd.read_csv(self.universe_path, dtype={'company_code': str})
        else:
            frame = pd.DataFrame()
        if frame.empty:
            return frame
        if 'exchange' not in frame.columns:
            frame['exchange'] = ''
        frame['company_code'] = [self._normalize_company_code(code, exchange) for code, exchange in zip(frame['company_code'], frame['exchange'])]
        if 'industry_code' in frame.columns:
            frame['industry_code'] = frame['industry_code'].astype(str).str.replace('.0', '', regex=False)
        for column in ['report_count', 'institution_count', 'positive_count', 'neutral_count', 'negative_count']:
            if column in frame.columns:
                frame[column] = pd.to_numeric(frame[column], errors='coerce').fillna(0).astype(int)
        if 'in_target_pool' in frame.columns:
            frame['in_target_pool'] = frame['in_target_pool'].astype(str).str.lower().isin(['true', '1', 'yes'])
        return frame

    def _load_quality(self) -> dict:
        if self.quality_path.exists():
            return json.loads(self.quality_path.read_text(encoding='utf-8'))
        return {}

    def _load_promotion_candidates(self) -> pd.DataFrame:
        if not self.promotion_candidates_path.exists():
            return pd.DataFrame()
        frame = pd.read_csv(self.promotion_candidates_path, dtype={'company_code': str})
        if frame.empty:
            return frame
        if 'exchange' not in frame.columns:
            frame['exchange'] = ''
        frame['company_code'] = [self._normalize_company_code(code, exchange) for code, exchange in zip(frame['company_code'], frame['exchange'])]
        if 'candidate_priority_score' in frame.columns:
            frame['candidate_priority_score'] = pd.to_numeric(frame['candidate_priority_score'], errors='coerce').fillna(0.0)
        return frame

    def _load_official_features(self) -> pd.DataFrame:
        if not self.official_features_path.exists():
            return pd.DataFrame()
        frame = pd.read_csv(self.official_features_path, dtype={'company_code': str})
        if frame.empty:
            return frame
        if 'report_year' in frame.columns:
            frame['report_year'] = pd.to_numeric(frame['report_year'], errors='coerce').fillna(0).astype(int)
        if 'company_name' not in frame.columns:
            frame['company_name'] = ''
        frame['company_code'] = frame['company_code'].astype(str)
        return frame

    def _normalize(self, series: pd.Series) -> pd.Series:
        series = pd.to_numeric(series, errors='coerce').fillna(0.0)
        if series.empty:
            return series
        minimum = float(series.min())
        maximum = float(series.max())
        if maximum == minimum:
            return pd.Series([70.0] * len(series), index=series.index)
        return ((series - minimum) / (maximum - minimum) * 100).clip(0, 100)

    def _score_candidates(self, frame: pd.DataFrame) -> pd.DataFrame:
        candidates = frame[~frame['in_target_pool']].copy() if 'in_target_pool' in frame.columns else frame.copy()
        if candidates.empty:
            return candidates
        safe_report_count = candidates['report_count'].replace(0, 1)
        candidates['positive_ratio'] = (candidates['positive_count'] / safe_report_count).fillna(0.0)
        candidates['negative_ratio'] = (candidates['negative_count'] / safe_report_count).fillna(0.0)
        candidates['report_score_norm'] = self._normalize(candidates['report_count'])
        candidates['institution_score_norm'] = self._normalize(candidates['institution_count'])
        candidates['candidate_priority_score'] = (
            candidates['report_score_norm'] * 0.45
            + candidates['institution_score_norm'] * 0.25
            + candidates['positive_ratio'] * 100 * 0.2
            + (1 - candidates['negative_ratio']).clip(lower=0) * 100 * 0.1
        ).clip(0, 100)
        return candidates

    def _build_reasons(self, row: pd.Series) -> list[str]:
        reasons = [
            f"研报覆盖 {int(row['report_count'])} 篇",
            f"覆盖机构 {int(row['institution_count'])} 家",
            f"正向占比 {float(row['positive_ratio']) * 100:.1f}%",
        ]
        if float(row['negative_ratio']) > 0:
            reasons.append(f"负向占比 {float(row['negative_ratio']) * 100:.1f}%")
        if row.get('latest_report_date'):
            reasons.append(f"最近研报 {row['latest_report_date']}")
        return reasons

    def _serialize_candidates(self, frame: pd.DataFrame) -> list[dict]:
        records = frame.to_dict('records')
        for item in records:
            row = pd.Series(item)
            item['candidate_priority_score'] = round(float(item.get('candidate_priority_score') or 0.0), 2)
            item['recommendation_reasons'] = self._build_reasons(row)
        return records

    def _build_financial_readiness(self, limit: int = 8) -> dict:
        promotion_frame = self._load_promotion_candidates()
        official_frame = self._load_official_features()
        if promotion_frame.empty:
            return {
                'promotion_candidate_count': 0,
                'official_feature_company_count': 0,
                'official_feature_row_count': 0,
                'ready_candidate_count': 0,
                'partial_candidate_count': 0,
                'pending_candidate_count': 0,
                'average_year_coverage_ratio': 0.0,
                'candidates': [],
            }

        if official_frame.empty:
            promotion_frame = promotion_frame.copy()
            promotion_frame['feature_year_count'] = 0
            promotion_frame['report_years'] = ''
            promotion_frame['latest_report_year'] = None
            promotion_frame['readiness_status'] = 'pending'
            promotion_frame['year_coverage_ratio'] = 0.0
        else:
            coverage = (
                official_frame.groupby('company_code', dropna=False)
                .agg(
                    feature_year_count=('report_year', 'nunique'),
                    latest_report_year=('report_year', 'max'),
                )
                .reset_index()
            )
            year_lists = (
                official_frame.groupby('company_code', dropna=False)['report_year']
                .apply(lambda values: ','.join(str(int(year)) for year in sorted(pd.unique(values))))
                .reset_index(name='report_years')
            )
            coverage = coverage.merge(year_lists, on='company_code', how='left')
            promotion_frame = promotion_frame.merge(coverage, on='company_code', how='left')
            promotion_frame['feature_year_count'] = pd.to_numeric(
                promotion_frame['feature_year_count'], errors='coerce'
            ).fillna(0).astype(int)
            promotion_frame['report_years'] = promotion_frame['report_years'].fillna('')
            promotion_frame['latest_report_year'] = pd.to_numeric(
                promotion_frame['latest_report_year'], errors='coerce'
            ).where(lambda series: series.notna(), None)
            promotion_frame['readiness_status'] = promotion_frame['feature_year_count'].map(
                lambda count: 'ready' if int(count) >= 3 else ('partial' if int(count) > 0 else 'pending')
            )
            promotion_frame['year_coverage_ratio'] = (promotion_frame['feature_year_count'] / 3).clip(0, 1).round(4)

        sort_fields = ['feature_year_count', 'candidate_priority_score', 'report_count', 'institution_count', 'company_code']
        ascending = [False, False, False, False, True]
        candidates = promotion_frame.sort_values(sort_fields, ascending=ascending).head(limit).copy()
        if 'candidate_priority_score' in candidates.columns:
            candidates['candidate_priority_score'] = candidates['candidate_priority_score'].astype(float).round(2)
        records = []
        for item in candidates.to_dict('records'):
            records.append(
                {
                    'company_code': item.get('company_code', ''),
                    'company_name': item.get('company_name', ''),
                    'exchange': item.get('exchange', ''),
                    'industry_name': item.get('industry_name', ''),
                    'candidate_priority_score': round(float(item.get('candidate_priority_score') or 0.0), 2),
                    'feature_year_count': int(item.get('feature_year_count') or 0),
                    'report_years': [year for year in str(item.get('report_years') or '').split(',') if year],
                    'latest_report_year': int(item['latest_report_year']) if pd.notna(item.get('latest_report_year')) else None,
                    'readiness_status': str(item.get('readiness_status') or 'pending'),
                    'year_coverage_ratio': round(float(item.get('year_coverage_ratio') or 0.0), 4),
                }
            )

        ready_count = int((promotion_frame['readiness_status'] == 'ready').sum())
        partial_count = int((promotion_frame['readiness_status'] == 'partial').sum())
        pending_count = int((promotion_frame['readiness_status'] == 'pending').sum())
        average_ratio = float(promotion_frame['year_coverage_ratio'].mean()) if not promotion_frame.empty else 0.0
        return {
            'promotion_candidate_count': int(len(promotion_frame)),
            'official_feature_company_count': int(official_frame['company_code'].nunique()) if not official_frame.empty else 0,
            'official_feature_row_count': int(len(official_frame)),
            'ready_candidate_count': ready_count,
            'partial_candidate_count': partial_count,
            'pending_candidate_count': pending_count,
            'average_year_coverage_ratio': round(average_ratio, 4),
            'candidates': records,
        }

    def get_promotion_plan(self, limit: int = 12, per_industry: int = 2) -> dict:
        frame = self._load_frame()
        quality = self._load_quality()
        if frame.empty:
            return {
                'plan_ready': False,
                'generated_at': quality.get('generated_at'),
                'limit': limit,
                'per_industry_limit': per_industry,
                'candidate_count': 0,
                'selected_count': 0,
                'industries': [],
                'candidates': [],
            }

        scored = self._score_candidates(frame)
        if scored.empty:
            return {
                'plan_ready': False,
                'generated_at': quality.get('generated_at'),
                'limit': limit,
                'per_industry_limit': per_industry,
                'candidate_count': 0,
                'selected_count': 0,
                'industries': [],
                'candidates': [],
            }

        scored = scored.sort_values(
            ['candidate_priority_score', 'report_count', 'institution_count', 'company_code'],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)
        selected_groups = []
        for _, group in scored.groupby('industry_name', sort=False):
            selected_groups.append(group.head(per_industry))
        selected = pd.concat(selected_groups, ignore_index=True) if selected_groups else scored.head(0).copy()
        selected = selected.sort_values(
            ['candidate_priority_score', 'report_count', 'institution_count', 'company_code'],
            ascending=[False, False, False, True],
        ).head(limit).reset_index(drop=True)
        industries = (
            selected.groupby('industry_name', dropna=False)
            .agg(selected_count=('company_code', 'count'))
            .reset_index()
            .sort_values(['selected_count', 'industry_name'], ascending=[False, True])
        )
        return {
            'plan_ready': True,
            'generated_at': quality.get('generated_at'),
            'limit': limit,
            'per_industry_limit': per_industry,
            'candidate_count': int(len(scored)),
            'selected_count': int(len(selected)),
            'industries': industries.to_dict('records'),
            'candidates': self._serialize_candidates(selected),
        }

    def get_summary(self, limit: int = 12) -> dict:
        frame = self._load_frame()
        quality = self._load_quality()
        financial_readiness = self._build_financial_readiness(limit=min(limit, 8))
        if frame.empty:
            return {
                'universe_ready': False,
                'generated_at': quality.get('generated_at'),
                'company_count': 0,
                'industry_count': 0,
                'total_report_count': 0,
                'target_overlap_count': 0,
                'exchanges': [],
                'industries': [],
                'top_companies': [],
                'recommended_candidates': [],
                'industry_code_map': quality.get('industry_code_map', {}),
                'financial_readiness': financial_readiness,
            }

        exchanges = (
            frame.groupby('exchange', dropna=False)
            .agg(
                company_count=('company_code', 'nunique'),
                report_count=('report_count', 'sum'),
            )
            .reset_index()
            .sort_values(['company_count', 'report_count', 'exchange'], ascending=[False, False, True])
        )
        industries = (
            frame.groupby(['industry_code', 'industry_name'], dropna=False)
            .agg(
                company_count=('company_code', 'nunique'),
                report_count=('report_count', 'sum'),
            )
            .reset_index()
            .sort_values(['company_count', 'report_count', 'industry_name'], ascending=[False, False, True])
        )
        top_companies = frame.sort_values(['report_count', 'institution_count', 'company_code'], ascending=[False, False, True]).head(limit)
        scored = self._score_candidates(frame)
        recommended_candidates = scored.sort_values(
            ['candidate_priority_score', 'report_count', 'institution_count', 'company_code'],
            ascending=[False, False, False, True],
        ).head(limit)

        return {
            'universe_ready': True,
            'generated_at': quality.get('generated_at'),
            'company_count': int(frame['company_code'].nunique()),
            'industry_count': int(frame['industry_name'].nunique()),
            'total_report_count': int(frame['report_count'].sum()),
            'target_overlap_count': int(frame.loc[frame['in_target_pool'], 'company_code'].nunique()) if 'in_target_pool' in frame else 0,
            'exchanges': exchanges.to_dict('records'),
            'industries': industries.head(limit).to_dict('records'),
            'top_companies': top_companies.to_dict('records'),
            'recommended_candidates': self._serialize_candidates(recommended_candidates),
            'industry_code_map': quality.get('industry_code_map', {}),
            'financial_readiness': financial_readiness,
        }
