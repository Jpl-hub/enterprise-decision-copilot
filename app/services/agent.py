from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.agents.models import ThreadMessage
from app.agents.workflow import AgentWorkflow


@dataclass(slots=True)
class AgentThread:
    thread_id: str
    title: str
    focus_company_code: str | None = None
    focus_company_name: str | None = None
    messages: list[ThreadMessage] = field(default_factory=list)


class AgentService:
    def __init__(self, workflow: AgentWorkflow) -> None:
        self.workflow = workflow
        self.threads: dict[str, AgentThread] = {}

    def _get_or_create_thread(
        self,
        thread_id: str | None,
        company_code: str | None,
        company_name: str | None,
        question: str,
    ) -> AgentThread:
        if thread_id and thread_id in self.threads:
            thread = self.threads[thread_id]
        else:
            thread = AgentThread(
                thread_id=thread_id or uuid4().hex,
                title=(company_name or question[:18] or "企业分析线程"),
            )
            self.threads[thread.thread_id] = thread
        if company_code:
            thread.focus_company_code = company_code
        if company_name:
            thread.focus_company_name = company_name
            if thread.title == "企业分析线程":
                thread.title = company_name
        return thread

    def _normalize_question(self, question: str, thread: AgentThread) -> str:
        normalized = question.strip()
        focus_name = thread.focus_company_name
        if not focus_name:
            return normalized
        replacements = ("这家公司", "该企业", "它", "这家企业")
        for placeholder in replacements:
            if placeholder in normalized:
                normalized = normalized.replace(placeholder, focus_name)
        return normalized

    def _update_focus(self, thread: AgentThread, payload: dict[str, Any]) -> None:
        matches = payload.get("matched_companies") or []
        if len(matches) == 1:
            match = matches[0]
            thread.focus_company_code = str(match.get("company_code") or thread.focus_company_code or "") or None
            thread.focus_company_name = str(match.get("company_name") or thread.focus_company_name or "") or None
            if thread.focus_company_name:
                thread.title = thread.focus_company_name

    def answer(
        self,
        question: str,
        thread_id: str | None = None,
        company_code: str | None = None,
        company_name: str | None = None,
    ) -> dict:
        thread = self._get_or_create_thread(thread_id, company_code, company_name, question)
        normalized_question = self._normalize_question(question, thread)
        thread.messages.append(ThreadMessage(role="user", content=normalized_question))
        payload = self.workflow.execute(normalized_question)
        self._update_focus(thread, payload)
        assistant_summary = payload.get("summary") or payload.get("title") or "已完成本轮分析。"
        thread.messages.append(ThreadMessage(role="assistant", content=str(assistant_summary)))
        payload.pop("matched_companies", None)
        payload.pop("intent", None)
        payload["thread_id"] = thread.thread_id
        payload["thread_title"] = thread.title
        payload["focus"] = {
            "company_code": thread.focus_company_code,
            "company_name": thread.focus_company_name,
        }
        payload["thread_messages"] = [item.as_dict() for item in thread.messages[-8:]]
        return payload
