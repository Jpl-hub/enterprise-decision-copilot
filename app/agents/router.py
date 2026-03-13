from __future__ import annotations

from dataclasses import dataclass
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from app.agents.models import AgentIntent


@dataclass(frozen=True, slots=True)
class IntentExample:
    intent: AgentIntent
    text: str


class IntentRouter:
    def __init__(self) -> None:
        self.compare_keywords = ("比较", "对比", "PK", "谁更", "横向", "哪家更", "孰优")
        self.risk_keywords = ("风险", "承压", "预警", "预测", "监测", "隐患", "稳健性", "暴露")
        self.report_keywords = ("报告", "摘要", "研究", "诊断书", "生成", "材料", "全景", "梳理")
        self.decision_keywords = ("建议", "决策", "策略", "依据", "原因", "机会", "举措", "打法", "取舍")
        self.industry_keywords = ("行业", "赛道", "趋势", "景气度", "板块", "主题", "风向")
        self.quality_keywords = ("数据质量", "质量", "覆盖率", "复核", "缺失", "治理", "异常字段", "底座", "可信", "可靠")
        self.company_focus_keywords = ("企业", "公司", "经营", "财务", "盈利", "收入", "现金流", "研发", "管理层", "业务")
        self.top_k = 3
        self.intent_examples = self._build_intent_examples()
        self.semantic_vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            min_df=1,
            sublinear_tf=True,
        )
        self.semantic_matrix = self.semantic_vectorizer.fit_transform([item.text for item in self.intent_examples])

    def _build_intent_examples(self) -> list[IntentExample]:
        return [
            IntentExample(AgentIntent.OVERVIEW, "给我看一下当前样本池整体情况"),
            IntentExample(AgentIntent.OVERVIEW, "先做一个全局扫描看看有什么值得关注"),
            IntentExample(AgentIntent.OVERVIEW, "帮我看看整个盘面现在发生了什么"),
            IntentExample(AgentIntent.DATA_QUALITY, "看看当前数据底座靠不靠谱"),
            IntentExample(AgentIntent.DATA_QUALITY, "数据覆盖和可信度现在怎么样"),
            IntentExample(AgentIntent.DATA_QUALITY, "底层数据还有哪些缺口需要补"),
            IntentExample(AgentIntent.COMPANY_DIAGNOSIS, "给迈瑞医疗做一次经营体检"),
            IntentExample(AgentIntent.COMPANY_DIAGNOSIS, "看看这家公司现在的经营状态"),
            IntentExample(AgentIntent.COMPANY_DIAGNOSIS, "帮我拆一下企业目前的核心问题"),
            IntentExample(AgentIntent.COMPANY_REPORT, "帮我整理一份给管理层看的公司材料"),
            IntentExample(AgentIntent.COMPANY_REPORT, "输出企业全景研判材料"),
            IntentExample(AgentIntent.COMPANY_REPORT, "把这家公司梳理成完整分析稿"),
            IntentExample(AgentIntent.COMPANY_DECISION_BRIEF, "结合机会和风险给出动作建议"),
            IntentExample(AgentIntent.COMPANY_DECISION_BRIEF, "给我一个管理层可执行的判断"),
            IntentExample(AgentIntent.COMPANY_DECISION_BRIEF, "应该怎么取舍和推进"),
            IntentExample(AgentIntent.COMPANY_RISK_FORECAST, "判断这家公司未来一段时间会不会出风险"),
            IntentExample(AgentIntent.COMPANY_RISK_FORECAST, "看看潜在隐患和风险暴露"),
            IntentExample(AgentIntent.COMPANY_RISK_FORECAST, "评估企业后续承压情况"),
            IntentExample(AgentIntent.COMPANY_COMPARE, "横向看看两家公司谁更强"),
            IntentExample(AgentIntent.COMPANY_COMPARE, "把两家企业放在一起评一下"),
            IntentExample(AgentIntent.COMPANY_COMPARE, "谁更适合现在重点跟踪"),
            IntentExample(AgentIntent.INDUSTRY_TREND, "看看这个板块最近在往哪走"),
            IntentExample(AgentIntent.INDUSTRY_TREND, "赛道最近发生了什么变化"),
            IntentExample(AgentIntent.INDUSTRY_TREND, "梳理一下行业风向和主题"),
            IntentExample(AgentIntent.FALLBACK, "我还没想好问什么"),
            IntentExample(AgentIntent.FALLBACK, "先告诉我可以怎么提问"),
        ]

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "")).strip()

    def _keyword_hits(self, question: str, keywords: tuple[str, ...]) -> list[str]:
        return [keyword for keyword in keywords if keyword and keyword in question]

    def _semantic_hits(self, question: str) -> dict[AgentIntent, tuple[float, str]]:
        normalized = self._normalize_text(question)
        if not normalized:
            return {}
        query_vector = self.semantic_vectorizer.transform([normalized])
        similarities = linear_kernel(query_vector, self.semantic_matrix)[0]

        best_by_intent: dict[AgentIntent, tuple[float, str]] = {}
        for idx, score in enumerate(similarities):
            if score <= 0:
                continue
            example = self.intent_examples[idx]
            current = best_by_intent.get(example.intent)
            candidate = (float(score), example.text)
            if current is None or candidate[0] > current[0]:
                best_by_intent[example.intent] = candidate
        return best_by_intent

    def score_intents(self, question: str, matches: list[dict]) -> list[dict]:
        text = self._normalize_text(question)
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

        semantic_hits = self._semantic_hits(text)
        for intent, (semantic_score, semantic_example) in semantic_hits.items():
            if semantic_score < 0.14:
                continue
            semantic_weight = round(min(2.6, semantic_score * 4.2), 2)
            scores[intent] += semantic_weight
            reasons[intent].append(f"语义示例：{semantic_example}")

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
            report_semantic = semantic_hits.get(AgentIntent.COMPANY_REPORT, (0.0, ""))[0]
            diagnosis_semantic = semantic_hits.get(AgentIntent.COMPANY_DIAGNOSIS, (0.0, ""))[0]
            if report_semantic >= 0.18 and report_semantic >= diagnosis_semantic:
                scores[AgentIntent.COMPANY_REPORT] += 2.2
                reasons[AgentIntent.COMPANY_REPORT].append("单企业问法更偏向完整材料输出")
            else:
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
