from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class AgentIntent(str, Enum):
    FALLBACK = "fallback"
    OVERVIEW = "overview"
    DATA_QUALITY = "data_quality"
    COMPANY_DIAGNOSIS = "company_diagnosis"
    COMPANY_REPORT = "company_report"
    COMPANY_DECISION_BRIEF = "company_decision_brief"
    EXECUTIVE_BOARDROOM = "executive_boardroom"
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
class PlanStep:
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
class ThreadMessage:
    role: str
    content: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"))

    def as_dict(self) -> dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class WorkflowContext:
    question: str
    matches: list[dict]
    intent: AgentIntent = AgentIntent.FALLBACK
    selected_tool: str = ""
    trace: list[TraceStep] = field(default_factory=list)
    plan: list[PlanStep] = field(default_factory=list)

    def add_trace(self, step: str, detail: str, status: str = "completed") -> None:
        self.trace.append(TraceStep(step=step, status=status, detail=detail))

    def add_plan(self, step: str, detail: str, status: str = "completed") -> None:
        self.plan.append(PlanStep(step=step, status=status, detail=detail))


@dataclass(slots=True)
class ToolResult:
    payload: dict
    detail: str
