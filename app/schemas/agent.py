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


class AgentBoardroomPanelist(BaseModel):
    agent_id: str
    role_label: str
    stance: str
    confidence: float
    evidence_focus: list[str] = Field(default_factory=list)
    challenge: str
    sql_focus: str | None = None


class AgentBoardroomSpeakerNote(BaseModel):
    agent_id: str
    statement: str


class AgentBoardroomDebateRound(BaseModel):
    round: int
    topic: str
    speaker_notes: list[AgentBoardroomSpeakerNote] = Field(default_factory=list)
    consensus_delta: str


class AgentBoardroomSynthesis(BaseModel):
    meeting_mode: str
    primary_call: str
    confidence: float
    consensus_summary: str
    action_board: list[str] = Field(default_factory=list)
    red_lines: list[str] = Field(default_factory=list)


class AgentSQLQuerySpec(BaseModel):
    query_id: str
    title: str
    sql: str
    params: list[str] = Field(default_factory=list)


class AgentSQLMission(BaseModel):
    mission_id: str
    label: str
    goal: str


class AgentSQLPlaybook(BaseModel):
    warehouse_ready: bool = False
    current_engine: str | None = None
    warehouse_db: str | None = None
    company_code: str | None = None
    company_name: str | None = None
    queries: list[AgentSQLQuerySpec] = Field(default_factory=list)
    missions: list[AgentSQLMission] = Field(default_factory=list)
    company_overview_rows: list[dict[str, Any]] = Field(default_factory=list)
    research_heat_rows: list[dict[str, Any]] = Field(default_factory=list)


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
    panelists: list[AgentBoardroomPanelist] = Field(default_factory=list)
    debate_rounds: list[AgentBoardroomDebateRound] = Field(default_factory=list)
    synthesis: AgentBoardroomSynthesis | None = None
    sql_playbook: AgentSQLPlaybook | None = None
    data_authenticity: dict[str, Any] = Field(default_factory=dict)
    thread_messages: list[AgentThreadMessage] = Field(default_factory=list)
