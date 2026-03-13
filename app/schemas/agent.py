from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description='User natural-language question.')
    thread_id: str | None = Field(default=None, description='Existing analysis thread ID.')
    company_code: str | None = Field(default=None, description='Focused company code for the current analysis thread.')
    company_name: str | None = Field(default=None, description='Focused company name for the current analysis thread.')
    task_mode: str | None = Field(default=None, description='Preferred task mode for the current analysis task.')


class AgentTraceStep(BaseModel):
    step: str
    status: str
    detail: str


class AgentPlanStep(BaseModel):
    step: str
    status: str
    detail: str


class AgentThreadMessage(BaseModel):
    role: str
    content: str
    created_at: str


class AgentFocus(BaseModel):
    company_code: str | None = None
    company_name: str | None = None


class AgentThreadMemory(BaseModel):
    task_label: str | None = None
    conclusion: str | None = None
    key_signals: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    evidence_focus: list[str] = Field(default_factory=list)
    execution_digest: 'AgentExecutionDigest | None' = None


class AgentExecutionDigest(BaseModel):
    stage_label: str | None = None
    skill_label: str | None = None
    task_label: str | None = None
    deliverables: list[str] = Field(default_factory=list)
    evidence_count: int = 0
    evidence_types: list[str] = Field(default_factory=list)
    route_label: str | None = None
    route_score: float | None = None
    trace_step_count: int = 0
    plan_step_count: int = 0
    real_data_only: bool = False
    trust_status: str = 'limited'


class AgentThreadSummary(BaseModel):
    thread_id: str
    title: str
    focus: AgentFocus | None = None
    thread_summary: str | None = None
    thread_memory: AgentThreadMemory | None = None
    last_message: str | None = None
    message_count: int
    created_at: str
    updated_at: str


class AgentThreadListResponse(BaseModel):
    total: int
    items: list[AgentThreadSummary] = Field(default_factory=list)


class AgentThreadDetailResponse(BaseModel):
    thread_id: str
    title: str
    focus: AgentFocus | None = None
    thread_summary: str | None = None
    thread_memory: AgentThreadMemory | None = None
    created_at: str
    updated_at: str
    messages: list[AgentThreadMessage] = Field(default_factory=list)


class AgentResponse(BaseModel):
    title: str
    summary: str
    highlights: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] | None = None
    trace: list[AgentTraceStep] = Field(default_factory=list)
    plan: list[AgentPlanStep] = Field(default_factory=list)
    task_mode: str = 'fallback'
    task_label: str = '问题引导'
    skill_id: str | None = None
    skill_label: str | None = None
    stage_label: str = '已完成'
    deliverables: list[str] = Field(default_factory=list)
    thread_id: str
    thread_title: str
    focus: AgentFocus | None = None
    thread_summary: str | None = None
    thread_memory: AgentThreadMemory | None = None
    execution_digest: AgentExecutionDigest | None = None
    data_authenticity: dict[str, Any] = Field(default_factory=dict)
    thread_messages: list[AgentThreadMessage] = Field(default_factory=list)
