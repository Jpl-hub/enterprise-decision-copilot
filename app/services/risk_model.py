from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.config import settings


BASE_FEATURE_COLUMNS = [
    'revenue_million',
    'net_profit_million',
    'gross_margin_pct',
    'net_margin_pct',
    'rd_ratio_pct',
    'debt_ratio_pct',
    'current_ratio',
    'cash_to_short_debt',
    'inventory_turnover',
    'receivable_turnover',
    'operating_cashflow_million',
    'roe_pct',
]

DERIVED_FEATURE_COLUMNS = [
    'revenue_yoy_pct',
    'profit_yoy_pct',
    'cashflow_yoy_change_million',
    'debt_ratio_change_pct',
    'current_ratio_change',
]

MODEL_FEATURE_COLUMNS = BASE_FEATURE_COLUMNS + DERIVED_FEATURE_COLUMNS


def build_rule_based_risk_label(frame: pd.DataFrame) -> pd.Series:
    penalties = (
        (frame['debt_ratio_pct'].fillna(0) > 60).astype(int)
        + (frame['cash_to_short_debt'].fillna(0) < 1).astype(int)
        + (frame['operating_cashflow_million'].fillna(0) < 0).astype(int)
        + (frame['current_ratio'].fillna(99) < 1.2).astype(int)
    )
    return (penalties >= 2).astype(int)


def build_feature_frame(financials: pd.DataFrame) -> pd.DataFrame:
    frame = financials.copy()
    if frame.empty:
        return frame
    frame['company_code'] = frame['company_code'].astype(str)
    frame['report_year'] = frame['report_year'].astype(int)
    frame = frame.sort_values(['company_code', 'report_year']).reset_index(drop=True)
    frame['rule_risk_label'] = build_rule_based_risk_label(frame)

    grouped = frame.groupby('company_code', group_keys=False)
    frame['revenue_yoy_pct'] = grouped['revenue_million'].pct_change().replace([np.inf, -np.inf], np.nan) * 100
    frame['profit_yoy_pct'] = grouped['net_profit_million'].pct_change().replace([np.inf, -np.inf], np.nan) * 100
    frame['cashflow_yoy_change_million'] = grouped['operating_cashflow_million'].diff()
    frame['debt_ratio_change_pct'] = grouped['debt_ratio_pct'].diff()
    frame['current_ratio_change'] = grouped['current_ratio'].diff()
    frame['future_risk_label'] = grouped['rule_risk_label'].shift(-1)
    frame['prediction_year'] = frame['report_year'] + 1
    return frame


class RiskModelService:
    def __init__(
        self,
        artifact_path: Path | None = None,
    ) -> None:
        model_dir = settings.cache_dir / 'models'
        self.artifact_path = artifact_path or (model_dir / 'risk_tabular_model.json')
        self._artifact: dict[str, Any] | None = None
        self._load_if_available()

    def _load_if_available(self) -> None:
        if self.artifact_path.exists():
            self._artifact = json.loads(self.artifact_path.read_text(encoding='utf-8'))

    def is_ready(self) -> bool:
        return self._artifact is not None

    def get_summary(self) -> dict:
        if not self.is_ready():
            return {
                'model_ready': False,
                'model_type': None,
                'trained_at': None,
                'sample_count': 0,
                'positive_samples': 0,
                'metrics': {},
                'feature_columns': MODEL_FEATURE_COLUMNS,
            }
        return {
            'model_ready': True,
            'model_type': self._artifact.get('model_type'),
            'trained_at': self._artifact.get('trained_at'),
            'sample_count': int(self._artifact.get('sample_count') or 0),
            'positive_samples': int(self._artifact.get('positive_samples') or 0),
            'metrics': self._artifact.get('metrics', {}),
            'feature_columns': self._artifact.get('feature_columns', MODEL_FEATURE_COLUMNS),
        }

    def build_latest_feature_row(self, company_history: list[dict]) -> pd.DataFrame:
        frame = pd.DataFrame(company_history)
        if frame.empty:
            return pd.DataFrame(columns=['company_code', 'report_year'] + MODEL_FEATURE_COLUMNS)
        feature_frame = build_feature_frame(frame)
        latest = feature_frame.sort_values('report_year').tail(1).copy()
        for column in MODEL_FEATURE_COLUMNS:
            if column not in latest:
                latest[column] = 0.0
        latest[MODEL_FEATURE_COLUMNS] = latest[MODEL_FEATURE_COLUMNS].astype(float)
        return latest[['company_code', 'report_year'] + MODEL_FEATURE_COLUMNS].reset_index(drop=True)

    def _prepare_vector(self, latest: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
        feature_columns: list[str] = self._artifact.get('feature_columns', MODEL_FEATURE_COLUMNS)
        imputer_statistics = np.asarray(self._artifact.get('imputer_statistics', [0.0] * len(feature_columns)), dtype=float)
        scaler_mean = np.asarray(self._artifact.get('scaler_mean', [0.0] * len(feature_columns)), dtype=float)
        scaler_scale = np.asarray(self._artifact.get('scaler_scale', [1.0] * len(feature_columns)), dtype=float)
        raw = latest[feature_columns].astype(float).to_numpy()[0]
        raw = np.where(np.isnan(raw), imputer_statistics, raw)
        safe_scale = np.where(scaler_scale == 0, 1.0, scaler_scale)
        scaled = (raw - scaler_mean) / safe_scale
        return scaled, feature_columns

    def predict_company(self, company_history: list[dict]) -> dict | None:
        if not self.is_ready():
            return None
        latest = self.build_latest_feature_row(company_history)
        if latest.empty:
            return None

        scaled, feature_columns = self._prepare_vector(latest)
        coefficients = np.asarray(self._artifact.get('coefficients', [0.0] * len(feature_columns)), dtype=float)
        intercept = float(self._artifact.get('intercept', 0.0))
        logit = float(np.dot(scaled, coefficients) + intercept)
        probability = 1.0 / (1.0 + math.exp(-logit))

        contributions: list[dict[str, Any]] = []
        for feature, contribution in sorted(
            ((feature, float(value * coef)) for feature, value, coef in zip(feature_columns, scaled, coefficients)),
            key=lambda item: abs(item[1]),
            reverse=True,
        )[:5]:
            contributions.append(
                {
                    'feature': feature,
                    'contribution': round(contribution, 4),
                    'direction': 'risk_up' if contribution >= 0 else 'risk_down',
                }
            )

        return {
            'company_code': str(latest.iloc[0]['company_code']),
            'report_year': int(latest.iloc[0]['report_year']),
            'high_risk_probability': round(probability, 4),
            'predicted_score': round(probability * 100, 1),
            'top_contributions': contributions,
            'model_summary': self.get_summary(),
        }

    def save_artifact(self, payload: dict[str, Any]) -> None:
        self.artifact_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {'trained_at': payload.get('trained_at') or datetime.now().isoformat(timespec='seconds'), **payload}
        self.artifact_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        self._artifact = payload
