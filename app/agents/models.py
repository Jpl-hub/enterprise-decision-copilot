from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AgentIntent(str, Enum):
    FALLBACK = "fallback"
    OVERVIEW = "overview"
    DATA_QUALITY = "data_quality"
    COMPANY_DIAGNOSIS = "company_diagnosis"
    COMPANY_REPORT = "company_report"
    COMPANY_DECISION_BRIEF = "company_decision_brief"
    COMPANY_RISK_FORECAST = "company_risk_forecast"
    COMPANY_COMPARE = "company_compare"
    INDUSTRY_TREND = "industry_trend"


@dataclass(slots=True)
class TraceStep:
    step: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {
            "step": self.step,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass(slots=True)
class WorkflowContext:
    question: str
    matches: list[dict]
    intent: AgentIntent = AgentIntent.FALLBACK
    selected_tool: str = ""
    trace: list[TraceStep] = field(default_factory=list)

    def add_trace(self, step: str, detail: str, status: str = "completed") -> None:
        self.trace.append(TraceStep(step=step, status=status, detail=detail))


@dataclass(slots=True)
class ToolResult:
    payload: dict
    detail: str
