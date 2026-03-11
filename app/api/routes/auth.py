from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies import get_auth_service, get_current_user
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse, RegisterRequest, RegisterResponse, AuthUserResponse
from app.services.auth import AuthService


router = APIRouter(prefix='/api/auth', tags=['auth'])
security = HTTPBearer(auto_error=False)


@router.post('/register', response_model=RegisterResponse)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    user = auth_service.register_user(payload.username, payload.password, payload.display_name)
    return {'user': user}


@router.post('/login', response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    return auth_service.login(payload.username, payload.password)


@router.get('/me', response_model=AuthUserResponse)
async def me(current_user: dict = Depends(get_current_user)) -> dict:
    return current_user


@router.post('/logout', response_model=LogoutResponse)
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    if credentials is not None:
        auth_service.logout(credentials.credentials)
    return {'success': True}
