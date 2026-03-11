from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User natural-language question.")
    thread_id: str | None = Field(default=None, description="Existing analysis thread ID.")
    company_code: str | None = Field(default=None, description="Focused company code for the current analysis thread.")
    company_name: str | None = Field(default=None, description="Focused company name for the current analysis thread.")


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


class AgentResponse(BaseModel):
    title: str
    summary: str
    highlights: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] | None = None
    trace: list[AgentTraceStep] = Field(default_factory=list)
    plan: list[AgentPlanStep] = Field(default_factory=list)
    thread_id: str
    thread_title: str
    focus: AgentFocus | None = None
    thread_messages: list[AgentThreadMessage] = Field(default_factory=list)
