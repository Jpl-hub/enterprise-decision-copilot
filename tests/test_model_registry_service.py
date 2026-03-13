from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

from app.services.model_registry import ModelRegistryService


def test_model_registry_service_reads_standardized_artifacts() -> None:
    base_dir = Path('data') / 'test_model_registry' / uuid.uuid4().hex
    model_dir = base_dir / 'models'
    dataset_dir = base_dir / 'datasets'
    multimodal_dir = base_dir / 'multimodal'
    model_dir.mkdir(parents=True, exist_ok=True)
    dataset_dir.mkdir(parents=True, exist_ok=True)
    multimodal_dir.mkdir(parents=True, exist_ok=True)

    try:
        (model_dir / 'risk_tabular_model.json').write_text(
            json.dumps(
                {
                    'sample_count': 18,
                    'positive_samples': 7,
                    'metrics': {'roc_auc': 0.8123},
                },
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )
        (model_dir / 'risk_tabular_metadata.json').write_text(
            json.dumps({'sample_count': 18, 'positive_samples': 7}, ensure_ascii=False),
            encoding='utf-8',
        )
        (model_dir / 'risk_lstm.keras').write_text('stub-model', encoding='utf-8')
        (model_dir / 'risk_lstm_metrics.json').write_text(
            json.dumps(
                {
                    'sample_count': 12,
                    'sequence_length': 3,
                    'best_val_auc': 0.7432,
                },
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )
        (multimodal_dir / '300760_2024.json').write_text('{"ok": true}', encoding='utf-8')
        (dataset_dir / 'official_multimodal_sft.jsonl').write_text(
            '{"input": "a"}\n{"input": "b"}\n',
            encoding='utf-8',
        )

        service = ModelRegistryService(
            model_dir=model_dir,
            dataset_dir=dataset_dir,
            multimodal_dir=multimodal_dir,
        )
        payload = service.get_summary()
        items = {item['model_id']: item for item in payload['items']}
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    assert payload['registry_ready'] is True
    assert payload['model_count'] == 4
    assert payload['active_count'] == 4
    assert items['risk-tabular']['metric_value'] == '0.812'
    assert items['risk-sequence']['metric_value'] == '0.743'
    assert items['risk-sequence']['notes'][0] == '序列长度 3 年窗口'
    assert items['multimodal-extractor']['sample_count'] == 1
    assert items['multimodal-sft']['sample_count'] == 2
