import asyncio

from app.core.container import build_service_container
from app.api.routes.reports import compare_companies
from app.services.analytics import AnalyticsService
from app.api.routes.risk import get_risk_model_summary
from app.services.risk import RiskService
from app.web.dashboard import build_dashboard_context



def test_dashboard_payload_has_targets() -> None:
    service = AnalyticsService()
    payload = service.get_dashboard_payload()
    assert len(payload["targets"]) >= 1



def test_dashboard_context_has_persona_entries() -> None:
    service = AnalyticsService()
    payload = service.get_dashboard_payload()
    context = build_dashboard_context("企航数策 Agent", payload)
    assert len(context["persona_entries"]) == 3



def test_agent_returns_guidance_when_data_not_ready() -> None:
    container = build_service_container()
    result = container.agent_service.answer("分析恒瑞医药")
    assert result["title"] in ["真实数据尚未全部接入", "行业全景分析"] or "企业诊断" in result["title"]



def test_company_report_has_sections() -> None:
    analytics = AnalyticsService()
    report = analytics.get_company_report("300760")
    assert report is not None
    assert report["company_name"]
    assert len(report["sections"]) >= 4
    assert "evidence" in report



def test_company_compare_has_dimensions_and_evidence() -> None:
    analytics = AnalyticsService()
    comparison = analytics.compare_companies(["300760", "688271"])
    assert comparison is not None
    assert comparison["winner_company_name"]
    assert len(comparison["comparison_rows"]) == 2
    assert any(item["dimension"] == "综合表现" for item in comparison["dimensions"])
    assert len(comparison["evidence"]["companies"]) == 2



def test_agent_can_generate_company_report() -> None:
    container = build_service_container()
    result = container.agent_service.answer("生成迈瑞医疗综合报告")
    assert "综合报告" in result["title"]
    assert len(result["trace"]) >= 3



def test_agent_api_returns_execution_trace() -> None:
    container = build_service_container()
    payload = container.agent_service.answer("比较迈瑞医疗和联影医疗")
    assert payload["trace"]
    assert payload["evidence"]["companies"]
    assert any(step["step"] == "tool_execution" for step in payload["trace"])



def test_company_trend_digest_has_multi_year_metrics() -> None:
    analytics = AnalyticsService()
    trend = analytics.get_company_trend_digest("300760")
    assert trend["start_year"] == 2022
    assert trend["end_year"] == 2024
    assert trend["revenue_cagr_pct"] > 0



def test_agent_can_generate_decision_brief() -> None:
    container = build_service_container()
    payload = container.agent_service.answer("结合行业研报看迈瑞医疗的机会和风险")
    assert "决策简报" in payload["title"]
    assert payload["evidence"]["query_terms"]
    assert payload["evidence"]["semantic_stock_reports"]
    assert payload["evidence"]["semantic_industry_reports"]
    assert payload["evidence"]["semantic_stock_reports"][0]["matched_excerpt"]
    assert any("证据：" in item for item in payload["highlights"])



def test_decision_brief_contains_evidence_highlights() -> None:
    container = build_service_container()
    brief = container.decision_service.build_company_decision_brief("300760", "结合海外增长和风险看迈瑞医疗")
    assert brief is not None
    assert brief["evidence"]["query_terms"]
    assert brief["evidence_highlights"]
    assert all("证据：" in item for item in brief["evidence_highlights"])



def test_risk_service_returns_forecast() -> None:
    forecast = RiskService(AnalyticsService()).build_company_risk_forecast("688271")
    assert forecast is not None
    assert forecast["risk_level"] in ["低", "中", "高"]
    assert forecast["monitoring_items"]
    assert forecast["heuristic_score"] >= 0
    assert "heuristic_score" in forecast["evidence"]
    assert "model_prediction" in forecast



def test_risk_model_summary_api_returns_payload() -> None:
    container = build_service_container()
    payload = asyncio.run(get_risk_model_summary(container.risk_model_service))
    assert "model_ready" in payload
    assert "sample_count" in payload


def test_compare_api_returns_structured_payload() -> None:
    payload = asyncio.run(
        compare_companies(
            company_codes=["300760", "688271"],
            analytics_service=AnalyticsService(),
        )
    )
    assert payload["summary"]
    assert payload["comparison_rows"]
    assert any(item["dimension"] == "风险水平" for item in payload["dimensions"])




def test_agent_can_answer_quality_governance_questions() -> None:
    container = build_service_container()
    payload = container.agent_service.answer('系统数据质量覆盖率和复核情况怎么样')
    assert '质量' in payload['title']
    assert payload['evidence']
    assert payload['trace']

