from __future__ import annotations

from app.agents.models import AgentIntent, WorkflowContext
from app.agents.router import IntentRouter
from app.agents.tools import AgentTool
from app.services.analytics import AnalyticsService


class AgentWorkflow:
    def __init__(
        self,
        analytics_service: AnalyticsService,
        intent_router: IntentRouter,
        tools: list[AgentTool],
    ) -> None:
        self.analytics_service = analytics_service
        self.intent_router = intent_router
        self.tools = {tool.name: tool for tool in tools}
        self.intent_to_tool = {
            AgentIntent.FALLBACK: "fallback_tool",
            AgentIntent.OVERVIEW: "industry_overview_tool",
            AgentIntent.DATA_QUALITY: "data_quality_tool",
            AgentIntent.COMPANY_DIAGNOSIS: "company_diagnosis_tool",
            AgentIntent.COMPANY_REPORT: "company_report_tool",
            AgentIntent.COMPANY_DECISION_BRIEF: "company_decision_brief_tool",
            AgentIntent.COMPANY_RISK_FORECAST: "company_risk_forecast_tool",
            AgentIntent.COMPANY_COMPARE: "company_compare_tool",
            AgentIntent.INDUSTRY_TREND: "industry_trend_tool",
        }

    def _select_tool_name(self, intent: AgentIntent) -> str:
        return self.intent_to_tool.get(intent, "fallback_tool")

    def _plan_for_intent(self, context: WorkflowContext) -> None:
        if context.intent == AgentIntent.COMPANY_COMPARE:
            context.add_plan("comparison_scope", "确认参与对比的企业集合，并统一年度口径。")
            context.add_plan("comparison_evidence", "抽取多家企业的财报、研报与风险信号进行横向比对。")
        elif context.intent == AgentIntent.DATA_QUALITY:
            context.add_plan("quality_scope", "检查官方财报覆盖、多模态抽取和异常分布。")
            context.add_plan("review_queue", "汇总自动复核与人工复核队列，识别待处理问题。")
        elif context.intent == AgentIntent.COMPANY_RISK_FORECAST:
            context.add_plan("risk_features", "提取财务、经营和行业风险特征。")
            context.add_plan("risk_scoring", "综合规则引擎与风险模型生成风险判断。")
        elif context.intent in {AgentIntent.COMPANY_DECISION_BRIEF, AgentIntent.COMPANY_REPORT, AgentIntent.COMPANY_DIAGNOSIS}:
            context.add_plan("company_evidence", "汇总企业财报、研报和趋势证据。")
            context.add_plan("decision_synthesis", "形成经营判断、风险机会和建议动作。")
        elif context.intent == AgentIntent.INDUSTRY_TREND:
            context.add_plan("industry_digest", "聚合行业研报与宏观指标，识别景气与主题变化。")
        elif context.intent == AgentIntent.OVERVIEW:
            context.add_plan("overview_digest", "汇总样本企业、研报覆盖和宏观摘要。")
        else:
            context.add_plan("fallback_guidance", "回退到默认引导，帮助用户锁定企业与任务。")

    def execute(self, question: str) -> dict:
        cleaned_question = question.strip()
        matches = self.analytics_service.find_company_matches(cleaned_question) if cleaned_question else []
        context = WorkflowContext(question=cleaned_question, matches=matches)
        context.add_plan("problem_intake", "接收用户问题并准备识别企业对象。")
        if matches:
            matched_names = "、".join(match["company_name"] for match in matches)
            context.add_trace("entity_match", f"已匹配企业：{matched_names}。")
            context.add_plan("entity_resolution", f"已识别分析对象：{matched_names}。")
        else:
            context.add_trace("entity_match", "未匹配到明确企业，将按全局分析链路处理。")
            context.add_plan("entity_resolution", "当前问题未显式命中企业，将走全局分析或回退引导。")

        if not cleaned_question:
            context.intent = AgentIntent.FALLBACK
            context.add_plan("intent_planning", "问题为空，进入默认引导。")
        elif not self.analytics_service.has_ready_data():
            status = self.analytics_service.get_pipeline_status()
            context.add_trace(
                "data_readiness",
                (
                    f"财报={'是' if status.has_financials else '否'}，"
                    f"研报={'是' if status.has_reports else '否'}，"
                    f"宏观={'是' if status.has_macro else '否'}。"
                ),
            )
            context.add_plan("data_readiness", "检查真实数据是否已经完成接入。")
            payload = {
                "title": "真实数据尚未全部接入",
                "summary": "当前系统骨架已完成，但还需要先抓取并整理交易所财报、东方财富研报和国家统计局宏观数据。",
                "highlights": [
                    f"财报数据就绪：{'是' if status.has_financials else '否'}",
                    f"研报数据就绪：{'是' if status.has_reports else '否'}",
                    f"宏观数据就绪：{'是' if status.has_macro else '否'}",
                ],
                "suggested_questions": ["下一步怎么抓取交易所财报？"],
                "matched_companies": matches,
                "intent": AgentIntent.FALLBACK.value,
                "plan": [step.as_dict() for step in context.plan],
            }
            payload["trace"] = [step.as_dict() for step in context.trace]
            return payload
        else:
            context.intent = self.intent_router.detect_intent(cleaned_question, matches)
            context.add_plan("intent_planning", f"识别当前问题属于 {context.intent.value}。")
            self._plan_for_intent(context)

        context.add_trace("intent_router", f"识别意图：{context.intent.value}。")
        context.selected_tool = self._select_tool_name(context.intent)
        context.add_trace("tool_selector", f"已选择工具：{context.selected_tool}。")
        context.add_plan("tool_selection", f"选择执行工具：{context.selected_tool}。")
        tool = self.tools[context.selected_tool]
        result = tool.run(context, self.analytics_service)
        context.add_trace("tool_execution", result.detail)
        context.add_plan("answer_synthesis", "已汇总分析结果、建议动作与证据。")
        payload = dict(result.payload)
        payload["trace"] = [step.as_dict() for step in context.trace]
        payload["plan"] = [step.as_dict() for step in context.plan]
        payload["matched_companies"] = matches
        payload["intent"] = context.intent.value
        return payload
