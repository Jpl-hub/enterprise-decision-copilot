import asyncio
import shutil
import uuid
from pathlib import Path

from app.api.routes.competition import get_company_competition_package
from app.core.container import build_service_container
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

    try:
        payload = asyncio.run(
            get_company_competition_package(
                company_code="300760",
                question="结合真实数据生成企业运营分析答辩稿",
                persist=True,
                competition_report_service=service,
            )
        )
        assert payload["company_code"] == "300760"
        assert payload["sections"]
        assert payload["citations"]
        assert payload["markdown_path"]
    finally:
        if export_root.exists():
            shutil.rmtree(export_root, ignore_errors=True)
