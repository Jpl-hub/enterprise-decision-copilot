from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Response

from app.api.dependencies import get_auth_service, get_current_user, get_request_token
from app.config import settings
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse, RegisterRequest, RegisterResponse, AuthUserResponse
from app.services.auth import AuthService


router = APIRouter(prefix='/api/auth', tags=['auth'])


def _cookie_domain() -> str | None:
    domain = settings.auth_cookie_domain.strip()
    return domain or None


def _set_session_cookie(response: Response, token: str, expires_at: str) -> None:
    expires_at_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        expires=expires_at_dt,
        path='/',
        domain=_cookie_domain(),
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        path='/',
        domain=_cookie_domain(),
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )


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
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    session = auth_service.login(payload.username, payload.password)
    _set_session_cookie(response, session['token'], session['expires_at'])
    return {
        'expires_at': session['expires_at'],
        'user': session['user'],
    }


@router.get('/me', response_model=AuthUserResponse)
async def me(current_user: dict = Depends(get_current_user)) -> dict:
    return current_user


@router.post('/logout', response_model=LogoutResponse)
async def logout(
    response: Response,
    token: str | None = Depends(get_request_token),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    if token:
        auth_service.logout(token)
    _clear_session_cookie(response)
    return {'success': True}
