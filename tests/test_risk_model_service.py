import json
import shutil
import uuid
from pathlib import Path

from app.services.risk_model import MODEL_FEATURE_COLUMNS, RiskModelService



def test_risk_model_service_predicts_from_latest_history() -> None:
    base_dir = Path('data/test_models') / uuid.uuid4().hex
    artifact_path = base_dir / 'risk_tabular_model.json'
    base_dir.mkdir(parents=True, exist_ok=True)

    artifact_path.write_text(
        json.dumps(
            {
                'model_type': 'logistic_regression_tabular',
                'trained_at': '2026-03-10T21:00:00',
                'sample_count': 4,
                'positive_samples': 2,
                'negative_samples': 2,
                'metrics': {'roc_auc': 0.9},
                'feature_columns': MODEL_FEATURE_COLUMNS,
                'imputer_statistics': [0.0] * len(MODEL_FEATURE_COLUMNS),
                'scaler_mean': [0.0] * len(MODEL_FEATURE_COLUMNS),
                'scaler_scale': [1.0] * len(MODEL_FEATURE_COLUMNS),
                'coefficients': [0.25] * len(MODEL_FEATURE_COLUMNS),
                'intercept': -1.0,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )

    history = [
        {
            'company_code': '300760',
            'report_year': 2022,
            'revenue_million': 3000,
            'net_profit_million': 800,
            'gross_margin_pct': 65,
            'net_margin_pct': 24,
            'rd_ratio_pct': 11,
            'debt_ratio_pct': 32,
            'current_ratio': 1.8,
            'cash_to_short_debt': 2.5,
            'inventory_turnover': 3.4,
            'receivable_turnover': 4.8,
            'operating_cashflow_million': 700,
            'roe_pct': 18,
        },
        {
            'company_code': '300760',
            'report_year': 2023,
            'revenue_million': 3200,
            'net_profit_million': 760,
            'gross_margin_pct': 63,
            'net_margin_pct': 21,
            'rd_ratio_pct': 10,
            'debt_ratio_pct': 39,
            'current_ratio': 1.4,
            'cash_to_short_debt': 1.2,
            'inventory_turnover': 2.8,
            'receivable_turnover': 4.1,
            'operating_cashflow_million': 420,
            'roe_pct': 15,
        },
        {
            'company_code': '300760',
            'report_year': 2024,
            'revenue_million': 3100,
            'net_profit_million': 520,
            'gross_margin_pct': 58,
            'net_margin_pct': 16,
            'rd_ratio_pct': 9,
            'debt_ratio_pct': 55,
            'current_ratio': 1.05,
            'cash_to_short_debt': 0.7,
            'inventory_turnover': 2.1,
            'receivable_turnover': 3.2,
            'operating_cashflow_million': -80,
            'roe_pct': 10,
        },
    ]

    try:
        service = RiskModelService(artifact_path=artifact_path)
        prediction = service.predict_company(history)
        assert prediction is not None
        assert prediction['company_code'] == '300760'
        assert 0 <= prediction['high_risk_probability'] <= 1
        assert prediction['top_contributions']
        assert prediction['model_summary']['model_ready'] is True
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


def test_risk_model_service_summary_reads_json_artifact() -> None:
    base_dir = Path('data/test_models') / uuid.uuid4().hex
    artifact_path = base_dir / 'risk_tabular_model.json'
    base_dir.mkdir(parents=True, exist_ok=True)

    artifact_path.write_text(
        json.dumps(
            {
                'model_type': 'logistic_regression_tabular',
                'trained_at': '2026-03-10T21:00:00',
                'sample_count': 12,
                'positive_samples': 3,
                'metrics': {'roc_auc': 0.61, 'f1': 0.44},
                'feature_columns': MODEL_FEATURE_COLUMNS,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )

    try:
        service = RiskModelService(artifact_path=artifact_path)
        summary = service.get_summary()
        assert summary['model_ready'] is True
        assert summary['sample_count'] == 12
        assert summary['metrics']['roc_auc'] == 0.61
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

