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
        self.company_focus_keywords = ("企业", "公司", "经营", "财务", "盈利", "收入", "现金流", "研发")
        self.top_k = 3

    def _keyword_hits(self, question: str, keywords: tuple[str, ...]) -> list[str]:
        return [keyword for keyword in keywords if keyword and keyword in question]

    def score_intents(self, question: str, matches: list[dict]) -> list[dict]:
        text = question.strip()
        matched_count = len(matches)
        scores: dict[AgentIntent, float] = {intent: 0.0 for intent in AgentIntent}
        reasons: dict[AgentIntent, list[str]] = {intent: [] for intent in AgentIntent}

        compare_hits = self._keyword_hits(text, self.compare_keywords)
        risk_hits = self._keyword_hits(text, self.risk_keywords)
        report_hits = self._keyword_hits(text, self.report_keywords)
        decision_hits = self._keyword_hits(text, self.decision_keywords)
        industry_hits = self._keyword_hits(text, self.industry_keywords)
        quality_hits = self._keyword_hits(text, self.quality_keywords)
        company_hits = self._keyword_hits(text, self.company_focus_keywords)

        if matched_count >= 2:
            scores[AgentIntent.COMPANY_COMPARE] += 8.0
            reasons[AgentIntent.COMPANY_COMPARE].append(f"命中 {matched_count} 家企业")
        elif matched_count == 1:
            for intent in (
                AgentIntent.COMPANY_DIAGNOSIS,
                AgentIntent.COMPANY_REPORT,
                AgentIntent.COMPANY_DECISION_BRIEF,
                AgentIntent.COMPANY_RISK_FORECAST,
            ):
                scores[intent] += 3.0
                reasons[intent].append("命中单一企业对象")

        for intent, hits, weight, label in (
            (AgentIntent.COMPANY_COMPARE, compare_hits, 4.0, "对比词"),
            (AgentIntent.COMPANY_RISK_FORECAST, risk_hits, 3.2, "风险词"),
            (AgentIntent.COMPANY_REPORT, report_hits, 2.8, "报告词"),
            (AgentIntent.COMPANY_DECISION_BRIEF, decision_hits, 2.8, "决策词"),
            (AgentIntent.INDUSTRY_TREND, industry_hits, 3.0, "行业词"),
            (AgentIntent.DATA_QUALITY, quality_hits, 4.0, "质量词"),
        ):
            if hits:
                scores[intent] += weight + min(len(hits) * 0.6, 1.8)
                reasons[intent].append(f"{label}：{'、'.join(hits[:3])}")

        if company_hits and matched_count == 1:
            scores[AgentIntent.COMPANY_DIAGNOSIS] += 2.4
            reasons[AgentIntent.COMPANY_DIAGNOSIS].append(f"经营词：{'、'.join(company_hits[:3])}")

        if matched_count == 1 and decision_hits and risk_hits:
            scores[AgentIntent.COMPANY_DECISION_BRIEF] += 1.6
            reasons[AgentIntent.COMPANY_DECISION_BRIEF].append("同时涉及机会与风险，更适合决策综述")

        if matched_count == 0 and industry_hits:
            scores[AgentIntent.INDUSTRY_TREND] += 2.0
        if matched_count == 0 and risk_hits:
            scores[AgentIntent.OVERVIEW] += 1.5
            reasons[AgentIntent.OVERVIEW].append("未锁定企业，转为全局风险扫描")
        if matched_count == 0 and not any([compare_hits, risk_hits, report_hits, decision_hits, industry_hits, quality_hits]):
            scores[AgentIntent.OVERVIEW] += 2.0
            reasons[AgentIntent.OVERVIEW].append("默认全局扫描入口")
        if matched_count == 1 and not any([report_hits, decision_hits, risk_hits]):
            scores[AgentIntent.COMPANY_DIAGNOSIS] += 1.8
            reasons[AgentIntent.COMPANY_DIAGNOSIS].append("单企业默认进入诊断链")

        if len(text) <= 12 and matched_count == 0:
            scores[AgentIntent.FALLBACK] += 1.4
            reasons[AgentIntent.FALLBACK].append("问题过短，需更多上下文")

        ranked = sorted(
            (
                {
                    "intent": intent,
                    "score": round(score, 2),
                    "reasons": reasons[intent],
                }
                for intent, score in scores.items()
                if score > 0
            ),
            key=lambda item: item["score"],
            reverse=True,
        )
        if not ranked:
            ranked = [
                {
                    "intent": AgentIntent.OVERVIEW,
                    "score": 1.0,
                    "reasons": ["默认全局扫描入口"],
                }
            ]
        return ranked

    def detect_intent(self, question: str, matches: list[dict]) -> AgentIntent:
        ranked = self.score_intents(question, matches)
        return ranked[0]["intent"]
