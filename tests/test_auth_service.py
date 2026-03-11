import shutil
import uuid
from pathlib import Path

import pytest

from app.services.auth import AuthService



def create_temp_db() -> Path:
    base_dir = Path('data') / 'test_auth' / uuid.uuid4().hex
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / 'app.db'



def test_auth_service_registers_first_user_as_admin() -> None:
    db_path = create_temp_db()
    try:
        service = AuthService(db_path)
        payload = service.register_user('captain', 'password123', '项目负责人')
    finally:
        shutil.rmtree(db_path.parent, ignore_errors=True)

    assert payload['username'] == 'captain'
    assert payload['role'] == 'admin'



def test_auth_service_login_and_resolve_token() -> None:
    db_path = create_temp_db()
    try:
        service = AuthService(db_path)
        service.register_user('analyst', 'password123', '分析师')
        login = service.login('analyst', 'password123')
        current = service.get_user_by_token(login['token'])
    finally:
        shutil.rmtree(db_path.parent, ignore_errors=True)

    assert login['token']
    assert current['username'] == 'analyst'



def test_auth_service_rejects_duplicate_username() -> None:
    db_path = create_temp_db()
    try:
        service = AuthService(db_path)
        service.register_user('repeat', 'password123', '用户甲')
        with pytest.raises(Exception):
            service.register_user('repeat', 'password123', '用户乙')
    finally:
        shutil.rmtree(db_path.parent, ignore_errors=True)



def test_auth_service_logout_revokes_token() -> None:
    db_path = create_temp_db()
    try:
        service = AuthService(db_path)
        service.register_user('reviewer', 'password123', '复核员')
        login = service.login('reviewer', 'password123')
        service.logout(login['token'])
        with pytest.raises(Exception):
            service.get_user_by_token(login['token'])
    finally:
        shutil.rmtree(db_path.parent, ignore_errors=True)
