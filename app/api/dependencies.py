from __future__ import annotations

from collections.abc import Callable

from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.core.container import ServiceContainer
from app.services.agent import AgentService
from app.services.ai_stack import AIStackService
from app.services.analytics import AnalyticsService
from app.services.audit import AuditService
from app.services.auth import AuthService
from app.services.competition_report import CompetitionReportService
from app.services.decision import DecisionService
from app.services.model_registry import ModelRegistryService
from app.services.narrative import NarrativeService
from app.services.quality import DataQualityService
from app.services.retrieval import RetrievalService
from app.services.risk import RiskService
from app.services.risk_model import RiskModelService
from app.services.universe import IndustryUniverseService
from app.services.warehouse import WarehouseService


security = HTTPBearer(auto_error=False)


def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container



def get_analytics_service(container: ServiceContainer = Depends(get_container)) -> AnalyticsService:
    # Analytics payloads are used by live dashboards and should reflect the latest refreshed data files.
    # Instantiate on demand here instead of pinning to the startup snapshot in the service container.
    return AnalyticsService()



def get_auth_service(container: ServiceContainer = Depends(get_container)) -> AuthService:
    return container.auth_service



def get_request_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    cookie_token: str | None = Cookie(default=None, alias=settings.auth_cookie_name),
) -> str | None:
    if credentials is not None and credentials.scheme.lower() == 'bearer':
        return credentials.credentials
    if cookie_token:
        return cookie_token
    return request.cookies.get(settings.auth_cookie_name)



def get_audit_service(container: ServiceContainer = Depends(get_container)) -> AuditService:
    return container.audit_service



def get_ai_stack_service(container: ServiceContainer = Depends(get_container)) -> AIStackService:
    # Stack readiness should reflect the latest artifacts produced by refresh, extraction and training scripts.
    return AIStackService(
        RiskModelService(),
        DataQualityService(),
        agent_skill_count=len(container.agent_service.workflow.skill_registry.skills),
    )


def get_model_registry_service() -> ModelRegistryService:
    return ModelRegistryService()



def get_current_user(
    token: str | None = Depends(get_request_token),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='请先登录。')
    return auth_service.get_user_by_token(token)



def require_roles(*allowed_roles: str) -> Callable[[dict], dict]:
    allowed = {role.strip().lower() for role in allowed_roles if role.strip()}

    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        role = str(current_user.get('role') or '').lower()
        if role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='当前账号没有此操作权限。')
        return current_user

    return dependency



def get_agent_service(container: ServiceContainer = Depends(get_container)) -> AgentService:
    return container.agent_service



def get_decision_service(container: ServiceContainer = Depends(get_container)) -> DecisionService:
    analytics_service = AnalyticsService()
    return DecisionService(
        analytics_service,
        RetrievalService(analytics_service),
        narrative_service=NarrativeService(),
    )



def get_risk_service(container: ServiceContainer = Depends(get_container)) -> RiskService:
    return RiskService(AnalyticsService(), container.risk_model_service)



def get_risk_model_service(container: ServiceContainer = Depends(get_container)) -> RiskModelService:
    return container.risk_model_service



def get_industry_universe_service(container: ServiceContainer = Depends(get_container)) -> IndustryUniverseService:
    return container.industry_universe_service



def get_quality_service(container: ServiceContainer = Depends(get_container)) -> DataQualityService:
    return container.quality_service



def get_competition_report_service(container: ServiceContainer = Depends(get_container)) -> CompetitionReportService:
    analytics_service = AnalyticsService()
    decision_service = DecisionService(
        analytics_service,
        RetrievalService(analytics_service),
        narrative_service=NarrativeService(),
    )
    risk_service = RiskService(analytics_service, container.risk_model_service)
    return CompetitionReportService(
        analytics_service,
        decision_service,
        risk_service,
        container.quality_service,
    )



def get_warehouse_service(container: ServiceContainer = Depends(get_container)) -> WarehouseService:
    return container.warehouse_service
