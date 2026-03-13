from __future__ import annotations

from pydantic import BaseModel, Field


class AuthUserResponse(BaseModel):
    user_id: str
    username: str
    display_name: str
    role: str
    created_at: str
    last_login_at: str | None = None


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)


class LoginResponse(BaseModel):
    expires_at: str
    user: AuthUserResponse


class RegisterResponse(BaseModel):
    user: AuthUserResponse


class LogoutResponse(BaseModel):
    success: bool = True
