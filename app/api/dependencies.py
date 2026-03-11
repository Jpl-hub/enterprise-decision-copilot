from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.container import ServiceContainer
from app.services.agent import AgentService
from app.services.analytics import AnalyticsService
from app.services.audit import AuditService
from app.services.auth import AuthService
from app.services.competition_report import CompetitionReportService
from app.services.decision import DecisionService
from app.services.quality import DataQualityService
from app.services.risk import RiskService
from app.services.risk_model import RiskModelService
from app.services.universe import IndustryUniverseService
from app.services.warehouse import WarehouseService


security = HTTPBearer(auto_error=False)


def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container



def get_analytics_service(container: ServiceContainer = Depends(get_container)) -> AnalyticsService:
    return container.analytics_service



def get_auth_service(container: ServiceContainer = Depends(get_container)) -> AuthService:
    return container.auth_service



def get_audit_service(container: ServiceContainer = Depends(get_container)) -> AuditService:
    return container.audit_service



def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    if credentials is None or credentials.scheme.lower() != 'bearer':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='请先登录。')
    return auth_service.get_user_by_token(credentials.credentials)



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
