from __future__ import annotations

from app.services.analytics import AnalyticsService
from app.services.narrative import NarrativeService
from app.services.retrieval import RetrievalService


class DecisionService:
    def __init__(
        self,
        analytics_service: AnalyticsService,
        retrieval_service: RetrievalService,
        narrative_service: NarrativeService | None = None,
    ) -> None:
        self.analytics_service = analytics_service
        self.retrieval_service = retrieval_service
        self.narrative_service = narrative_service

    def _verdict(self, row: dict, trend: dict) -> str:
        score = float(row.get("total_score", 0) or 0)
        risk_level = str(row.get("risk_level") or "中")
        revenue_cagr = float(trend.get("revenue_cagr_pct") or 0)
        profit_cagr = float(trend.get("profit_cagr_pct") or 0)
        if risk_level == "高":
            return "风险观察"
        if score >= 70 and revenue_cagr >= 8 and profit_cagr >= 8:
            return "重点跟踪"
        if score >= 45:
            return "稳健经营"
        return "持续观察"

    def _build_evidence_highlights(self, evidence: dict) -> list[str]:
        highlights: list[str] = []
        for label, rows in (("个股", evidence.get("stock_reports", [])), ("行业", evidence.get("industry_reports", []))):
            for item in rows[:2]:
                source = " ".join(
                    part for part in [
                        str(item.get("report_date") or "").strip(),
                        str(item.get("institution") or item.get("industry_name") or "").strip(),
                    ]
                    if part
                )
                excerpt = str(item.get("matched_excerpt") or item.get("title") or "").replace("；", "，").strip()
                excerpt = excerpt[:56]
                title = str(item.get("title") or "未命名报告").strip()
                prefix = f"{source}《{title}》" if source else f"《{title}》"
                highlights.append(f"{label}证据：{prefix}指出“{excerpt}”。")
        return highlights[:4]

    def build_company_decision_brief(self, company_code: str, question: str) -> dict | None:
        row = self.analytics_service.get_company_record(company_code)
        if row is None:
            return None

        trend = self.analytics_service.get_company_trend_digest(company_code)
        research = self.analytics_service.get_company_research_digest(company_code)
        industry = self.analytics_service.get_company_industry_digest(company_code)
        macro = self.analytics_service.get_macro_digest()
        evidence = self.retrieval_service.retrieve_company_evidence(company_code, question, limit=4)
        evidence_highlights = self._build_evidence_highlights(evidence)
        verdict = self._verdict(row, trend)
        macro_line = "；".join(
            f"{item['indicator_name']}{item['indicator_value']}{item['unit']}"
            for item in macro.get("items", [])[:2]
        ) or "宏观指标待补充。"

        key_judgements = [
            (
                f"经营趋势：{trend['start_year']}-{trend['end_year']} 年营收 CAGR "
                f"{trend['revenue_cagr_pct']:.2f}% ，净利润 CAGR {trend['profit_cagr_pct']:.2f}% 。"
            ),
            (
                f"能力表现：净利率 {float(row['net_margin_pct']):.2f}% ，ROE {float(row['roe_pct']):.2f}% ，"
                f"研发强度 {float(row['rd_ratio_pct']):.2f}% 。"
            ),
            (
                f"外部观点：近两年个股研报 {research['count']} 篇，正向 {research['positive']} 篇，"
                f"负向 {research['negative']} 篇；行业研报匹配 {industry['count']} 篇。"
            ),
            f"外部环境：{macro_line}",
        ]

        action_recommendations = [
            (
                "运营侧："
                + (
                    "保持高研发投入并强化高毛利产品贡献。"
                    if float(row.get("rd_ratio_pct") or 0) >= 10
                    else "继续优化产品结构与研发资源配置。"
                )
            ),
            (
                "策略侧："
                + (
                    "结合语义召回到的研报主题，优先跟踪高景气细分赛道和机构持续看多方向。"
                    if evidence["industry_reports"]
                    else "补充行业景气度跟踪与同业对标。"
                )
            ),
            (
                "风控侧："
                + (
                    "重点关注现金流、负债率和机构谨慎观点带来的经营压力。"
                    if row.get("risk_flags")
                    else "当前风险可控，重点做季度经营偏差监测。"
                )
            ),
        ]

        summary = (
            f"{row['company_name']} 当前经营判断为“{verdict}”。"
            f"综合得分 {float(row['total_score']):.1f}，风险等级 {row['risk_level']}，"
            f"语义召回到个股证据 {len(evidence['stock_reports'])} 条、行业证据 {len(evidence['industry_reports'])} 条。"
        )

        brief = {
            "company_code": str(company_code),
            "company_name": row["company_name"],
            "question": question,
            "verdict": verdict,
            "summary": summary,
            "key_judgements": key_judgements,
            "action_recommendations": action_recommendations,
            "evidence_highlights": evidence_highlights,
            "evidence": {
                "financial_source_url": row.get("source_url"),
                "query_terms": evidence.get("query_terms", []),
                "query_profile": evidence.get("query_profile", {}),
                "semantic_stock_reports": evidence["stock_reports"],
                "semantic_industry_reports": evidence["industry_reports"],
                "macro_items": macro.get("items", []),
                "trend_digest": trend,
            },
        }
        if self.narrative_service is None:
            return brief
        return self.narrative_service.enrich_decision_brief(brief)
