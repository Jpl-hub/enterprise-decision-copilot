from __future__ import annotations

from typing import Any

from app.services.llm import SiliconFlowClient


class NarrativeService:
    def __init__(self, llm_client: SiliconFlowClient | None = None) -> None:
        self.llm_client = llm_client or SiliconFlowClient()

    def is_enabled(self) -> bool:
        return self.llm_client.is_enabled()

    def _merge_evidence(self, evidence: dict[str, Any], mode: str) -> dict[str, Any]:
        merged = dict(evidence)
        merged['narrative_mode'] = mode
        merged['narrative_model'] = getattr(self.llm_client, 'model', None)
        return merged

    def _clean_strings(self, items: Any, limit: int) -> list[str]:
        if not isinstance(items, list):
            return []
        cleaned: list[str] = []
        for item in items:
            text = str(item or '').strip()
            if text:
                cleaned.append(text)
            if len(cleaned) >= limit:
                break
        return cleaned

    def enrich_decision_brief(self, brief: dict[str, Any]) -> dict[str, Any]:
        if not self.is_enabled():
            brief['evidence'] = self._merge_evidence(dict(brief.get('evidence') or {}), 'fallback')
            return brief
        system_prompt = (
            '你是企业运营分析助手。请基于给定结构化证据，用中文输出更自然、更克制的经营判断。'
            '只能使用提供的数据，不要编造事实。返回 JSON，字段包含 summary, key_judgements, action_recommendations。'
        )
        user_prompt = (
            f"公司：{brief.get('company_name')}\n"
            f"问题：{brief.get('question')}\n"
            f"当前摘要：{brief.get('summary')}\n"
            f"关键判断：{brief.get('key_judgements')}\n"
            f"动作建议：{brief.get('action_recommendations')}\n"
            f"证据摘录：{brief.get('evidence_highlights')}\n"
        )
        try:
            payload = self.llm_client.extract_json(system_prompt, user_prompt)
        except Exception:
            brief['evidence'] = self._merge_evidence(dict(brief.get('evidence') or {}), 'fallback')
            return brief

        enriched = dict(brief)
        summary = str(payload.get('summary') or '').strip()
        if summary:
            enriched['summary'] = summary
        key_judgements = self._clean_strings(payload.get('key_judgements'), 4)
        if key_judgements:
            enriched['key_judgements'] = key_judgements
        action_recommendations = self._clean_strings(payload.get('action_recommendations'), 3)
        if action_recommendations:
            enriched['action_recommendations'] = action_recommendations
        enriched['evidence'] = self._merge_evidence(dict(brief.get('evidence') or {}), 'llm')
        return enriched

    def enrich_company_report(self, report: dict[str, Any], question: str | None = None) -> dict[str, Any]:
        if not self.is_enabled():
            report['evidence'] = self._merge_evidence(dict(report.get('evidence') or {}), 'fallback')
            return report
        system_prompt = (
            '你是企业分析报告撰写助手。请基于给定结构化报告内容，将摘要和各章节改写成更自然的中文分析。'
            '不要新增不存在的事实。返回 JSON，字段包含 summary, sections。sections 为数组，每项包含 title, content。'
        )
        user_prompt = (
            f"公司：{report.get('company_name')}\n"
            f"问题：{question or '生成企业综合分析'}\n"
            f"当前摘要：{report.get('summary')}\n"
            f"章节：{report.get('sections')}\n"
            f"优势：{report.get('strengths')}\n"
            f"风险：{report.get('risks')}\n"
        )
        try:
            payload = self.llm_client.extract_json(system_prompt, user_prompt)
        except Exception:
            report['evidence'] = self._merge_evidence(dict(report.get('evidence') or {}), 'fallback')
            return report

        enriched = dict(report)
        summary = str(payload.get('summary') or '').strip()
        if summary:
            enriched['summary'] = summary
        raw_sections = payload.get('sections')
        if isinstance(raw_sections, list):
            sections: list[dict[str, str]] = []
            for item in raw_sections[: len(report.get('sections') or [])]:
                title = str((item or {}).get('title') or '').strip()
                content = str((item or {}).get('content') or '').strip()
                if title and content:
                    sections.append({'title': title, 'content': content})
            if sections:
                enriched['sections'] = sections
        enriched['evidence'] = self._merge_evidence(dict(report.get('evidence') or {}), 'llm')
        return enriched

    def build_industry_narrative(self, payload: dict[str, Any], query: str) -> dict[str, Any]:
        if not self.is_enabled():
            return payload
        system_prompt = (
            '你是医药行业分析助手。请基于行业研报聚合结果和宏观指标，输出克制、结构清晰的行业趋势判断。'
            '不要编造事实。返回 JSON，字段包含 summary, highlights。'
        )
        user_prompt = (
            f"问题：{query}\n"
            f"当前摘要：{payload.get('summary')}\n"
            f"当前要点：{payload.get('highlights')}\n"
        )
        try:
            generated = self.llm_client.extract_json(system_prompt, user_prompt)
        except Exception:
            return payload

        enriched = dict(payload)
        summary = str(generated.get('summary') or '').strip()
        if summary:
            enriched['summary'] = summary
        highlights = self._clean_strings(generated.get('highlights'), 4)
        if highlights:
            enriched['highlights'] = highlights
        return enriched
