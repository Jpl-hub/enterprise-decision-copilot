from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.db import get_connection, init_db


class AuditService:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path
        init_db(db_path)

    def _now(self) -> str:
        return datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')

    def log_event(
        self,
        event_type: str,
        user_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        detail: dict | None = None,
    ) -> dict:
        payload = {
            'log_id': uuid4().hex,
            'user_id': user_id,
            'event_type': event_type,
            'target_type': target_type,
            'target_id': target_id,
            'detail_json': json.dumps(detail or {}, ensure_ascii=False),
            'created_at': self._now(),
        }
        with get_connection(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO audit_logs (log_id, user_id, event_type, target_type, target_id, detail_json, created_at)
                VALUES (:log_id, :user_id, :event_type, :target_type, :target_id, :detail_json, :created_at)
                ''',
                payload,
            )
            conn.commit()
        return payload

    def list_recent(self, limit: int = 20) -> list[dict]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                '''
                SELECT log_id, user_id, event_type, target_type, target_id, detail_json, created_at
                FROM audit_logs
                ORDER BY created_at DESC
                LIMIT ?
                ''',
                (limit,),
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item['detail'] = json.loads(item.pop('detail_json') or '{}')
            result.append(item)
        return result
