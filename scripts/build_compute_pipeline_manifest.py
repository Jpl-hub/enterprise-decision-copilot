from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUALITY_DIR = ROOT / "data" / "quality"
OUT_PATH = QUALITY_DIR / "compute_pipeline_manifest.json"
WAREHOUSE_SUMMARY_PATH = QUALITY_DIR / "warehouse_summary.json"
QUALITY_REPORT_PATH = QUALITY_DIR / "quality_report.json"


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    warehouse = read_json(WAREHOUSE_SUMMARY_PATH)
    quality_report = read_json(QUALITY_REPORT_PATH)

    mart_views = list(warehouse.get("mart_views") or [])
    parquet_count = len(quality_report.get("parquet_artifacts") or [])

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "current_engine": "python + duckdb",
        "next_engine": "spark-ready batch",
        "warehouse_db": warehouse.get("warehouse_db"),
        "parquet_artifact_count": parquet_count,
        "mart_views": mart_views,
        "jobs": [
            {
                "job_id": "bronze_to_silver_governance",
                "stage": "数据清洗",
                "current_engine": "python",
                "spark_ready": True,
                "inputs": ["lake/bronze/*.parquet"],
                "outputs": ["lake/silver/*.parquet"],
                "partition_keys": ["dataset_name", "report_year"],
                "goal": "把原始财报、研报、宏观和企业池数据清洗到可分析层。",
            },
            {
                "job_id": "silver_to_gold_company_fact",
                "stage": "主题汇总",
                "current_engine": "duckdb",
                "spark_ready": True,
                "inputs": ["lake/silver/financial_features", "lake/silver/research_reports"],
                "outputs": ["lake/gold/company_fact", "mart.company_overview"],
                "partition_keys": ["company_code", "report_year"],
                "goal": "把企业经营、研报情绪和风险特征汇总成主题事实表。",
            },
            {
                "job_id": "multimodal_extract_batch",
                "stage": "多模态解析",
                "current_engine": "python + vision api",
                "spark_ready": True,
                "inputs": ["raw/official/**/*.pdf"],
                "outputs": ["cache/official_page_images", "cache/official_extract_multimodal"],
                "partition_keys": ["company_code", "report_year"],
                "goal": "批量解析财报图表页，补齐文本抽取缺失字段。",
            },
            {
                "job_id": "multimodal_sft_dataset_build",
                "stage": "训练数据构建",
                "current_engine": "python",
                "spark_ready": True,
                "inputs": ["cache/official_extract_multimodal", "cache/official_extract", "processed/financial_features_official.csv"],
                "outputs": ["data/datasets/official_multimodal_sft.jsonl"],
                "partition_keys": ["company_code", "report_year"],
                "goal": "把图像、文本证据和标签整理成后续微调可直接消费的样本。",
            },
            {
                "job_id": "risk_model_training",
                "stage": "风险训练",
                "current_engine": "python / sklearn / tensorflow",
                "spark_ready": True,
                "inputs": ["processed/financial_features.csv", "lake/gold/company_fact"],
                "outputs": ["cache/models/risk_tabular_model.json", "cache/models/risk_lstm.keras"],
                "partition_keys": ["company_code", "report_year"],
                "goal": "训练表格风险模型和序列风险模型，形成可复用模型产物。",
            },
        ],
    }

    OUT_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(OUT_PATH), "job_count": len(manifest["jobs"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
