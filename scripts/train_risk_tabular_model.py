from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings
from app.services.risk_model import MODEL_FEATURE_COLUMNS, RiskModelService, build_feature_frame


def load_financial_panel() -> pd.DataFrame:
    path = settings.processed_dir / 'financial_features.csv'
    if not path.exists():
        raise FileNotFoundError(f'未找到文件：{path}')
    frame = pd.read_csv(path, dtype={'company_code': str})
    if frame.empty:
        raise ValueError('financial_features.csv 为空，无法训练。')
    return frame


def build_training_dataset(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    feature_frame = build_feature_frame(frame)
    training = feature_frame[feature_frame['future_risk_label'].notna()].copy()
    if training.empty:
        raise ValueError('未来风险标签为空，无法训练。')
    x = training[MODEL_FEATURE_COLUMNS].astype(float).replace([np.inf, -np.inf], np.nan)
    y = training['future_risk_label'].astype(int)
    return x, y


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)),
        ]
    )


def evaluate_model(pipeline: Pipeline, x: pd.DataFrame, y: pd.Series) -> dict:
    positive_samples = int(y.sum())
    negative_samples = int((1 - y).sum())
    if positive_samples == 0 or negative_samples == 0:
        raise ValueError('风险标签只有单一类别，无法训练分类模型。')

    n_splits = min(3, positive_samples, negative_samples)
    if n_splits >= 2:
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        probabilities = cross_val_predict(pipeline, x, y, cv=cv, method='predict_proba')[:, 1]
        predictions = (probabilities >= 0.5).astype(int)
    else:
        pipeline.fit(x, y)
        probabilities = pipeline.predict_proba(x)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)

    return {
        'accuracy': round(float(accuracy_score(y, predictions)), 4),
        'precision': round(float(precision_score(y, predictions, zero_division=0)), 4),
        'recall': round(float(recall_score(y, predictions, zero_division=0)), 4),
        'f1': round(float(f1_score(y, predictions, zero_division=0)), 4),
        'roc_auc': round(float(roc_auc_score(y, probabilities)), 4),
        'positive_rate': round(float(y.mean()), 4),
    }


def main() -> None:
    financials = load_financial_panel()
    x, y = build_training_dataset(financials)
    pipeline = build_pipeline()
    metrics = evaluate_model(pipeline, x, y)
    pipeline.fit(x, y)

    imputer = pipeline.named_steps['imputer']
    scaler = pipeline.named_steps['scaler']
    classifier = pipeline.named_steps['clf']

    payload = {
        'model_type': 'logistic_regression_tabular',
        'trained_at': datetime.now().isoformat(timespec='seconds'),
        'sample_count': int(len(x)),
        'positive_samples': int(y.sum()),
        'negative_samples': int((1 - y).sum()),
        'metrics': metrics,
        'feature_columns': MODEL_FEATURE_COLUMNS,
        'imputer_statistics': [float(value) for value in imputer.statistics_],
        'scaler_mean': [float(value) for value in scaler.mean_],
        'scaler_scale': [float(value) for value in scaler.scale_],
        'coefficients': [float(value) for value in classifier.coef_[0]],
        'intercept': float(classifier.intercept_[0]),
    }

    service = RiskModelService()
    service.save_artifact(payload)

    output = {
        'artifact_path': str(service.artifact_path),
        'metadata': payload,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
