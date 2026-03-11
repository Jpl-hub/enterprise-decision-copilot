from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.analytics import AnalyticsService
from app.services.decision import DecisionService
from app.services.quality import DataQualityService
from app.services.risk import RiskService


class CompetitionReportService:
    def __init__(
        self,
        analytics_service: AnalyticsService,
        decision_service: DecisionService,
        risk_service: RiskService,
        quality_service: DataQualityService,
        export_root: Path | None = None,
    ) -> None:
        self.analytics_service = analytics_service
        self.decision_service = decision_service
        self.risk_service = risk_service
        self.quality_service = quality_service
        self.export_root = export_root or (settings.data_dir / "exports" / "competition_packages")

    def _build_citations(self, report: dict, brief: dict) -> list[dict]:
        citations: list[dict] = []
        seen: set[tuple[str, str, str]] = set()

        def add_item(source_type: str, item: dict, title_key: str = "title", excerpt_key: str = "matched_excerpt") -> None:
            title = str(item.get(title_key) or "未命名来源").strip()
            source_url = str(item.get("source_url") or "").strip()
            report_date = str(item.get("report_date") or "").strip()
            key = (source_type, source_url, title)
            if key in seen:
                return
            seen.add(key)
            citations.append(
                {
                    "source_type": source_type,
                    "title": title,
                    "source_url": source_url or None,
                    "report_date": report_date or None,
                    "institution": str(item.get("institution") or item.get("industry_name") or "").strip() or None,
                    "excerpt": str(item.get(excerpt_key) or item.get("content") or title).strip(),
                }
            )

        financial_url = str(report.get("evidence", {}).get("financial_source_url") or "").strip()
        if financial_url:
            citations.append(
                {
                    "source_type": "official_financial_report",
                    "title": f"{report['company_name']}{report['report_year']}年年度报告",
                    "source_url": financial_url,
                    "report_date": None,
                    "institution": "交易所公告",
                    "excerpt": report.get("summary"),
                }
            )
            seen.add(("official_financial_report", financial_url, f"{report['company_name']}{report['report_year']}年年度报告"))

        for item in report.get("evidence", {}).get("research_reports", [])[:4]:
            add_item("stock_research_report", item, excerpt_key="title")
        for item in report.get("evidence", {}).get("industry_reports", [])[:4]:
            add_item("industry_research_report", item, excerpt_key="title")
        for item in brief.get("evidence", {}).get("semantic_stock_reports", [])[:4]:
            add_item("semantic_stock_evidence", item)
        for item in brief.get("evidence", {}).get("semantic_industry_reports", [])[:4]:
            add_item("semantic_industry_evidence", item)

        for idx, item in enumerate(citations, start=1):
            item["citation_id"] = f"E{idx}"
        return citations

    def _company_quality_snapshot(self, company_code: str) -> dict:
        summary = self.quality_service.get_quality_summary()
        anomalies = [
            item
            for item in self.quality_service.get_financial_anomalies(limit=50)
            if str(item.get("company_code") or "") == str(company_code)
        ]
        queue = [
            item
            for item in self.quality_service.get_review_queue()
            if str(item.get("company_code") or "") == str(company_code)
        ]
        return {
            "official_report_coverage_ratio": summary.get("official_report_coverage_ratio", 0.0),
            "pending_review_count": summary.get("pending_review_count", 0),
            "company_anomalies": anomalies[:5],
            "company_review_queue": queue[:5],
        }

    def _refs(self, citations: list[dict], start: int = 0, limit: int = 2) -> str:
        selected = citations[start : start + limit]
        if not selected:
            return ""
        return " " + "".join(f"[{item['citation_id']}]" for item in selected)

    def _build_sections(self, report: dict, brief: dict, risk: dict, quality_snapshot: dict, citations: list[dict]) -> list[dict]:
        sections = [
            {
                "title": "项目对象",
                "content": (
                    f"本答辩稿围绕 {report['company_name']} 展开，基于 {report['report_year']} 年真实披露财报、"
                    "近两年公开研报、行业研报与宏观指标生成经营分析与决策支持结论。"
                    f"{self._refs(citations, 0, 1)}"
                ),
            },
            {
                "title": "经营与趋势判断",
                "content": (
                    f"{report['summary']} {report['sections'][1]['content']} {report['sections'][2]['content']}"
                    f"{self._refs(citations, 0, 3)}"
                ),
            },
            {
                "title": "关键判断",
                "content": "；".join(brief.get("key_judgements", []) + brief.get("evidence_highlights", [])[:2]) + self._refs(citations, 1, 4),
            },
            {
                "title": "行动建议",
                "content": (
                    "；".join(brief.get("action_recommendations", []))
                    + (
                        f"。本轮问题命中主题词包括：{'、'.join(brief.get('evidence', {}).get('query_terms', []))}"
                        if brief.get("evidence", {}).get("query_terms")
                        else ""
                    )
                ),
            },
            {
                "title": "风险预测与监测",
                "content": (
                    f"{risk['summary']} 风险驱动：{'；'.join(risk.get('drivers', [])[:4])}。"
                    f"建议重点监测：{'；'.join(risk.get('monitoring_items', [])[:4])}。"
                ),
            },
            {
                "title": "数据质量与可追溯性",
                "content": (
                    f"当前官方财报总体覆盖率 {(float(quality_snapshot.get('official_report_coverage_ratio') or 0) * 100):.1f}% ，"
                    f"全局待复核 {int(quality_snapshot.get('pending_review_count') or 0)} 项。"
                    + (
                        f"该企业存在 {len(quality_snapshot.get('company_anomalies', []))} 条异常记录，"
                        f"待跟踪复核 {len(quality_snapshot.get('company_review_queue', []))} 条。"
                        if quality_snapshot.get("company_anomalies") or quality_snapshot.get("company_review_queue")
                        else "该企业当前未命中高优先级质量异常。"
                    )
                ),
            },
        ]
        return sections

    def _render_markdown(self, package: dict) -> str:
        lines = [
            f"# {package['company_name']} 企业运营分析答辩稿骨架",
            "",
            f"- 公司代码：{package['company_code']}",
            f"- 报告年度：{package['report_year']}",
            f"- 生成时间：{package['exported_at']}",
            f"- 问题设定：{package['question']}",
            "",
            "## 执行摘要",
            package["summary"],
            "",
        ]
        for section in package["sections"]:
            lines.extend([f"## {section['title']}", section["content"], ""])
        lines.append("## 证据清单")
        for citation in package["citations"]:
            source = " ".join(part for part in [citation.get("report_date"), citation.get("institution")] if part)
            excerpt = str(citation.get("excerpt") or "").replace("\n", " ").strip()
            lines.append(
                f"- [{citation['citation_id']}] {citation['title']}"
                + (f" | {source}" if source else "")
                + (f" | {citation['source_url']}" if citation.get("source_url") else "")
                + (f" | 摘要：{excerpt}" if excerpt else "")
            )
        lines.append("")
        lines.append("## 导出说明")
        lines.append("本文件可直接作为作品报告、答辩讲稿和后续 DOCX/PPT 自动生成的中间稿。")
        return "\n".join(lines)

    def build_company_competition_package(
        self,
        company_code: str,
        question: str = "结合真实数据生成企业运营分析答辩稿",
        persist: bool = True,
    ) -> dict | None:
        report = self.analytics_service.get_company_report(company_code)
        if report is None:
            return None
        brief = self.decision_service.build_company_decision_brief(company_code, question)
        risk = self.risk_service.build_company_risk_forecast(company_code)
        if brief is None or risk is None:
            return None

        citations = self._build_citations(report, brief)
        quality_snapshot = self._company_quality_snapshot(company_code)
        exported_at = datetime.now().isoformat(timespec="seconds")
        package = {
            "company_code": str(company_code),
            "company_name": report["company_name"],
            "report_year": int(report["report_year"]),
            "question": question,
            "exported_at": exported_at,
            "summary": brief["summary"],
            "sections": self._build_sections(report, brief, risk, quality_snapshot, citations),
            "citations": citations,
            "quality_snapshot": quality_snapshot,
            "report": report,
            "brief": brief,
            "risk": risk,
        }
        markdown_content = self._render_markdown(package)
        package["markdown_content"] = markdown_content
        package["citation_count"] = len(citations)

        export_dir = None
        markdown_path = None
        evidence_path = None
        if persist:
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            export_dir = self.export_root / str(company_code) / stamp
            export_dir.mkdir(parents=True, exist_ok=True)
            markdown_path = export_dir / "competition_report.md"
            evidence_path = export_dir / "evidence_bundle.json"
            markdown_path.write_text(markdown_content, encoding="utf-8")
            evidence_path.write_text(
                json.dumps(
                    {
                        "company_code": package["company_code"],
                        "company_name": package["company_name"],
                        "report_year": package["report_year"],
                        "question": package["question"],
                        "exported_at": package["exported_at"],
                        "quality_snapshot": quality_snapshot,
                        "citations": citations,
                        "report": report,
                        "brief": brief,
                        "risk": risk,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        package["export_dir"] = str(export_dir.resolve()) if export_dir else None
        package["markdown_path"] = str(markdown_path.resolve()) if markdown_path else None
        package["evidence_path"] = str(evidence_path.resolve()) if evidence_path else None
        return package
