import asyncio
import shutil
import uuid
from pathlib import Path

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
        assert package["markdown_path"]
        assert package["evidence_path"]
        assert Path(package["markdown_path"]).exists()
        assert Path(package["evidence_path"]).exists()
        assert "## 关键判断" in package["markdown_content"]
        assert package["quality_snapshot"]["official_report_coverage_ratio"] >= 0
        assert "multimodal_extract_count" in package["quality_snapshot"]
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
        assert payload["markdown_path"]
        assert any("多模态" in section["content"] for section in payload["sections"])
        logs = audit_service.list_recent(limit=5)
        assert any(item['event_type'] == 'competition.package.export' for item in logs)
    finally:
        if export_root.exists():
            shutil.rmtree(export_root, ignore_errors=True)
        if audit_service.db_path and audit_service.db_path.parent.exists():
            shutil.rmtree(audit_service.db_path.parent, ignore_errors=True)
