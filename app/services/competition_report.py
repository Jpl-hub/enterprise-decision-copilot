from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.analytics import AnalyticsService
from app.services.data_authenticity import DataAuthenticityService
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
        self.data_authenticity_service = DataAuthenticityService()

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
        multimodal = report.get("evidence", {}).get("multimodal_digest", {}) or {}
        if multimodal.get("available"):
            citations.append(
                {
                    "source_type": "multimodal_financial_anchor",
                    "title": f"{report['company_name']} 财报图表锚点",
                    "source_url": multimodal.get("source_url") or financial_url or None,
                    "report_date": multimodal.get("published_at"),
                    "institution": multimodal.get("backend") or "多模态抽取",
                    "excerpt": multimodal.get("summary") or "多模态财报锚点摘要",
                }
            )
        for item in brief.get("evidence", {}).get("semantic_stock_reports", [])[:4]:
            add_item("semantic_stock_evidence", item)
        for item in brief.get("evidence", {}).get("semantic_industry_reports", [])[:4]:
            add_item("semantic_industry_evidence", item)

        for idx, item in enumerate(citations, start=1):
            item["citation_id"] = f"E{idx}"
        return citations

    def _company_quality_snapshot(self, company_code: str) -> dict:
        return self.quality_service.get_company_quality_snapshot(company_code)

    def _build_evidence_digest(self, report: dict, brief: dict, risk: dict, quality_snapshot: dict) -> dict[str, Any]:
        report_evidence = report.get("evidence", {}) or {}
        brief_evidence = brief.get("evidence", {}) or {}
        risk_evidence = risk.get("evidence", {}) or {}
        multimodal = report_evidence.get("multimodal_digest", {}) or {}
        company_anomalies = quality_snapshot.get("company_anomalies", []) or []
        company_review_queue = quality_snapshot.get("company_review_queue", []) or []
        return {
            "multimodal_field_count": int(multimodal.get("filled_field_count") or 0),
            "multimodal_page_count": len(multimodal.get("page_asset_links", []) or []),
            "semantic_stock_count": len(brief_evidence.get("semantic_stock_reports", []) or []),
            "semantic_industry_count": len(brief_evidence.get("semantic_industry_reports", []) or []),
            "official_source_url": report_evidence.get("financial_source_url"),
            "query_terms": list(brief_evidence.get("query_terms", []) or [])[:6],
            "pending_review_count": int(quality_snapshot.get("pending_review_count") or 0),
            "company_anomaly_count": len(company_anomalies),
            "company_review_queue_count": len(company_review_queue),
            "risk_driver_count": len(risk.get("drivers", []) or []),
            "risk_monitor_count": len(risk.get("monitoring_items", []) or []),
            "latest_periodic_label": brief_evidence.get("latest_periodic_label") or risk_evidence.get("latest_periodic_label"),
            "latest_official_disclosure": (
                brief_evidence.get("latest_official_disclosure") or risk_evidence.get("latest_official_disclosure")
            ),
        }

    def _build_data_authenticity(self, report: dict, brief: dict, risk: dict, citations: list[dict]) -> dict[str, Any]:
        evidence_payload = {
            "financial_source_url": report.get("evidence", {}).get("financial_source_url"),
            "research_reports": report.get("evidence", {}).get("research_reports", []),
            "industry_reports": report.get("evidence", {}).get("industry_reports", []),
            "semantic_stock_reports": brief.get("evidence", {}).get("semantic_stock_reports", []),
            "semantic_industry_reports": brief.get("evidence", {}).get("semantic_industry_reports", []),
            "macro_items": report.get("evidence", {}).get("macro_items", []),
            "risk_evidences": risk.get("evidence", {}).get("evidences", []),
            "citations": citations,
        }
        return self.data_authenticity_service.summarize_evidence(
            evidence_payload,
            required_source_types=["financial", "research", "macro"],
            scope_label="企业运营分析材料",
        )

    def _build_publication_gate(self, data_authenticity: dict, quality_snapshot: dict, trust_center: dict) -> dict[str, Any]:
        package_trust_status = str(data_authenticity.get("trust_status") or "limited")
        system_trust_status = str(trust_center.get("trust_status") or "at_risk")
        blocking_reasons: list[str] = []
        warnings: list[str] = []

        if package_trust_status != "trusted":
            blocking_reasons.append(str(data_authenticity.get("statement") or "当前材料真实性校验未达到 trusted。"))
        if system_trust_status != "trusted":
            blocking_reasons.append(
                f"系统数据底座当前信任状态为 {system_trust_status}，不应生成企业级正式对外材料。"
            )
        for item in list(trust_center.get("findings") or []):
            if str(item.get("level") or "").lower() == "critical":
                blocking_reasons.append(str(item.get("detail") or item.get("title") or "存在关键数据治理风险。"))

        company_anomalies = list(quality_snapshot.get("company_anomalies") or [])
        company_review_queue = list(quality_snapshot.get("company_review_queue") or [])
        if company_anomalies:
            warnings.append(f"该企业仍有 {len(company_anomalies)} 条异常记录待复核。")
        if company_review_queue:
            warnings.append(f"该企业仍有 {len(company_review_queue)} 条人工复核任务未关闭。")

        if blocking_reasons:
            gate_status = "blocked"
            statement = "当前材料未通过正式发布门禁，只能继续补数或复核，不能作为企业级正式输出。"
        elif warnings:
            gate_status = "review_required"
            statement = "当前材料已通过真实性门禁，但仍带有质量复核提示，适合内部评审版本。"
        else:
            gate_status = "approved"
            statement = "当前材料已通过真实性与系统信任门禁，可作为企业级正式输出。"

        return {
            "gate_status": gate_status,
            "export_allowed": gate_status != "blocked",
            "enterprise_ready": gate_status == "approved",
            "package_trust_status": package_trust_status,
            "system_trust_status": system_trust_status,
            "system_trust_score": int(trust_center.get("trust_score") or 0),
            "review_required": bool(warnings),
            "blocking_reasons": blocking_reasons,
            "warnings": warnings,
            "statement": statement,
        }

    def _refs(self, citations: list[dict], start: int = 0, limit: int = 2) -> str:
        selected = citations[start : start + limit]
        if not selected:
            return ""
        return " " + "".join(f"[{item['citation_id']}]" for item in selected)

    def _build_sections(self, report: dict, brief: dict, risk: dict, quality_snapshot: dict, citations: list[dict]) -> list[dict]:
        multimodal_extracts = quality_snapshot.get("multimodal_extracts", [])
        multimodal_line = (
            f"多模态抽取已覆盖 {len(multimodal_extracts)} 份企业报告，"
            f"最近一次后端为 {multimodal_extracts[0].get('backend', 'unknown')}，"
            f"识别字段 {int(multimodal_extracts[0].get('filled_field_count') or 0)} 项。"
            if multimodal_extracts
            else "该企业尚未完成多模态财报抽取，已纳入后续治理任务。"
        )
        sections = [
            {
                "title": "项目对象",
                "content": (
                    f"本分析材料围绕 {report['company_name']} 展开，基于 {report['report_year']} 年真实披露财报、"
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
                    + multimodal_line
                ),
            },
        ]
        return sections

    def _render_markdown(self, package: dict) -> str:
        data_authenticity = package.get("data_authenticity", {}) or {}
        publication_gate = package.get("publication_gate", {}) or {}
        lines = [
            f"# {package['company_name']} 企业运营分析材料",
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
        lines.extend(
            [
                "## 真实性声明",
                f"- 材料真实性：{data_authenticity.get('statement') or '暂无'}",
                f"- 系统发布门禁：{publication_gate.get('statement') or '暂无'}",
            ]
        )
        for item in list(publication_gate.get("blocking_reasons") or []):
            lines.append(f"- 阻断原因：{item}")
        for item in list(publication_gate.get("warnings") or []):
            lines.append(f"- 复核提示：{item}")
        lines.append("")
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
        lines.append("本文件可直接作为分析材料、汇报文稿和后续 DOCX/PPT 自动生成的中间稿。")
        return "\n".join(lines)

    def build_company_competition_package(
        self,
        company_code: str,
        question: str = "结合真实数据生成企业运营分析材料",
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
        evidence_digest = self._build_evidence_digest(report, brief, risk, quality_snapshot)
        data_authenticity = self._build_data_authenticity(report, brief, risk, citations)
        trust_center = self.quality_service.get_trust_center_summary()
        publication_gate = self._build_publication_gate(data_authenticity, quality_snapshot, trust_center)
        exported_at = datetime.now().isoformat(timespec="seconds")
        package = {
            "company_code": str(company_code),
            "company_name": report["company_name"],
            "report_year": int(report["report_year"]),
            "question": question,
            "exported_at": exported_at,
            "summary": brief.get("executive_summary") or brief["summary"],
            "brief_verdict": brief.get("verdict"),
            "risk_level": risk.get("risk_level"),
            "sections": self._build_sections(report, brief, risk, quality_snapshot, citations),
            "citations": citations,
            "data_authenticity": data_authenticity,
            "publication_gate": publication_gate,
            "evidence_digest": evidence_digest,
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
            markdown_path = export_dir / "analysis_material.md"
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
                        "brief_verdict": package.get("brief_verdict"),
                        "risk_level": package.get("risk_level"),
                        "data_authenticity": data_authenticity,
                        "publication_gate": publication_gate,
                        "evidence_digest": evidence_digest,
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
