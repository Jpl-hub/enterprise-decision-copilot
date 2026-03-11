from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DecisionBriefResponse(BaseModel):
    company_code: str
    company_name: str
    question: str
    verdict: str
    summary: str
    key_judgements: list[str] = Field(default_factory=list)
    action_recommendations: list[str] = Field(default_factory=list)
    evidence_highlights: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
