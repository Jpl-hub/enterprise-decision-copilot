import asyncio
import json
import shutil
import uuid
from pathlib import Path

import pandas as pd

from app.api.routes.quality import get_quality_summary, submit_manual_review, sync_auto_reviews
from app.schemas.quality import ManualReviewRequest
from app.services.quality import DataQualityService


def build_quality_service(base_dir: Path) -> DataQualityService:
    base_dir.mkdir(parents=True, exist_ok=True)
    official_quality = base_dir / "financial_features_official_quality.csv"
    inventory_quality = base_dir / "official_reports_quality.json"
    inventory = base_dir / "report_inventory.csv"
    review_queue = base_dir / "manual_review_queue.csv"

    pd.DataFrame(
        [
            {
                "company_code": "300760",
                "company_name": "迈瑞医疗",
                "report_year": 2024,
                "filled_fields": 10,
                "field_coverage_ratio": 0.8333,
                "critical_fields_missing": "gross_margin_pct,current_ratio",
                "anomaly_flags": "receivable_turnover:outlier",
            },
            {
                "company_code": "688271",
                "company_name": "联影医疗",
                "report_year": 2024,
                "filled_fields": 12,
                "field_coverage_ratio": 1.0,
                "critical_fields_missing": "",
                "anomaly_flags": "",
            },
        ]
    ).to_csv(official_quality, index=False, encoding="utf-8-sig")

    inventory.write_text(
        "exchange,company_code,disclosure_company_code,company_name,year,title,published_at,source_url,local_path,file_exists,size_bytes,status,manifest_path\n"
        "SZSE,300760,300760,迈瑞医疗,2024,迈瑞医疗：2024年年度报告,2025-04-29,https://example.com/report.pdf,data/raw/official/szse/pdfs/300760_2024_annual_szse.pdf,True,100,downloaded,data/raw/official/szse/report_manifest.json\n",
        encoding="utf-8-sig",
    )

    inventory_quality.write_text(
        json.dumps(
            {
                "target_coverage": {
                    "coverage_ratio": 0.8889,
                    "downloaded_slots": 16,
                    "expected_slots": 18,
                    "missing_slots": [{"company_code": "920047", "company_name": "N锦华", "exchange": "BSE", "year": 2024}],
                },
                "exchanges": [
                    {"exchange": "SSE", "manifest_exists": True, "rows": 12, "downloaded_rows": 12, "file_missing_rows": 0, "companies": ["600276"]},
                    {"exchange": "SZSE", "manifest_exists": True, "rows": 6, "downloaded_rows": 6, "file_missing_rows": 0, "companies": ["300760"]},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return DataQualityService(
        official_quality_path=official_quality,
        inventory_quality_path=inventory_quality,
        inventory_path=inventory,
        review_queue_path=review_queue,
    )


def create_test_dir() -> Path:
    base_dir = Path("data") / "test_quality" / uuid.uuid4().hex
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def test_quality_service_builds_summary() -> None:
    base_dir = create_test_dir()
    try:
        service = build_quality_service(base_dir)
        summary = service.get_quality_summary()
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    assert summary["official_report_coverage_ratio"] == 0.8889
    assert summary["missing_report_slots"] == 1
    assert summary["anomaly_company_count"] == 1
    assert summary["top_anomalies"][0]["company_code"] == "300760"
    assert summary["top_anomalies"][0]["financial_source_url"] == "https://example.com/report.pdf"


def test_quality_service_persists_manual_review() -> None:
    base_dir = create_test_dir()
    try:
        service = build_quality_service(base_dir)
        record = service.submit_manual_review(
            company_code="300760",
            report_year=2024,
            finding_level="high",
            finding_type="净利率异常",
            note="需要人工核对利润表和主要会计数据表。",
        )
        queue = service.get_review_queue()
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    assert record["status"] == "pending"
    assert len(queue) == 1
    assert queue[0]["finding_type"] == "净利率异常"


def test_quality_service_can_sync_auto_reviews() -> None:
    base_dir = create_test_dir()
    try:
        service = build_quality_service(base_dir)
        first = service.sync_auto_review_queue(limit=5)
        second = service.sync_auto_review_queue(limit=5)
        queue = service.get_review_queue()
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    assert first["created_count"] >= 2
    assert second["created_count"] == 0
    assert second["skipped_count"] >= 1
    assert len(queue) == first["created_count"]


def test_quality_routes_return_summary_and_accept_review() -> None:
    base_dir = create_test_dir()
    try:
        service = build_quality_service(base_dir)
        summary = asyncio.run(get_quality_summary(quality_service=service))
        response = asyncio.run(
            submit_manual_review(
                payload=ManualReviewRequest(
                    company_code="300760",
                    report_year=2024,
                    finding_level="medium",
                    finding_type="现金短债比待核验",
                    note="货币资金和短期债务来源表格需要人工校对。",
                ),
                quality_service=service,
            )
        )
        auto_payload = asyncio.run(sync_auto_reviews(limit=3, quality_service=service))
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    assert summary["official_report_expected_slots"] == 18
    assert response["review"]["company_code"] == "300760"
    assert response["summary"]["pending_review_count"] == 1
    assert auto_payload["created_count"] >= 1
    assert auto_payload["summary"]["pending_review_count"] >= 2
