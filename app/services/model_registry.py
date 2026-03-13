from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.config import settings


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "scripts"


class ModelRegistryService:
    def __init__(
        self,
        model_dir: Path | None = None,
        dataset_dir: Path | None = None,
        multimodal_dir: Path | None = None,
    ) -> None:
        self.model_dir = model_dir or (settings.cache_dir / "models")
        self.dataset_dir = dataset_dir or (settings.data_dir / "datasets")
        self.multimodal_dir = multimodal_dir or (settings.cache_dir / "official_extract_multimodal")

    def _read_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _safe_path(self, path: Path) -> str | None:
        return str(path.resolve()) if path.exists() else None

    def _line_count(self, path: Path) -> int:
        if not path.exists() or not path.is_file():
            return 0
        with path.open("r", encoding="utf-8") as fp:
            return sum(1 for line in fp if line.strip())

    def _count_matching_files(self, folder: Path, pattern: str) -> int:
        if not folder.exists():
            return 0
        return len(list(folder.glob(pattern)))

    def _tabular_item(self) -> dict:
        model_path = self.model_dir / "risk_tabular_model.json"
        metadata_path = self.model_dir / "risk_tabular_metadata.json"
        payload = self._read_json(model_path)
        metadata = self._read_json(metadata_path)
        metrics = payload.get("metrics") or metadata.get("metrics") or {}
        sample_count = int(payload.get("sample_count") or metadata.get("sample_count") or 0)
        ready = model_path.exists()
        return {
            "model_id": "risk-tabular",
            "label": "表格风险模型",
            "status": "active" if ready else "warming_up",
            "stage_label": "已落盘" if ready else "待训练",
            "artifact_path": self._safe_path(model_path),
            "sample_count": sample_count,
            "metric_label": "ROC-AUC" if metrics.get("roc_auc") is not None else None,
            "metric_value": f"{float(metrics.get('roc_auc')):.3f}" if metrics.get("roc_auc") is not None else None,
            "notes": [
                f"训练样本 {sample_count} 条",
                f"正样本 {int(payload.get('positive_samples') or metadata.get('positive_samples') or 0)} 条",
            ],
        }

    def _sequence_item(self) -> dict:
        model_path = self.model_dir / "risk_lstm.keras"
        metrics_path = self.model_dir / "risk_lstm_metrics.json"
        payload = self._read_json(metrics_path)
        script_ready = (SCRIPT_DIR / "train_risk_sequence_model.py").exists()
        active = model_path.exists()
        return {
            "model_id": "risk-sequence",
            "label": "时序风险模型",
            "status": "active" if active else ("building" if script_ready else "warming_up"),
            "stage_label": "已产出模型" if active else ("脚本已就绪" if script_ready else "未接入"),
            "artifact_path": self._safe_path(model_path),
            "sample_count": int(payload.get("sample_count") or 0),
            "metric_label": "验证 AUC" if payload.get("best_val_auc") is not None else None,
            "metric_value": f"{float(payload.get('best_val_auc')):.3f}" if payload.get("best_val_auc") is not None else None,
            "notes": [
                f"序列长度 {int(payload.get('sequence_length') or 3)} 年窗口",
                "需继续补统一评测与模型治理流程。",
            ],
        }

    def _multimodal_item(self) -> dict:
        extract_count = self._count_matching_files(self.multimodal_dir, "*.json")
        script_ready = (SCRIPT_DIR / "extract_official_financial_panel_multimodal.py").exists()
        return {
            "model_id": "multimodal-extractor",
            "label": "多模态财报抽取",
            "status": "active" if extract_count else ("building" if script_ready else "warming_up"),
            "stage_label": "抽取结果入链" if extract_count else ("脚本已就绪" if script_ready else "未接入"),
            "artifact_path": self._safe_path(self.multimodal_dir),
            "sample_count": extract_count,
            "metric_label": "抽取样本",
            "metric_value": str(extract_count),
            "notes": [
                "负责把复杂图表页转成结构化字段和锚点证据。",
                "抽取结果会回流到企业分析与质量治理链路。",
            ],
        }

    def _sft_item(self) -> dict:
        dataset_path = self.dataset_dir / "official_multimodal_sft.jsonl"
        sample_count = self._line_count(dataset_path)
        script_ready = (SCRIPT_DIR / "build_multimodal_sft_dataset.py").exists()
        return {
            "model_id": "multimodal-sft",
            "label": "多模态 SFT 数据集",
            "status": "active" if sample_count else ("building" if script_ready else "warming_up"),
            "stage_label": "可用于微调" if sample_count else ("脚本已就绪" if script_ready else "未接入"),
            "artifact_path": self._safe_path(dataset_path),
            "sample_count": sample_count,
            "metric_label": "样本数",
            "metric_value": str(sample_count),
            "notes": [
                "用于后续 LoRA / ModelScope 微调实验。",
                "当前样本量仍需继续扩充。",
            ],
        }

    def get_summary(self) -> dict:
        items = [
            self._tabular_item(),
            self._sequence_item(),
            self._multimodal_item(),
            self._sft_item(),
        ]
        active_count = sum(1 for item in items if item["status"] == "active")
        building_count = sum(1 for item in items if item["status"] == "building")
        priority_actions = [
            "优先把时序风险模型补出 metrics 文件和稳定产物，避免只停留在训练脚本。",
            "继续扩充多模态抽取与 SFT 样本，把模型实验从脚手架推进到可评测阶段。",
            "把模型注册表接入后续批任务和审计链，形成统一 ModelOps 入口。",
        ]
        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "registry_ready": any(item["status"] == "active" for item in items),
            "model_count": len(items),
            "active_count": active_count,
            "building_count": building_count,
            "items": items,
            "priority_actions": priority_actions,
        }
