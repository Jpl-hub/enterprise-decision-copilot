from __future__ import annotations

from app.agents.models import AgentIntent


class IntentRouter:
    def __init__(self) -> None:
        self.compare_keywords = ("比较", "对比", "PK", "谁更")
        self.risk_keywords = ("风险", "承压", "预警", "预测", "监测")
        self.report_keywords = ("报告", "摘要", "研究", "诊断书", "生成")
        self.decision_keywords = ("建议", "决策", "策略", "依据", "原因", "机会", "举措")
        self.industry_keywords = ("行业", "赛道", "趋势", "景气度")
        self.quality_keywords = ("数据质量", "质量", "覆盖率", "复核", "缺失", "治理", "异常字段")

    def detect_intent(self, question: str, matches: list[dict]) -> AgentIntent:
        if len(matches) >= 2 or any(keyword in question for keyword in self.compare_keywords):
            if len(matches) >= 2:
                return AgentIntent.COMPANY_COMPARE
            return AgentIntent.OVERVIEW

        if any(keyword in question for keyword in self.quality_keywords):
            return AgentIntent.DATA_QUALITY

        if len(matches) == 1:
            if any(keyword in question for keyword in self.report_keywords):
                return AgentIntent.COMPANY_REPORT
            if any(keyword in question for keyword in self.decision_keywords):
                return AgentIntent.COMPANY_DECISION_BRIEF
            if any(keyword in question for keyword in self.risk_keywords):
                return AgentIntent.COMPANY_RISK_FORECAST
            return AgentIntent.COMPANY_DIAGNOSIS

        if any(keyword in question for keyword in self.industry_keywords):
            return AgentIntent.INDUSTRY_TREND
        if any(keyword in question for keyword in self.risk_keywords):
            return AgentIntent.OVERVIEW
        return AgentIntent.OVERVIEW
