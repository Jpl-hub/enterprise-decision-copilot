from __future__ import annotations

from fastapi import Depends, Request

from app.core.container import ServiceContainer
from app.services.agent import AgentService
from app.services.analytics import AnalyticsService
from app.services.competition_report import CompetitionReportService
from app.services.decision import DecisionService
from app.services.quality import DataQualityService
from app.services.risk import RiskService
from app.services.risk_model import RiskModelService
from app.services.universe import IndustryUniverseService
from app.services.warehouse import WarehouseService



def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container



def get_analytics_service(container: ServiceContainer = Depends(get_container)) -> AnalyticsService:
    return container.analytics_service



def get_agent_service(container: ServiceContainer = Depends(get_container)) -> AgentService:
    return container.agent_service



def get_decision_service(container: ServiceContainer = Depends(get_container)) -> DecisionService:
    return container.decision_service



def get_risk_service(container: ServiceContainer = Depends(get_container)) -> RiskService:
    return container.risk_service



def get_risk_model_service(container: ServiceContainer = Depends(get_container)) -> RiskModelService:
    return container.risk_model_service



def get_industry_universe_service(container: ServiceContainer = Depends(get_container)) -> IndustryUniverseService:
    return container.industry_universe_service



def get_quality_service(container: ServiceContainer = Depends(get_container)) -> DataQualityService:
    return container.quality_service


def get_competition_report_service(container: ServiceContainer = Depends(get_container)) -> CompetitionReportService:
    return container.competition_report_service



def get_warehouse_service(container: ServiceContainer = Depends(get_container)) -> WarehouseService:
    return container.warehouse_service
