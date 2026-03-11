from __future__ import annotations

from app.agents.workflow import AgentWorkflow


class AgentService:
    def __init__(self, workflow: AgentWorkflow) -> None:
        self.workflow = workflow

    def answer(self, question: str) -> dict:
        return self.workflow.execute(question)
