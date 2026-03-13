import shutil
import uuid
from pathlib import Path

from app.api.routes.audit import get_audit_logs
from app.services.audit import AuditService



def create_audit_db() -> Path:
    base_dir = Path('data') / 'test_audit' / uuid.uuid4().hex
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / 'app.db'



def test_audit_service_records_and_lists_events() -> None:
    db_path = create_audit_db()
    try:
        service = AuditService(db_path)
        service.log_event('agent.query', user_id='u1', target_type='thread', target_id='t1', detail={'question': '分析迈瑞医疗'})
        logs = service.list_recent(limit=10)
    finally:
        shutil.rmtree(db_path.parent, ignore_errors=True)

    assert len(logs) == 1
    assert logs[0]['event_type'] == 'agent.query'
    assert logs[0]['detail']['question'] == '分析迈瑞医疗'



def test_audit_route_returns_recent_logs() -> None:
    db_path = create_audit_db()
    try:
        service = AuditService(db_path)
        service.log_event('quality.review.submit', user_id='admin', target_type='manual_review', target_id='300760-2024', detail={'finding_type': '字段异常'})
        payload = get_audit_logs(limit=10, _={'user_id': 'admin', 'role': 'admin'}, audit_service=service)
        if hasattr(payload, '__await__'):
            import asyncio
            payload = asyncio.run(payload)
    finally:
        shutil.rmtree(db_path.parent, ignore_errors=True)
    assert payload['total'] == 1
    assert payload['items'][0]['event_type'] == 'quality.review.submit'
