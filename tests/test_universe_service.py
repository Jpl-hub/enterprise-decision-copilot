import json
import shutil
import uuid
from pathlib import Path

import pandas as pd

from app.services.universe import IndustryUniverseService



def test_industry_universe_service_summarizes_candidates() -> None:
    base_dir = Path('data/test_universe') / uuid.uuid4().hex
    universe_path = base_dir / 'industry_company_universe.csv'
    quality_path = base_dir / 'industry_company_universe_quality.json'
    base_dir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        [
            {
                'company_code': '300760',
                'company_name': '迈瑞医疗',
                'exchange': 'SZSE',
                'market': 'SHENZHEN',
                'industry_code': '1041',
                'industry_name': '医疗器械',
                'report_count': 12,
                'institution_count': 6,
                'positive_count': 10,
                'neutral_count': 2,
                'negative_count': 0,
                'latest_report_date': '2026-03-01',
                'earliest_report_date': '2024-01-10',
                'in_target_pool': True,
                'latest_report_title': '稳健增长',
                'latest_source_url': 'https://example.com/a',
            },
            {
                'company_code': '688271',
                'company_name': '联影医疗',
                'exchange': 'SSE',
                'market': 'SHANGHAI',
                'industry_code': '1041',
                'industry_name': '医疗器械',
                'report_count': 8,
                'institution_count': 4,
                'positive_count': 5,
                'neutral_count': 2,
                'negative_count': 1,
                'latest_report_date': '2026-02-26',
                'earliest_report_date': '2024-02-20',
                'in_target_pool': True,
                'latest_report_title': '设备放量',
                'latest_source_url': 'https://example.com/b',
            },
            {
                'company_code': '002001',
                'company_name': '新和成',
                'exchange': 'SZSE',
                'market': 'SHENZHEN',
                'industry_code': '1010',
                'industry_name': '化学制药',
                'report_count': 5,
                'institution_count': 3,
                'positive_count': 2,
                'neutral_count': 2,
                'negative_count': 1,
                'latest_report_date': '2026-02-18',
                'earliest_report_date': '2024-03-12',
                'in_target_pool': False,
                'latest_report_title': '候选扩容',
                'latest_source_url': 'https://example.com/c',
            },
        ]
    ).to_csv(universe_path, index=False, encoding='utf-8-sig')

    quality_path.write_text(
        json.dumps(
            {
                'generated_at': '2026-03-10T22:00:00',
                'industry_code_map': {'医疗器械': '1041', '化学制药': '1010'},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )

    try:
        service = IndustryUniverseService(universe_path=universe_path, quality_path=quality_path)
        summary = service.get_summary(limit=5)
        assert summary['universe_ready'] is True
        assert summary['company_count'] == 3
        assert summary['industry_count'] == 2
        assert summary['target_overlap_count'] == 2
        assert summary['top_companies'][0]['company_code'] == '300760'
        assert summary['industries'][0]['industry_name'] == '医疗器械'
        assert summary['industry_code_map']['医疗器械'] == '1041'
        assert summary['recommended_candidates']
        assert summary['recommended_candidates'][0]['in_target_pool'] is False
        assert summary['recommended_candidates'][0]['candidate_priority_score'] > 0
        assert summary['recommended_candidates'][0]['recommendation_reasons']
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)



def test_industry_universe_service_handles_missing_files() -> None:
    base_dir = Path('data/test_universe') / uuid.uuid4().hex
    base_dir.mkdir(parents=True, exist_ok=True)

    try:
        service = IndustryUniverseService(
            universe_path=base_dir / 'missing.csv',
            quality_path=base_dir / 'missing.json',
        )
        summary = service.get_summary()
        assert summary['universe_ready'] is False
        assert summary['company_count'] == 0
        assert summary['top_companies'] == []
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

def test_industry_universe_service_builds_balanced_promotion_plan() -> None:
    base_dir = Path('data/test_universe') / uuid.uuid4().hex
    universe_path = base_dir / 'industry_company_universe.csv'
    quality_path = base_dir / 'industry_company_universe_quality.json'
    base_dir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        [
            {
                'company_code': 'A1', 'company_name': '候选A1', 'exchange': 'SSE', 'market': 'SHANGHAI', 'industry_code': '1', 'industry_name': '化学制药',
                'report_count': 20, 'institution_count': 8, 'positive_count': 18, 'neutral_count': 2, 'negative_count': 0,
                'latest_report_date': '2026-03-01', 'earliest_report_date': '2024-01-01', 'in_target_pool': False, 'latest_report_title': 'A1', 'latest_source_url': 'https://example.com/a1'
            },
            {
                'company_code': 'A2', 'company_name': '候选A2', 'exchange': 'SSE', 'market': 'SHANGHAI', 'industry_code': '1', 'industry_name': '化学制药',
                'report_count': 18, 'institution_count': 7, 'positive_count': 16, 'neutral_count': 2, 'negative_count': 0,
                'latest_report_date': '2026-02-01', 'earliest_report_date': '2024-01-01', 'in_target_pool': False, 'latest_report_title': 'A2', 'latest_source_url': 'https://example.com/a2'
            },
            {
                'company_code': 'A3', 'company_name': '候选A3', 'exchange': 'SSE', 'market': 'SHANGHAI', 'industry_code': '1', 'industry_name': '化学制药',
                'report_count': 17, 'institution_count': 6, 'positive_count': 15, 'neutral_count': 2, 'negative_count': 0,
                'latest_report_date': '2026-01-01', 'earliest_report_date': '2024-01-01', 'in_target_pool': False, 'latest_report_title': 'A3', 'latest_source_url': 'https://example.com/a3'
            },
            {
                'company_code': 'B1', 'company_name': '候选B1', 'exchange': 'SZSE', 'market': 'SHENZHEN', 'industry_code': '2', 'industry_name': '医疗器械',
                'report_count': 15, 'institution_count': 5, 'positive_count': 14, 'neutral_count': 1, 'negative_count': 0,
                'latest_report_date': '2026-03-02', 'earliest_report_date': '2024-01-01', 'in_target_pool': False, 'latest_report_title': 'B1', 'latest_source_url': 'https://example.com/b1'
            },
            {
                'company_code': 'B2', 'company_name': '候选B2', 'exchange': 'SZSE', 'market': 'SHENZHEN', 'industry_code': '2', 'industry_name': '医疗器械',
                'report_count': 14, 'institution_count': 4, 'positive_count': 12, 'neutral_count': 2, 'negative_count': 0,
                'latest_report_date': '2026-03-01', 'earliest_report_date': '2024-01-01', 'in_target_pool': False, 'latest_report_title': 'B2', 'latest_source_url': 'https://example.com/b2'
            },
            {
                'company_code': 'T1', 'company_name': '正式T1', 'exchange': 'SZSE', 'market': 'SHENZHEN', 'industry_code': '2', 'industry_name': '医疗器械',
                'report_count': 30, 'institution_count': 10, 'positive_count': 25, 'neutral_count': 5, 'negative_count': 0,
                'latest_report_date': '2026-03-03', 'earliest_report_date': '2024-01-01', 'in_target_pool': True, 'latest_report_title': 'T1', 'latest_source_url': 'https://example.com/t1'
            },
        ]
    ).to_csv(universe_path, index=False, encoding='utf-8-sig')

    quality_path.write_text(json.dumps({'generated_at': '2026-03-10T22:00:00'}, ensure_ascii=False), encoding='utf-8')

    try:
        service = IndustryUniverseService(universe_path=universe_path, quality_path=quality_path)
        plan = service.get_promotion_plan(limit=4, per_industry=2)
        assert plan['plan_ready'] is True
        assert plan['selected_count'] == 4
        assert all(item['company_code'] != 'T1' for item in plan['candidates'])
        counts = {item['industry_name']: item['selected_count'] for item in plan['industries']}
        assert counts['化学制药'] == 2
        assert counts['医疗器械'] == 2
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

def test_industry_universe_service_normalizes_zero_padded_codes() -> None:
    base_dir = Path('data/test_universe') / uuid.uuid4().hex
    universe_path = base_dir / 'industry_company_universe.csv'
    quality_path = base_dir / 'industry_company_universe_quality.json'
    base_dir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        [
            {
                'company_code': '999',
                'company_name': '华润三九',
                'exchange': 'SZSE',
                'market': 'SHENZHEN',
                'industry_code': '1040',
                'industry_name': '中药Ⅱ',
                'report_count': 10,
                'institution_count': 4,
                'positive_count': 9,
                'neutral_count': 1,
                'negative_count': 0,
                'latest_report_date': '2026-03-01',
                'earliest_report_date': '2024-01-01',
                'in_target_pool': False,
                'latest_report_title': '中药修复',
                'latest_source_url': 'https://example.com/z999',
            }
        ]
    ).to_csv(universe_path, index=False, encoding='utf-8-sig')
    quality_path.write_text('{}', encoding='utf-8')

    try:
        service = IndustryUniverseService(universe_path=universe_path, quality_path=quality_path)
        summary = service.get_summary(limit=5)
        assert summary['top_companies'][0]['company_code'] == '000999'
        assert summary['recommended_candidates'][0]['company_code'] == '000999'
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)



def test_industry_universe_service_reports_financial_readiness() -> None:
    base_dir = Path('data/test_universe') / uuid.uuid4().hex
    universe_path = base_dir / 'industry_company_universe.csv'
    quality_path = base_dir / 'industry_company_universe_quality.json'
    promotion_candidates_path = base_dir / 'target_promotion_candidates.csv'
    official_features_path = base_dir / 'financial_features_official.csv'
    base_dir.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        [
            {
                'company_code': '000999',
                'company_name': '华润三九',
                'exchange': 'SZSE',
                'market': 'SHENZHEN',
                'industry_code': '1040',
                'industry_name': '中药Ⅱ',
                'report_count': 10,
                'institution_count': 4,
                'positive_count': 9,
                'neutral_count': 1,
                'negative_count': 0,
                'latest_report_date': '2026-03-01',
                'earliest_report_date': '2024-01-01',
                'in_target_pool': False,
                'latest_report_title': '中药修复',
                'latest_source_url': 'https://example.com/z999',
            },
            {
                'company_code': '688677',
                'company_name': '海泰新光',
                'exchange': 'SSE',
                'market': 'SHANGHAI',
                'industry_code': '1041',
                'industry_name': '医疗器械',
                'report_count': 8,
                'institution_count': 3,
                'positive_count': 6,
                'neutral_count': 2,
                'negative_count': 0,
                'latest_report_date': '2026-03-02',
                'earliest_report_date': '2024-01-01',
                'in_target_pool': False,
                'latest_report_title': '器械恢复',
                'latest_source_url': 'https://example.com/haitai',
            },
        ]
    ).to_csv(universe_path, index=False, encoding='utf-8-sig')

    promotion_candidates = pd.DataFrame(
        [
            {
                'company_code': '000999',
                'company_name': '华润三九',
                'exchange': 'SZSE',
                'industry_name': '中药Ⅱ',
                'candidate_priority_score': 87.6,
                'report_count': 10,
                'institution_count': 4,
            },
            {
                'company_code': '688677',
                'company_name': '海泰新光',
                'exchange': 'SSE',
                'industry_name': '医疗器械',
                'candidate_priority_score': 74.2,
                'report_count': 8,
                'institution_count': 3,
            },
            {
                'company_code': '920982',
                'company_name': '锦波生物',
                'exchange': 'BSE',
                'industry_name': '医疗美容',
                'candidate_priority_score': 70.1,
                'report_count': 7,
                'institution_count': 3,
            },
        ]
    )
    promotion_candidates.to_csv(promotion_candidates_path, index=False, encoding='utf-8-sig')

    pd.DataFrame(
        [
            {'company_code': '000999', 'company_name': '华润三九', 'report_year': 2022},
            {'company_code': '000999', 'company_name': '华润三九', 'report_year': 2023},
            {'company_code': '000999', 'company_name': '华润三九', 'report_year': 2024},
            {'company_code': '688677', 'company_name': '海泰新光', 'report_year': 2023},
            {'company_code': '688677', 'company_name': '海泰新光', 'report_year': 2024},
        ]
    ).to_csv(official_features_path, index=False, encoding='utf-8-sig')
    quality_path.write_text('{}', encoding='utf-8')

    try:
        service = IndustryUniverseService(
            universe_path=universe_path,
            quality_path=quality_path,
            promotion_candidates_path=promotion_candidates_path,
            official_features_path=official_features_path,
        )
        summary = service.get_summary(limit=5)
        readiness = summary['financial_readiness']
        assert readiness['promotion_candidate_count'] == 3
        assert readiness['official_feature_company_count'] == 2
        assert readiness['ready_candidate_count'] == 1
        assert readiness['partial_candidate_count'] == 1
        assert readiness['pending_candidate_count'] == 1
        assert readiness['candidates'][0]['company_code'] == '000999'
        assert readiness['candidates'][0]['readiness_status'] == 'ready'
        assert readiness['candidates'][1]['readiness_status'] == 'partial'
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)
