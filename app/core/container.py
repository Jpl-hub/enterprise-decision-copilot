from __future__ import annotations

from dataclasses import dataclass

from app.agents.router import IntentRouter
from app.agents.tools import build_agent_tools
from app.agents.workflow import AgentWorkflow
from app.services.agent import AgentService
from app.services.analytics import AnalyticsService
from app.services.audit import AuditService
from app.services.auth import AuthService
from app.services.competition_report import CompetitionReportService
from app.services.decision import DecisionService
from app.services.quality import DataQualityService
from app.services.retrieval import RetrievalService
from app.services.risk import RiskService
from app.services.risk_model import RiskModelService
from app.services.universe import IndustryUniverseService
from app.services.warehouse import WarehouseService


@dataclass(slots=True)
class ServiceContainer:
    analytics_service: AnalyticsService
    auth_service: AuthService
    audit_service: AuditService
    decision_service: DecisionService
    risk_model_service: RiskModelService
    risk_service: RiskService
    quality_service: DataQualityService
    competition_report_service: CompetitionReportService
    warehouse_service: WarehouseService
    industry_universe_service: IndustryUniverseService
    agent_service: AgentService



def build_service_container() -> ServiceContainer:
    analytics_service = AnalyticsService()
    audit_service = AuditService()
    auth_service = AuthService(audit_service=audit_service)
    retrieval_service = RetrievalService(analytics_service)
    decision_service = DecisionService(analytics_service, retrieval_service)
    risk_model_service = RiskModelService()
    risk_service = RiskService(analytics_service, risk_model_service)
    quality_service = DataQualityService()
    competition_report_service = CompetitionReportService(analytics_service, decision_service, risk_service, quality_service)
    warehouse_service = WarehouseService()
    industry_universe_service = IndustryUniverseService()
    workflow = AgentWorkflow(
        analytics_service=analytics_service,
        intent_router=IntentRouter(),
        tools=build_agent_tools(decision_service, risk_service, quality_service),
    )
    agent_service = AgentService(workflow, audit_service=audit_service)
    return ServiceContainer(
        analytics_service=analytics_service,
        auth_service=auth_service,
        audit_service=audit_service,
        decision_service=decision_service,
        risk_model_service=risk_model_service,
        risk_service=risk_service,
        quality_service=quality_service,
        competition_report_service=competition_report_service,
        warehouse_service=warehouse_service,
        industry_universe_service=industry_universe_service,
        agent_service=agent_service,
    )
