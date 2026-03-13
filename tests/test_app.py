import pytest
import asyncio
import shutil
import uuid
from pathlib import Path

from app.agents.models import AgentIntent, WorkflowContext
from app.agents.router import IntentRouter
from app.agents.tools import CompanyReportTool, build_agent_tools
from app.agents.workflow import AgentWorkflow
from app.api.routes.ai import get_ai_engine_room, get_ai_model_registry
from app.api.routes.reports import compare_companies
from app.api.routes.risk import get_risk_model_summary
from app.core.container import build_service_container
from app.services.agent import AgentService
from app.services.analytics import AnalyticsService
from app.services.audit import AuditService
from app.services.decision import DecisionService
from app.services.model_registry import ModelRegistryService
from app.services.quality import DataQualityService
from app.services.retrieval import RetrievalService
from app.services.risk import RiskService
from app.services.risk_model import RiskModelService
from app.web.dashboard import build_dashboard_context


def test_dashboard_payload_has_targets() -> None:
    service = AnalyticsService()
    payload = service.get_dashboard_payload()
    assert len(payload["targets"]) >= 1
    assert len(payload["company_pool"]) >= 1
    assert payload["system_status_tagline"]
    assert payload["home_summary"]
    assert payload["company_pool"][0]["tags"]
    assert "freshness" in payload
    assert payload["data_authenticity"]["real_data_only"] is True


def test_dashboard_payload_exposes_freshness_summary() -> None:
    service = AnalyticsService()
    freshness = service.get_data_freshness()

    assert "period_summaries" in freshness
    assert len(freshness["period_summaries"]) == 4
    assert freshness["latest_research_report"]
    assert freshness["latest_industry_report"]
    assert freshness["latest_macro_period"]


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
    assert report["evidence"]["multimodal_digest"]["available"] is True
    assert report["evidence"]["multimodal_digest"]["filled_field_count"] >= 1
    assert report["evidence"]["evidences"]
    assert any(item["evidence_type"] == "image" for item in report["evidence"]["evidences"])
    assert "is_stale_data" in report["evidence"]
    assert "missing_expected_full_year_report" in report["evidence"]
    assert report["data_authenticity"]["real_data_only"] is True
    assert "financial" in report["data_authenticity"]["source_types_present"]


def test_company_compare_has_dimensions_and_evidence() -> None:
    analytics = AnalyticsService()
    comparison = analytics.compare_companies(["300760", "688271"])
    assert comparison is not None
    assert comparison["winner_company_name"]
    assert len(comparison["comparison_rows"]) == 2
    assert len(comparison["scorecards"]) == 2
    assert any(item["dimension"] == "综合表现" for item in comparison["dimensions"])
    assert comparison["battlecards"]
    assert comparison["battlecards"][0]["decisive_metrics"]
    assert len(comparison["evidence"]["companies"]) == 2
    assert comparison["evidence"]["freshness"]["latest_official_disclosure"]
    assert comparison["evidence"]["companies"][0]["freshness_digest"]["annual_report_year"]
    assert comparison["evidence"]["companies"][0]["multimodal_digest"]["filled_field_count"] >= 1
    assert comparison["data_authenticity"]["real_data_only"] is True


def test_agent_can_generate_company_report() -> None:
    container = build_service_container()
    result = container.agent_service.answer("生成迈瑞医疗综合报告")
    assert "综合报告" in result["title"]
    assert len(result["trace"]) >= 3
    assert result["plan"]
    assert result["thread_id"]


def test_agent_api_returns_execution_trace() -> None:
    container = build_service_container()
    payload = container.agent_service.answer("比较迈瑞医疗和联影医疗")
    assert payload["trace"]
    assert payload["evidence"]["companies"]
    assert any(step["step"] == "生成结果" for step in payload["trace"])
    assert any(step["step"] == "选择分析路径" for step in payload["plan"])
    assert payload["route_candidates"]
    assert payload["route_candidates"][0]["intent"] == "company_compare"
    assert payload["data_authenticity"]["real_data_only"] is True
    assert payload["execution_digest"]["trust_status"] == "trusted"


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
    assert payload["evidence"]["query_profile"]["query_variants"]
    assert payload["evidence"]["semantic_stock_reports"]
    assert payload["evidence"]["semantic_industry_reports"]
    assert payload["evidence"]["semantic_stock_reports"][0]["matched_excerpt"]
    assert any("证据：" in item for item in payload["highlights"])


def test_decision_brief_contains_evidence_highlights() -> None:
    container = build_service_container()
    brief = container.decision_service.build_company_decision_brief("300760", "结合海外增长和风险看迈瑞医疗")
    assert brief is not None
    assert brief["executive_summary"]
    assert brief["evidence"]["query_terms"]
    assert brief["evidence"]["query_profile"]["query_variants"]
    assert brief["evidence_highlights"]
    assert all("证据：" in item for item in brief["evidence_highlights"])
    assert brief["evidence"]["multimodal_digest"]["available"] is True
    assert brief["evidence"]["evidences"]
    assert any(item["evidence_type"] == "pdf_anchor" for item in brief["evidence"]["evidences"])


def test_risk_service_returns_forecast() -> None:
    forecast = RiskService(AnalyticsService()).build_company_risk_forecast("688271")
    assert forecast is not None
    assert forecast["risk_level"] in ["低", "中", "高"]
    assert forecast["monitoring_items"]
    assert forecast["heuristic_score"] >= 0
    assert "heuristic_score" in forecast["evidence"]
    assert "model_prediction" in forecast
    assert forecast["evidence"]["evidences"]
    assert any(item["evidence_type"] in {"text", "image"} for item in forecast["evidence"]["evidences"])


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
    assert payload["scorecards"]
    assert payload["battlecards"]
    assert any(item["dimension"] == "风险水平" for item in payload["dimensions"])
    assert payload["evidence"]["freshness"]["latest_stock_report"]


def test_agent_can_answer_quality_governance_questions() -> None:
    container = build_service_container()
    payload = container.agent_service.answer('系统数据质量覆盖率和复核情况怎么样')
    assert '数据' in payload['title']
    assert payload['evidence']
    assert payload['trace']


def test_intent_router_exposes_ranked_candidates() -> None:
    router = IntentRouter()
    ranked = router.score_intents(
        "比较迈瑞医疗和联影医疗的风险与盈利能力",
        [
            {"company_code": "300760", "company_name": "迈瑞医疗"},
            {"company_code": "688271", "company_name": "联影医疗"},
        ],
    )

    assert ranked
    assert ranked[0]["intent"] == AgentIntent.COMPANY_COMPARE
    assert ranked[0]["score"] > 0
    assert ranked[0]["reasons"]


def test_intent_router_uses_semantic_examples_for_quality_questions() -> None:
    router = IntentRouter()
    ranked = router.score_intents("看看当前数据底座靠不靠谱", [])

    assert ranked
    assert ranked[0]["intent"] == AgentIntent.DATA_QUALITY
    assert any("语义示例" in reason for reason in ranked[0]["reasons"])


def test_intent_router_promotes_report_queries_without_explicit_report_keyword() -> None:
    router = IntentRouter()
    ranked = router.score_intents(
        "帮我整理一份迈瑞医疗给管理层看的版本",
        [{"company_code": "300760", "company_name": "迈瑞医疗"}],
    )

    assert ranked
    assert ranked[0]["intent"] == AgentIntent.COMPANY_REPORT


def test_agent_thread_keeps_focus_for_follow_up_questions() -> None:
    container = build_service_container()
    first = container.agent_service.answer('分析迈瑞医疗')
    second = container.agent_service.answer('把这家公司风险拆成三层', thread_id=first['thread_id'])
    assert second['thread_id'] == first['thread_id']
    assert second['focus']['company_name'] == '迈瑞医疗'
    assert len(second['thread_messages']) >= 4


def test_agent_thread_persists_in_database() -> None:
    db_dir = Path('data') / 'test_agent_threads' / uuid.uuid4().hex
    db_path = db_dir / 'app.db'
    db_dir.mkdir(parents=True, exist_ok=True)
    try:
        analytics = AnalyticsService()
        retrieval = RetrievalService(analytics)
        decision = DecisionService(analytics, retrieval)
        risk_model = RiskModelService()
        risk = RiskService(analytics, risk_model)
        workflow = AgentWorkflow(
            analytics_service=analytics,
            intent_router=IntentRouter(),
            tools=build_agent_tools(decision, risk, DataQualityService()),
        )
        audit = AuditService(db_path)
        first_service = AgentService(workflow, audit_service=audit, db_path=db_path)
        first = first_service.answer('分析迈瑞医疗', user_id='tester')
        second_service = AgentService(workflow, audit_service=audit, db_path=db_path)
        second = second_service.answer('把这家公司风险拆成三层', thread_id=first['thread_id'], user_id='tester')
        logs = audit.list_recent(limit=5)
    finally:
        shutil.rmtree(db_dir, ignore_errors=True)

    assert second['thread_id'] == first['thread_id']
    assert second['focus']['company_name'] == '迈瑞医疗'
    assert len(second['thread_messages']) >= 4
    assert any(item['event_type'] == 'agent.query' for item in logs)

def test_agent_thread_history_lists_user_threads() -> None:
    db_dir = Path('data') / 'test_agent_threads' / uuid.uuid4().hex
    db_path = db_dir / 'app.db'
    db_dir.mkdir(parents=True, exist_ok=True)
    try:
        analytics = AnalyticsService()
        retrieval = RetrievalService(analytics)
        decision = DecisionService(analytics, retrieval)
        risk_model = RiskModelService()
        risk = RiskService(analytics, risk_model)
        workflow = AgentWorkflow(
            analytics_service=analytics,
            intent_router=IntentRouter(),
            tools=build_agent_tools(decision, risk, DataQualityService()),
        )
        service = AgentService(workflow, audit_service=AuditService(db_path), db_path=db_path)
        first = service.answer('分析迈瑞医疗', user_id='tester')
        service.answer('看它的行业风险', thread_id=first['thread_id'], user_id='tester')
        history = service.list_threads(user_id='tester', role='analyst')
    finally:
        shutil.rmtree(db_dir, ignore_errors=True)

    assert history['total'] == 1
    assert history['items'][0]['thread_id'] == first['thread_id']
    assert history['items'][0]['message_count'] >= 4


def test_agent_thread_detail_blocks_other_users() -> None:
    db_dir = Path('data') / 'test_agent_threads' / uuid.uuid4().hex
    db_path = db_dir / 'app.db'
    db_dir.mkdir(parents=True, exist_ok=True)
    try:
        analytics = AnalyticsService()
        retrieval = RetrievalService(analytics)
        decision = DecisionService(analytics, retrieval)
        risk_model = RiskModelService()
        risk = RiskService(analytics, risk_model)
        workflow = AgentWorkflow(
            analytics_service=analytics,
            intent_router=IntentRouter(),
            tools=build_agent_tools(decision, risk, DataQualityService()),
        )
        service = AgentService(workflow, audit_service=AuditService(db_path), db_path=db_path)
        first = service.answer('分析迈瑞医疗', user_id='owner')
        with pytest.raises(Exception):
            service.get_thread_detail(first['thread_id'], user_id='other-user', role='viewer')
    finally:
        shutil.rmtree(db_dir, ignore_errors=True)



def test_agent_respects_explicit_task_mode() -> None:
    container = build_service_container()
    payload = container.agent_service.answer('分析迈瑞医疗', task_mode='company_risk_forecast')
    assert payload['task_mode'] == 'company_risk_forecast'
    assert payload['task_label'] == '风险判断'
    assert '风险' in payload['title']

def test_ai_stack_summary_exposes_core_engines() -> None:
    container = build_service_container()
    from app.services.ai_stack import AIStackService

    service = AIStackService(container.risk_model_service, container.quality_service)
    payload = service.get_stack_summary()
    engine_ids = {item['engine_id'] for item in payload['engines']}
    pillar_ids = {item['pillar_id'] for item in payload['pillars']}
    assert 'agent-orchestrator' in engine_ids
    assert 'risk-model' in engine_ids
    assert 'multimodal-extractor' in engine_ids
    assert 'traditional-agent' in pillar_ids
    assert 'deep-learning' in pillar_ids
    assert 'big-data' in pillar_ids


def test_ai_engine_room_route_returns_compute_and_model_registry() -> None:
    container = build_service_container()

    payload = asyncio.run(get_ai_engine_room(container.ai_stack_service))

    assert payload['compute_pipeline']['job_count'] >= 1
    assert payload['compute_pipeline']['spark_ready_job_count'] >= 1
    assert payload['model_registry']
    assert any(item['model_id'] == 'risk-tabular' for item in payload['model_registry'])
    assert payload['recommended_actions']


def test_ai_model_registry_route_returns_registry_summary() -> None:
    payload = asyncio.run(get_ai_model_registry(ModelRegistryService()))

    assert payload['model_count'] == 4
    assert len(payload['items']) == 4
    assert payload['priority_actions']
    assert {item['model_id'] for item in payload['items']} == {
        'risk-tabular',
        'risk-sequence',
        'multimodal-extractor',
        'multimodal-sft',
    }

def test_agent_returns_safe_payload_when_workflow_fails() -> None:
    class BrokenWorkflow:
        def execute(self, question: str, preferred_task_mode: str | None = None) -> dict:
            raise RuntimeError('boom')

    service = AgentService(BrokenWorkflow())
    payload = service.answer('分析迈瑞医疗')

    assert payload['title'] == '本轮分析暂时失败'
    assert payload['stage_label'] == '需要重试'
    assert payload['thread_id']
    assert len(payload['thread_messages']) >= 2

def test_agent_thread_reuses_last_task_mode_for_ambiguous_follow_up() -> None:
    container = build_service_container()
    first = container.agent_service.answer('把迈瑞医疗的风险拆成三层')
    second = container.agent_service.answer('展开讲讲', thread_id=first['thread_id'])

    assert second['thread_id'] == first['thread_id']
    assert second['focus']['company_name'] == '迈瑞医疗'
    assert second['task_mode'] == 'company_risk_forecast'
    assert any(step['step'] == '承接上下文' for step in second['trace'])

def test_agent_response_exposes_skill_metadata() -> None:
    container = build_service_container()
    payload = container.agent_service.answer('分析迈瑞医疗')

    assert payload['skill_id'] == 'company_diagnosis'
    assert payload['skill_label'] == '企业诊断分析'

def test_decision_service_can_use_narrative_service() -> None:
    class StubNarrativeService:
        def enrich_decision_brief(self, brief: dict) -> dict:
            enriched = dict(brief)
            enriched['summary'] = 'LLM增强：' + str(brief['summary'])
            enriched['key_judgements'] = list(brief.get('key_judgements', [])) + ['LLM补充判断']
            enriched['evidence'] = dict(brief.get('evidence') or {})
            enriched['evidence']['narrative_mode'] = 'stub'
            return enriched

    analytics = AnalyticsService()
    retrieval = RetrievalService(analytics)
    service = DecisionService(analytics, retrieval, narrative_service=StubNarrativeService())

    brief = service.build_company_decision_brief('300760', '结合研报看迈瑞医疗的经营动作')

    assert brief is not None
    assert brief['summary'].startswith('LLM增强：')
    assert brief['evidence']['narrative_mode'] == 'stub'
    assert 'LLM补充判断' in brief['key_judgements']


def test_company_report_tool_can_use_narrative_service() -> None:
    class StubNarrativeService:
        def enrich_company_report(self, report: dict, question: str | None = None) -> dict:
            enriched = dict(report)
            enriched['summary'] = f"重写摘要：{question}"
            enriched['sections'] = list(report['sections'])
            enriched['sections'][0] = {
                'title': report['sections'][0]['title'],
                'content': '重写首段：经营概况更适合答辩口径。',
            }
            enriched['evidence'] = dict(report.get('evidence') or {})
            enriched['evidence']['narrative_mode'] = 'stub'
            return enriched

    tool = CompanyReportTool(narrative_service=StubNarrativeService())
    context = WorkflowContext(
        question='生成更正式的企业综合报告',
        matches=[{'company_code': '300760', 'company_name': '迈瑞医疗'}],
        intent=AgentIntent.COMPANY_REPORT,
    )

    result = tool.run(context, AnalyticsService())

    assert result.payload['summary'] == '重写摘要：生成更正式的企业综合报告'
    assert result.payload['highlights'][0] == '重写首段：经营概况更适合答辩口径。'
    assert result.payload['evidence']['narrative_mode'] == 'stub'

def test_agent_response_exposes_thread_summary() -> None:
    container = build_service_container()
    payload = container.agent_service.answer('分析迈瑞医疗')

    assert payload['thread_summary']
    assert payload['thread_memory']
    assert payload['thread_memory']['conclusion']
    assert payload['thread_memory']['execution_digest']
    assert payload['execution_digest']
    assert payload['execution_digest']['deliverables']
    assert '企业诊断' in payload['thread_summary']


def test_agent_thread_history_and_detail_expose_thread_summary() -> None:
    db_dir = Path('data') / 'test_agent_threads' / uuid.uuid4().hex
    db_path = db_dir / 'app.db'
    db_dir.mkdir(parents=True, exist_ok=True)
    try:
        analytics = AnalyticsService()
        retrieval = RetrievalService(analytics)
        decision = DecisionService(analytics, retrieval)
        risk_model = RiskModelService()
        risk = RiskService(analytics, risk_model)
        workflow = AgentWorkflow(
            analytics_service=analytics,
            intent_router=IntentRouter(),
            tools=build_agent_tools(decision, risk, DataQualityService()),
        )
        service = AgentService(workflow, audit_service=AuditService(db_path), db_path=db_path)
        first = service.answer('分析迈瑞医疗', user_id='tester')
        history = service.list_threads(user_id='tester', role='analyst')
        detail = service.get_thread_detail(first['thread_id'], user_id='tester', role='analyst')
    finally:
        shutil.rmtree(db_dir, ignore_errors=True)

    assert history['items'][0]['thread_summary']
    assert history['items'][0]['thread_memory']
    assert history['items'][0]['thread_memory']['execution_digest']
    assert detail['thread_summary']
    assert detail['thread_memory']
    assert detail['thread_memory']['execution_digest']
    assert detail['thread_summary'] == history['items'][0]['thread_summary']


def test_agent_augments_short_follow_up_with_thread_summary() -> None:
    class StubAnalytics:
        def find_company_matches(self, question: str) -> list[dict]:
            if '迈瑞医疗' in question:
                return [{'company_code': '300760', 'company_name': '迈瑞医疗'}]
            return []

    class CapturingWorkflow:
        def __init__(self) -> None:
            self.analytics_service = StubAnalytics()
            self.captured_questions: list[str] = []

        def execute(self, question: str, preferred_task_mode: str | None = None, context_task_mode: str | None = None) -> dict:
            self.captured_questions.append(question)
            return {
                'title': '模拟结果',
                'summary': '已承接上一轮结论。',
                'highlights': ['继续围绕上一轮话题展开。'],
                'suggested_questions': [],
                'evidence': {},
                'trace': [],
                'plan': [],
                'task_mode': context_task_mode or 'company_diagnosis',
                'task_label': '企业诊断',
                'stage_label': '已完成',
                'deliverables': ['结论摘要'],
                'matched_companies': [{'company_code': '300760', 'company_name': '迈瑞医疗'}],
            }

    workflow = CapturingWorkflow()
    service = AgentService(workflow)
    first = service.answer('分析迈瑞医疗')
    second = service.answer('展开讲讲', thread_id=first['thread_id'])

    assert second['thread_summary']
    assert len(workflow.captured_questions) == 2
    assert '上一轮结论：' in workflow.captured_questions[1]
    assert '继续问题：迈瑞医疗展开讲讲' in workflow.captured_questions[1]

