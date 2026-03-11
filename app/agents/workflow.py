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
