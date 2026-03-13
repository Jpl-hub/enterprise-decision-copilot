import asyncio
import shutil
import uuid
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api.routes.competition import get_company_competition_package
from app.core.container import build_service_container
from app.services.audit import AuditService
from app.services.competition_report import CompetitionReportService



def test_competition_report_service_exports_files() -> None:
    container = build_service_container()
    export_root = Path("data/test_exports") / uuid.uuid4().hex
    service = CompetitionReportService(
        analytics_service=container.analytics_service,
        decision_service=container.decision_service,
        risk_service=container.risk_service,
        quality_service=container.quality_service,
        export_root=export_root,
    )

    try:
        package = service.build_company_competition_package("300760", persist=True)
        assert package is not None
        assert package["citation_count"] >= 3
        assert package["citations"][0]["citation_id"] == "E1"
        assert package["brief_verdict"]
        assert package["risk_level"]
        assert package["evidence_digest"]["semantic_stock_count"] >= 0
        assert package["markdown_path"]
        assert package["evidence_path"]
        assert Path(package["markdown_path"]).exists()
        assert Path(package["evidence_path"]).exists()
        assert "## 关键判断" in package["markdown_content"]
        assert package["quality_snapshot"]["official_report_coverage_ratio"] >= 0
        assert "multimodal_extract_count" in package["quality_snapshot"]
        assert package["data_authenticity"]["trust_status"] == "trusted"
        assert package["publication_gate"]["export_allowed"] is True
        assert "## 真实性声明" in package["markdown_content"]
    finally:
        if export_root.exists():
            shutil.rmtree(export_root, ignore_errors=True)



def test_competition_package_route_returns_export_payload() -> None:
    container = build_service_container()
    export_root = Path("data/test_exports") / uuid.uuid4().hex
    service = CompetitionReportService(
        analytics_service=container.analytics_service,
        decision_service=container.decision_service,
        risk_service=container.risk_service,
        quality_service=container.quality_service,
        export_root=export_root,
    )
    audit_service = AuditService(Path("data/test_exports") / uuid.uuid4().hex / "app.db")

    try:
        payload = asyncio.run(
            get_company_competition_package(
                company_code="300760",
                question="结合真实数据生成企业运营分析答辩稿",
                persist=True,
                current_user={'user_id': 'tester'},
                competition_report_service=service,
                audit_service=audit_service,
            )
        )
        assert payload["company_code"] == "300760"
        assert payload["sections"]
        assert payload["citations"]
        assert payload["brief_verdict"]
        assert payload["risk_level"]
        assert "pending_review_count" in payload["evidence_digest"]
        assert payload["markdown_path"]
        assert any("多模态" in section["content"] for section in payload["sections"])
        assert payload["publication_gate"]["export_allowed"] is True
        logs = audit_service.list_recent(limit=5)
        assert any(item['event_type'] == 'competition.package.export' for item in logs)
    finally:
        if export_root.exists():
            shutil.rmtree(export_root, ignore_errors=True)
        if audit_service.db_path and audit_service.db_path.parent.exists():
            shutil.rmtree(audit_service.db_path.parent, ignore_errors=True)


def test_competition_report_service_marks_package_for_review_when_company_has_pending_findings() -> None:
    container = build_service_container()
    export_root = Path("data/test_exports") / uuid.uuid4().hex

    class ReviewFlagQualityService:
        def __init__(self, base) -> None:
            self.base = base

        def get_company_quality_snapshot(self, company_code: str) -> dict:
            snapshot = dict(self.base.get_company_quality_snapshot(company_code))
            snapshot["company_anomalies"] = [{"finding": "净利率待复核"}]
            snapshot["company_review_queue"] = [{"finding": "人工复核未关闭"}]
            return snapshot

        def get_trust_center_summary(self) -> dict:
            return self.base.get_trust_center_summary()

    service = CompetitionReportService(
        analytics_service=container.analytics_service,
        decision_service=container.decision_service,
        risk_service=container.risk_service,
        quality_service=ReviewFlagQualityService(container.quality_service),
        export_root=export_root,
    )

    try:
        package = service.build_company_competition_package("300760", persist=False)
        assert package is not None
        assert package["publication_gate"]["gate_status"] == "review_required"
        assert package["publication_gate"]["enterprise_ready"] is False
        assert package["publication_gate"]["export_allowed"] is True
        assert package["publication_gate"]["warnings"]
    finally:
        if export_root.exists():
            shutil.rmtree(export_root, ignore_errors=True)


def test_competition_package_route_blocks_persist_when_release_gate_fails() -> None:
    container = build_service_container()
    export_root = Path("data/test_exports") / uuid.uuid4().hex
    audit_service = AuditService(Path("data/test_exports") / uuid.uuid4().hex / "app.db")

    class BlockingQualityService:
        def __init__(self, base) -> None:
            self.base = base

        def get_company_quality_snapshot(self, company_code: str) -> dict:
            return self.base.get_company_quality_snapshot(company_code)

        def get_trust_center_summary(self) -> dict:
            payload = dict(self.base.get_trust_center_summary())
            payload["trust_status"] = "watch"
            return payload

    service = CompetitionReportService(
        analytics_service=container.analytics_service,
        decision_service=container.decision_service,
        risk_service=container.risk_service,
        quality_service=BlockingQualityService(container.quality_service),
        export_root=export_root,
    )

    try:
        with pytest.raises(HTTPException) as excinfo:
            asyncio.run(
                get_company_competition_package(
                    company_code="300760",
                    question="结合真实数据生成企业运营分析答辩稿",
                    persist=True,
                    current_user={'user_id': 'tester'},
                    competition_report_service=service,
                    audit_service=audit_service,
                )
            )
        assert excinfo.value.status_code == 409
    finally:
        if export_root.exists():
            shutil.rmtree(export_root, ignore_errors=True)
        if audit_service.db_path and audit_service.db_path.parent.exists():
            shutil.rmtree(audit_service.db_path.parent, ignore_errors=True)
