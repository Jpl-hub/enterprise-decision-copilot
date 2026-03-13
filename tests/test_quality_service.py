import asyncio
import json
import shutil
import uuid
from pathlib import Path

import pandas as pd

from app.api.routes.quality import (
    get_governance_summary,
    get_preparation_summary,
    get_quality_summary,
    get_retrieval_evaluation_summary,
    get_trust_center_summary,
    submit_manual_review,
    sync_auto_reviews,
)
from app.schemas.quality import ManualReviewRequest
from app.services.audit import AuditService
from app.services.quality import DataQualityService



def build_quality_service(base_dir: Path) -> DataQualityService:
    base_dir.mkdir(parents=True, exist_ok=True)
    official_quality = base_dir / "financial_features_official_quality.csv"
    inventory_quality = base_dir / "official_reports_quality.json"
    inventory = base_dir / "report_inventory.csv"
    review_queue = base_dir / "manual_review_queue.csv"
    multimodal_dir = base_dir / "official_extract_multimodal"
    source_registry = base_dir / "source_registry.csv"
    script_dir = base_dir / "scripts"
    multimodal_dir.mkdir(parents=True, exist_ok=True)
    script_dir.mkdir(parents=True, exist_ok=True)

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

    source_registry.write_text(
        "source_type,source_name,domain,entry_url,usage_scope,compliance_note,priority\n"
        "financial,SSE regular reports,query.sse.com.cn,https://www.sse.com.cn/disclosure/listedinfo/regular/,定期报告,公开披露,P0\n"
        "financial,SZSE regular reports,www.szse.cn,https://www.szse.cn/disclosure/listed/fixed/index.html,定期报告,公开披露,P0\n"
        "financial,BSE announcements,www.bse.cn,https://www.bse.cn/disclosure/announcement.html,定期报告,公开披露,P0\n"
        "research,Eastmoney stock reports,data.eastmoney.com,https://data.eastmoney.com/report/stock.jshtml,个股研报,公开接口,P0\n"
        "research,Eastmoney industry reports,data.eastmoney.com,https://data.eastmoney.com/report/industry.jshtml,行业研报,公开接口,P1\n"
        "macro,NBS stats,stats.gov.cn,https://www.stats.gov.cn/sj/,宏观指标,公开披露,P0\n",
        encoding="utf-8-sig",
    )
    (script_dir / "legacy_bootstrap.py").write_text(
        "URL = 'https://legacy.example.com/raw.pdf'\n",
        encoding="utf-8",
    )

    (multimodal_dir / "300760_2024.json").write_text(
        json.dumps(
            {
                "company_code": "300760",
                "company_name": "迈瑞医疗",
                "report_year": 2024,
                "backend": "modelscope",
                "model_id": "Qwen/Qwen2.5-VL-7B-Instruct",
                "source_url": "https://example.com/report.pdf",
                "page_images": ["data/cache/official_page_images/300760_2024/page_01.png"],
                "field_sources": {"revenue_million": "page 1"},
                "notes": ["由多模态模型抽取"],
                "revenue_million": 1000.0,
                "net_profit_million": 200.0,
                "roe_pct": 20.5,
                "debt_ratio_pct": 31.2,
                "current_ratio": 1.8,
                "cash_to_short_debt": 2.4,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return DataQualityService(
        official_quality_path=official_quality,
        inventory_quality_path=inventory_quality,
        inventory_path=inventory,
        review_queue_path=review_queue,
        multimodal_extract_dir=multimodal_dir,
        source_registry_path=source_registry,
        script_dir=script_dir,
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
    assert summary["target_pool_ready"] is False
    assert summary["universe_report_expected_slots"] == 18
    assert summary["issue_breakdown"]["missing_reports"] == 1
    assert summary["anomaly_company_count"] == 1
    assert summary["multimodal_extract_report_count"] == 1
    assert summary["multimodal_extract_coverage_ratio"] == 1.0
    assert summary["multimodal_backends"] == ["modelscope"]
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



def test_quality_service_returns_company_multimodal_snapshot() -> None:
    base_dir = create_test_dir()
    try:
        service = build_quality_service(base_dir)
        snapshot = service.get_company_quality_snapshot("300760")
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    assert snapshot["multimodal_extract_count"] == 1
    assert snapshot["multimodal_extracts"][0]["backend"] == "modelscope"
    assert snapshot["multimodal_extracts"][0]["filled_field_count"] >= 6


def test_quality_service_returns_real_preparation_summary() -> None:
    service = DataQualityService()
    summary = service.get_preparation_summary()

    assert summary["promotion_candidate_count"] >= summary["selected_candidate_count"] >= 0
    assert summary["promoted_report_download_count"] >= 0
    assert summary["promoted_report_missing_count"] >= 0
    assert len(summary["promotion_years"]) >= 1
    assert summary["promoted_report_download_count"] + summary["promoted_report_missing_count"] >= summary["selected_candidate_count"]
    assert isinstance(summary["promoted_exchange_status"], list)
    assert isinstance(summary["promoted_companies"], list)
    if summary["promoted_companies"]:
        first = summary["promoted_companies"][0]
        assert "downloaded_years" in first
        assert "missing_years" in first



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
    audit_db = Path("data") / "test_quality_audit" / uuid.uuid4().hex / "app.db"
    audit_service = AuditService(audit_db)
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
                current_user={'user_id': 'tester'},
                quality_service=service,
                audit_service=audit_service,
            )
        )
        auto_payload = asyncio.run(sync_auto_reviews(limit=3, current_user={'user_id': 'tester'}, quality_service=service, audit_service=audit_service))
        logs = audit_service.list_recent(limit=10)
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)
        if audit_db.parent.exists():
            shutil.rmtree(audit_db.parent, ignore_errors=True)

    assert summary["official_report_expected_slots"] == 18
    assert summary["multimodal_extract_report_count"] == 1
    assert response["review"]["company_code"] == "300760"
    assert response["summary"]["pending_review_count"] == 1
    assert auto_payload["created_count"] >= 1
    assert auto_payload["summary"]["pending_review_count"] >= 2
    assert any(item['event_type'] == 'quality.review.submit' for item in logs)
    assert any(item['event_type'] == 'quality.review.auto_sync' for item in logs)


def test_quality_route_returns_preparation_payload() -> None:
    payload = asyncio.run(get_preparation_summary(quality_service=DataQualityService()))

    assert payload["promotion_candidate_count"] >= payload["selected_candidate_count"] >= 0
    assert "promoted_exchange_status" in payload
    assert "promoted_companies" in payload


def test_quality_route_returns_governance_payload() -> None:
    payload = asyncio.run(get_governance_summary(quality_service=DataQualityService()))

    assert payload["source_catalog"]
    assert payload["company_coverage"]
    assert payload["field_quality"]
    assert payload["evidence_mapping"]


def test_quality_service_returns_trust_center_summary() -> None:
    base_dir = create_test_dir()
    try:
        service = build_quality_service(base_dir)
        payload = service.get_trust_center_summary()
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    assert payload["source_alignment"]["registry_source_count"] == 6
    assert payload["source_alignment"]["legacy_script_issue_count"] == 1
    assert payload["observed_domains"]
    assert any(item["domain"] == "data.eastmoney.com" for item in payload["observed_domains"])
    assert payload["freshness_watchlist"]
    assert payload["findings"]
    assert payload["next_actions"]


def test_quality_route_returns_trust_center_payload() -> None:
    payload = asyncio.run(get_trust_center_summary(quality_service=DataQualityService()))

    assert payload["source_alignment"]["registry_source_count"] >= 6
    assert payload["observed_domains"]
    assert payload["freshness_watchlist"]
    assert payload["next_actions"]


def test_quality_service_returns_retrieval_evaluation_summary() -> None:
    payload = DataQualityService().get_retrieval_evaluation_summary()

    assert payload["case_count"] >= 1
    assert payload["retrieval_mode"] == "hybrid_tfidf_rerank"
    assert payload["strategy_labels"]
    assert len(payload["strategy_benchmarks"]) == 3
    assert payload["best_mode"]
    assert payload["comparison_notes"]
    assert payload["cases"]
    assert "hit_at_3" in payload


def test_quality_route_returns_retrieval_evaluation_payload() -> None:
    payload = asyncio.run(get_retrieval_evaluation_summary(quality_service=DataQualityService()))

    assert payload["case_count"] >= 1
    assert payload["strategy_benchmarks"]
    assert payload["cases"]
