from pathlib import Path

import pandas as pd

from scripts.expand_target_pool import build_expanded_targets


def test_build_expanded_targets_adds_ranked_candidates() -> None:
    targets = pd.DataFrame(
        [
            {'company_code': '600276', 'company_name': '恒瑞医药', 'exchange': 'SSE', 'industry': '医药生物', 'segment': '创新药'},
            {'company_code': '300760', 'company_name': '迈瑞医疗', 'exchange': 'SZSE', 'industry': '医药生物', 'segment': '医疗器械'},
        ]
    )
    promotion = pd.DataFrame(
        [
            {'company_code': '300896', 'company_name': '爱美客', 'exchange': 'SZSE', 'industry_name': '医疗美容', 'candidate_priority_score': 99.77, 'report_count': 88, 'institution_count': 19},
            {'company_code': '300294', 'company_name': '博雅生物', 'exchange': 'SZSE', 'industry_name': '生物制品', 'candidate_priority_score': 63.36, 'report_count': 37, 'institution_count': 12},
            {'company_code': '301096', 'company_name': '百诚医药', 'exchange': 'SZSE', 'industry_name': '医疗服务', 'candidate_priority_score': 55.86, 'report_count': 27, 'institution_count': 11},
        ]
    )
    coverage = pd.DataFrame(
        [
            {'company_code': '300896', 'report_year': 2022},
            {'company_code': '300896', 'report_year': 2023},
            {'company_code': '300896', 'report_year': 2024},
            {'company_code': '300294', 'report_year': 2022},
            {'company_code': '300294', 'report_year': 2023},
            {'company_code': '300294', 'report_year': 2024},
        ]
    )

    expanded, summary = build_expanded_targets(
        targets,
        promotion,
        coverage,
        max_total=4,
        min_feature_years=2,
        per_industry=4,
        coverage_source='financial',
    )

    codes = expanded['company_code'].astype(str).tolist()
    assert len(expanded) == 4
    assert '300896' in codes
    assert '300294' in codes
    assert '301096' not in codes
    assert summary['added_target_count'] == 2
    assert summary['coverage_source'] == 'financial'
