from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status

from app.config import settings
from app.db import get_connection, init_db
from app.services.audit import AuditService


class AuthService:
    def __init__(self, db_path: Path | None = None, audit_service: AuditService | None = None) -> None:
        self.db_path = db_path
        self.audit_service = audit_service
        init_db(db_path)

    def _now(self) -> datetime:
        return datetime.now(UTC)

    def _hash_password(self, password: str, salt: str) -> str:
        digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), 120_000)
        return digest.hex()

    def _serialize_user(self, row) -> dict:
        return {
            'user_id': row['user_id'],
            'username': row['username'],
            'display_name': row['display_name'],
            'role': row['role'],
            'created_at': row['created_at'],
            'last_login_at': row['last_login_at'],
        }

    def register_user(self, username: str, password: str, display_name: str) -> dict:
        normalized_username = username.strip().lower()
        normalized_display_name = display_name.strip() or normalized_username
        if len(normalized_username) < 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='用户名至少 3 位。')
        if len(password) < 8:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='密码至少 8 位。')

        with get_connection(self.db_path) as conn:
            existing = conn.execute('SELECT user_id FROM users WHERE username = ?', (normalized_username,)).fetchone()
            if existing is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='用户名已存在。')
            user_count = conn.execute('SELECT COUNT(*) AS count FROM users').fetchone()['count']
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(password, salt)
            created_at = self._now().isoformat(timespec='seconds').replace('+00:00', 'Z')
            role = 'admin' if user_count == 0 else 'analyst'
            user = {
                'user_id': uuid4().hex,
                'username': normalized_username,
                'display_name': normalized_display_name,
                'password_hash': password_hash,
                'password_salt': salt,
                'role': role,
                'created_at': created_at,
                'last_login_at': None,
            }
            conn.execute(
                '''
                INSERT INTO users (user_id, username, display_name, password_hash, password_salt, role, created_at, last_login_at)
                VALUES (:user_id, :username, :display_name, :password_hash, :password_salt, :role, :created_at, :last_login_at)
                ''',
                user,
            )
            conn.commit()
        response = self._serialize_user(user)
        if self.audit_service is not None:
            self.audit_service.log_event('auth.register', user_id=response['user_id'], target_type='user', target_id=response['user_id'], detail={'username': response['username'], 'role': response['role']})
        return response

    def login(self, username: str, password: str) -> dict:
        normalized_username = username.strip().lower()
        with get_connection(self.db_path) as conn:
            row = conn.execute('SELECT * FROM users WHERE username = ?', (normalized_username,)).fetchone()
            if row is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='用户名或密码错误。')
            expected = self._hash_password(password, row['password_salt'])
            if not hmac.compare_digest(expected, row['password_hash']):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='用户名或密码错误。')
            token = secrets.token_urlsafe(32)
            now = self._now()
            expires_at = now + timedelta(hours=settings.auth_token_ttl_hours)
            now_text = now.isoformat(timespec='seconds').replace('+00:00', 'Z')
            conn.execute(
                'INSERT INTO user_sessions (token, user_id, created_at, expires_at, revoked_at) VALUES (?, ?, ?, ?, NULL)',
                (
                    token,
                    row['user_id'],
                    now_text,
                    expires_at.isoformat(timespec='seconds').replace('+00:00', 'Z'),
                ),
            )
            conn.execute(
                'UPDATE users SET last_login_at = ? WHERE user_id = ?',
                (now_text, row['user_id']),
            )
            conn.commit()
        user = self._serialize_user({**dict(row), 'last_login_at': now_text})
        if self.audit_service is not None:
            self.audit_service.log_event('auth.login', user_id=user['user_id'], target_type='user', target_id=user['user_id'], detail={'username': user['username']})
        return {
            'token': token,
            'expires_at': expires_at.isoformat(timespec='seconds').replace('+00:00', 'Z'),
            'user': user,
        }

    def get_user_by_token(self, token: str) -> dict:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                '''
                SELECT u.* , s.expires_at, s.revoked_at
                FROM user_sessions s
                JOIN users u ON u.user_id = s.user_id
                WHERE s.token = ?
                ''',
                (token,),
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='登录状态无效。')
            if row['revoked_at'] is not None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='登录状态已失效。')
            expires_at = datetime.fromisoformat(str(row['expires_at']).replace('Z', '+00:00'))
            if expires_at <= self._now():
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='登录状态已过期。')
            return self._serialize_user(row)

    def logout(self, token: str) -> None:
        user_id = None
        with get_connection(self.db_path) as conn:
            session = conn.execute('SELECT user_id FROM user_sessions WHERE token = ?', (token,)).fetchone()
            if session is not None:
                user_id = session['user_id']
            conn.execute(
                'UPDATE user_sessions SET revoked_at = ? WHERE token = ? AND revoked_at IS NULL',
                (self._now().isoformat(timespec='seconds').replace('+00:00', 'Z'), token),
            )
            conn.commit()
        if self.audit_service is not None:
            self.audit_service.log_event('auth.logout', user_id=user_id, target_type='session', target_id=token[:12], detail={})
