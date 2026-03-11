from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User natural-language question.")


class AgentTraceStep(BaseModel):
    step: str
    status: str
    detail: str


class AgentResponse(BaseModel):
    title: str
    summary: str
    highlights: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] | None = None
    trace: list[AgentTraceStep] = Field(default_factory=list)
