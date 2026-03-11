from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from app.agents.models import ThreadMessage
from app.agents.workflow import AgentWorkflow
from app.db import get_connection, init_db
from app.services.audit import AuditService


class AgentService:
    def __init__(self, workflow: AgentWorkflow, audit_service: AuditService | None = None, db_path: Path | None = None) -> None:
        self.workflow = workflow
        self.audit_service = audit_service
        self.db_path = db_path
        init_db(db_path)

    def _now(self) -> str:
        return datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')

    def _load_thread(self, thread_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                '''
                SELECT thread_id, user_id, title, focus_company_code, focus_company_name, created_at, updated_at
                FROM agent_threads
                WHERE thread_id = ?
                ''',
                (thread_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def _create_thread(self, thread_id: str, user_id: str | None, title: str, company_code: str | None, company_name: str | None) -> dict:
        now = self._now()
        payload = {
            'thread_id': thread_id,
            'user_id': user_id,
            'title': title,
            'focus_company_code': company_code,
            'focus_company_name': company_name,
            'created_at': now,
            'updated_at': now,
        }
        with get_connection(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO agent_threads (thread_id, user_id, title, focus_company_code, focus_company_name, created_at, updated_at)
                VALUES (:thread_id, :user_id, :title, :focus_company_code, :focus_company_name, :created_at, :updated_at)
                ''',
                payload,
            )
            conn.commit()
        return payload

    def _get_or_create_thread(
        self,
        thread_id: str | None,
        user_id: str | None,
        company_code: str | None,
        company_name: str | None,
        question: str,
    ) -> dict:
        if thread_id:
            thread = self._load_thread(thread_id)
            if thread is not None:
                return thread
        return self._create_thread(
            thread_id=thread_id or uuid4().hex,
            user_id=user_id,
            title=(company_name or question[:18] or '企业分析线程'),
            company_code=company_code,
            company_name=company_name,
        )

    def _append_message(self, thread_id: str, message: ThreadMessage) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO agent_messages (message_id, thread_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (uuid4().hex, thread_id, message.role, message.content, message.created_at),
            )
            conn.execute(
                'UPDATE agent_threads SET updated_at = ? WHERE thread_id = ?',
                (message.created_at, thread_id),
            )
            conn.commit()

    def _list_messages(self, thread_id: str, limit: int = 8) -> list[ThreadMessage]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                '''
                SELECT role, content, created_at
                FROM agent_messages
                WHERE thread_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                ''',
                (thread_id, limit),
            ).fetchall()
        return [ThreadMessage(role=row['role'], content=row['content'], created_at=row['created_at']) for row in reversed(rows)]

    def _normalize_question(self, question: str, thread: dict) -> str:
        normalized = question.strip()
        focus_name = thread.get('focus_company_name')
        if not focus_name:
            return normalized
        replacements = ('这家公司', '该企业', '它', '这家企业')
        for placeholder in replacements:
            if placeholder in normalized:
                normalized = normalized.replace(placeholder, str(focus_name))
        return normalized

    def _update_focus(self, thread: dict, payload: dict[str, Any]) -> dict:
        matches = payload.get('matched_companies') or []
        updated = dict(thread)
        if len(matches) == 1:
            match = matches[0]
            updated['focus_company_code'] = str(match.get('company_code') or updated.get('focus_company_code') or '') or None
            updated['focus_company_name'] = str(match.get('company_name') or updated.get('focus_company_name') or '') or None
            if updated['focus_company_name']:
                updated['title'] = updated['focus_company_name']
        with get_connection(self.db_path) as conn:
            conn.execute(
                '''
                UPDATE agent_threads
                SET title = ?, focus_company_code = ?, focus_company_name = ?, updated_at = ?
                WHERE thread_id = ?
                ''',
                (
                    updated['title'],
                    updated.get('focus_company_code'),
                    updated.get('focus_company_name'),
                    self._now(),
                    updated['thread_id'],
                ),
            )
            conn.commit()
        return updated

    def _ensure_access(self, thread: dict | None, user_id: str | None, role: str | None) -> dict:
        if thread is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='分析线程不存在。')
        is_admin = str(role or '').lower() == 'admin'
        owner_id = thread.get('user_id')
        if owner_id and owner_id != user_id and not is_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='你不能查看这条分析线程。')
        return thread

    def list_threads(self, user_id: str | None, role: str | None, limit: int = 20) -> dict:
        query = '''
            SELECT
                t.thread_id,
                t.title,
                t.focus_company_code,
                t.focus_company_name,
                t.created_at,
                t.updated_at,
                COUNT(m.message_id) AS message_count,
                (
                    SELECT content
                    FROM agent_messages last_m
                    WHERE last_m.thread_id = t.thread_id
                    ORDER BY created_at DESC
                    LIMIT 1
                ) AS last_message
            FROM agent_threads t
            LEFT JOIN agent_messages m ON m.thread_id = t.thread_id
        '''
        params: tuple[Any, ...]
        if str(role or '').lower() == 'admin':
            query += ' GROUP BY t.thread_id ORDER BY t.updated_at DESC LIMIT ?'
            params = (limit,)
        else:
            query += ' WHERE t.user_id = ? GROUP BY t.thread_id ORDER BY t.updated_at DESC LIMIT ?'
            params = (user_id, limit)
        with get_connection(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
        items = [
            {
                'thread_id': row['thread_id'],
                'title': row['title'],
                'focus': {
                    'company_code': row['focus_company_code'],
                    'company_name': row['focus_company_name'],
                },
                'last_message': row['last_message'],
                'message_count': int(row['message_count'] or 0),
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
            }
            for row in rows
        ]
        return {'total': len(items), 'items': items}

    def get_thread_detail(self, thread_id: str, user_id: str | None, role: str | None) -> dict:
        thread = self._ensure_access(self._load_thread(thread_id), user_id=user_id, role=role)
        messages = [item.as_dict() for item in self._list_messages(thread['thread_id'], limit=100)]
        return {
            'thread_id': thread['thread_id'],
            'title': thread['title'],
            'focus': {
                'company_code': thread.get('focus_company_code'),
                'company_name': thread.get('focus_company_name'),
            },
            'created_at': thread['created_at'],
            'updated_at': thread['updated_at'],
            'messages': messages,
        }

    def answer(
        self,
        question: str,
        thread_id: str | None = None,
        company_code: str | None = None,
        company_name: str | None = None,
        user_id: str | None = None,
    ) -> dict:
        thread = self._get_or_create_thread(thread_id, user_id, company_code, company_name, question)
        normalized_question = self._normalize_question(question, thread)
        user_message = ThreadMessage(role='user', content=normalized_question)
        self._append_message(thread['thread_id'], user_message)
        payload = self.workflow.execute(normalized_question)
        thread = self._update_focus(thread, payload)
        assistant_summary = payload.get('summary') or payload.get('title') or '已完成本轮分析。'
        assistant_message = ThreadMessage(role='assistant', content=str(assistant_summary))
        self._append_message(thread['thread_id'], assistant_message)
        if self.audit_service is not None:
            self.audit_service.log_event(
                event_type='agent.query',
                user_id=user_id,
                target_type='agent_thread',
                target_id=thread['thread_id'],
                detail={
                    'question': normalized_question,
                    'title': payload.get('title'),
                    'focus_company_code': thread.get('focus_company_code'),
                },
            )
        payload.pop('matched_companies', None)
        payload.pop('intent', None)
        payload['thread_id'] = thread['thread_id']
        payload['thread_title'] = thread['title']
        payload['focus'] = {
            'company_code': thread.get('focus_company_code'),
            'company_name': thread.get('focus_company_name'),
        }
        payload['thread_messages'] = [item.as_dict() for item in self._list_messages(thread['thread_id'], limit=8)]
        return payload
