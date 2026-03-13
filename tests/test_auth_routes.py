import asyncio
import shutil
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx

from app.config import settings
from app.main import _ensure_runtime_dirs, create_app
from app.services.auth import AuthService


def create_temp_db() -> Path:
    base_dir = Path('data') / 'test_auth_routes' / uuid.uuid4().hex
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / 'app.db'


def test_auth_routes_use_http_only_cookie_session() -> None:
    db_path = create_temp_db()
    app = create_app()

    async def exercise_routes() -> None:
        async with app.router.lifespan_context(app):
            auth_service = AuthService(db_path)
            app.state.container.auth_service = auth_service
            auth_service.register_user('cookie-user', 'password123', 'Cookie 用户')

            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url='http://testserver') as client:
                response = await client.post(
                    '/api/auth/login',
                    json={'username': 'cookie-user', 'password': 'password123'},
                )

                assert response.status_code == 200
                payload = response.json()
                assert 'token' not in payload
                assert payload['user']['username'] == 'cookie-user'
                assert settings.auth_cookie_name in client.cookies

                set_cookie = response.headers.get('set-cookie', '').lower()
                assert f'{settings.auth_cookie_name}=' in set_cookie
                assert 'httponly' in set_cookie

                me = await client.get('/api/auth/me')
                assert me.status_code == 200
                assert me.json()['username'] == 'cookie-user'

                logout = await client.post('/api/auth/logout')
                assert logout.status_code == 200

                me_after_logout = await client.get('/api/auth/me')
                assert me_after_logout.status_code == 401

    try:
        asyncio.run(exercise_routes())
    finally:
        shutil.rmtree(db_path.parent, ignore_errors=True)


def test_runtime_cache_dir_is_created_for_clean_environment() -> None:
    with TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / "cache"

        assert cache_dir.exists() is False

        _ensure_runtime_dirs(cache_dir)

        assert cache_dir.exists() is True
        assert cache_dir.is_dir() is True
