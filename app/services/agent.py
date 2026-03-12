from __future__ import annotations

import inspect
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from app.agents.models import ThreadMessage
from app.agents.workflow import AgentWorkflow
from app.db import get_connection, init_db
from app.services.audit import AuditService

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, workflow: AgentWorkflow, audit_service: AuditService | None = None, db_path: Path | None = None) -> None:
        self.workflow = workflow
        self.audit_service = audit_service
        self.db_path = db_path
        init_db(db_path)
        self.follow_up_keywords = ('展开', '详细', '具体', '继续', '补充', '细说', '往下', '再说', '怎么看', '怎么做')
        self.supports_routing_question = 'routing_question' in inspect.signature(workflow.execute).parameters

    def _now(self) -> str:
        return datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')

    def _load_thread(self, thread_id: str) -> dict | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                '''
                SELECT thread_id, user_id, title, focus_company_code, focus_company_name, last_task_mode, last_task_label, thread_summary, created_at, updated_at
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
            'last_task_mode': None,
            'last_task_label': None,
            'thread_summary': None,
            'created_at': now,
            'updated_at': now,
        }
        with get_connection(self.db_path) as conn:
            conn.execute(
                '''
                INSERT INTO agent_threads (
                    thread_id,
                    user_id,
                    title,
                    focus_company_code,
                    focus_company_name,
                    last_task_mode,
                    last_task_label,
                    thread_summary,
                    created_at,
                    updated_at
                )
                VALUES (
                    :thread_id,
                    :user_id,
                    :title,
                    :focus_company_code,
                    :focus_company_name,
                    :last_task_mode,
                    :last_task_label,
                    :thread_summary,
                    :created_at,
                    :updated_at
                )
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

    def _is_short_follow_up(self, question: str) -> bool:
        stripped = question.strip()
        if not stripped:
            return False
        return len(stripped) <= 16 or any(keyword in stripped for keyword in self.follow_up_keywords)

    def _normalize_question(self, question: str, thread: dict) -> str:
        normalized = question.strip()
        focus_name = thread.get('focus_company_name')
        if not focus_name:
            return normalized
        replacements = ('这家公司', '该企业', '它', '这家企业')
        for placeholder in replacements:
            if placeholder in normalized:
                normalized = normalized.replace(placeholder, str(focus_name))
        matches = self.workflow.analytics_service.find_company_matches(normalized) if normalized else []
        if not matches and self._is_short_follow_up(normalized):
            normalized = f'{focus_name}{normalized}'
        return normalized

    def _augment_question_with_thread_memory(self, question: str, thread: dict) -> str:
        summary = str(thread.get('thread_summary') or '').strip()
        if not summary or not self._is_short_follow_up(question):
            return question
        focus_name = str(thread.get('focus_company_name') or '').strip()
        last_task_label = str(thread.get('last_task_label') or '').strip()
        context_bits: list[str] = []
        if focus_name and focus_name not in question:
            context_bits.append(f'企业：{focus_name}')
        if last_task_label:
            context_bits.append(f'上一轮任务：{last_task_label}')
        context_bits.append(f'上一轮结论：{summary[:220]}')
        context_bits.append(f'继续问题：{question}')
        return '；'.join(context_bits)

    def _resolve_context_task_mode(self, thread: dict, explicit_task_mode: str | None) -> str | None:
        if explicit_task_mode:
            return explicit_task_mode
        last_task_mode = thread.get('last_task_mode')
        if isinstance(last_task_mode, str) and last_task_mode.strip():
            return last_task_mode.strip()
        return None

    def _build_thread_summary(self, payload: dict[str, Any], thread: dict) -> str | None:
        if payload.get('stage_label') == '需要重试':
            return thread.get('thread_summary')
        task_label = str(payload.get('task_label') or thread.get('last_task_label') or '').strip()
        title = str(payload.get('title') or '').strip()
        summary = str(payload.get('summary') or '').strip()
        highlights = [str(item).strip() for item in list(payload.get('highlights') or [])[:2] if str(item).strip()]
        segments: list[str] = []
        if task_label:
            segments.append(task_label)
        if title:
            segments.append(title)
        if summary:
            segments.append(summary)
        if highlights:
            segments.append('；'.join(highlights))
        compact = re.sub(r'\s+', ' ', '。'.join(segment for segment in segments if segment)).strip('。 ')
        if not compact:
            return thread.get('thread_summary')
        return compact[:260]

    def _update_focus(self, thread: dict, payload: dict[str, Any]) -> dict:
        matches = payload.get('matched_companies') or []
        updated = dict(thread)
        if len(matches) == 1:
            match = matches[0]
            updated['focus_company_code'] = str(match.get('company_code') or updated.get('focus_company_code') or '') or None
            updated['focus_company_name'] = str(match.get('company_name') or updated.get('focus_company_name') or '') or None
            if updated['focus_company_name']:
                updated['title'] = updated['focus_company_name']
        updated['last_task_mode'] = str(payload.get('task_mode') or updated.get('last_task_mode') or '') or None
        updated['last_task_label'] = str(payload.get('task_label') or updated.get('last_task_label') or '') or None
        updated['thread_summary'] = self._build_thread_summary(payload, updated)
        with get_connection(self.db_path) as conn:
            conn.execute(
                '''
                UPDATE agent_threads
                SET title = ?, focus_company_code = ?, focus_company_name = ?, last_task_mode = ?, last_task_label = ?, thread_summary = ?, updated_at = ?
                WHERE thread_id = ?
                ''',
                (
                    updated['title'],
                    updated.get('focus_company_code'),
                    updated.get('focus_company_name'),
                    updated.get('last_task_mode'),
                    updated.get('last_task_label'),
                    updated.get('thread_summary'),
                    self._now(),
                    updated['thread_id'],
                ),
            )
            conn.commit()
        return updated

    def _build_assistant_message(self, payload: dict[str, Any]) -> str:
        lines: list[str] = []
        title = str(payload.get('title') or '').strip()
        summary = str(payload.get('summary') or '').strip()
        if title:
            lines.append(title)
        if summary and summary != title:
            lines.append(summary)
        for item in list(payload.get('highlights') or [])[:3]:
            content = str(item).strip()
            if content:
                lines.append(f'- {content}')
        return '\n'.join(lines) or '已完成本轮分析。'

    def _build_failure_payload(self, thread: dict, question: str, error: Exception) -> dict[str, Any]:
        focus_name = thread.get('focus_company_name') or '这家公司'
        last_task_label = thread.get('last_task_label') or '当前分析'
        return {
            'title': '本轮分析暂时失败',
            'summary': '系统没有完成这轮推理，但上下文已经保留。建议缩小问题范围或换一种问法继续追问。',
            'highlights': [
                '当前线程和上下文已保留，不需要重新开始。',
                f'上一轮任务模式仍保留为：{last_task_label}。',
                f'如需继续，可直接追问：{focus_name}当前最值得关注的经营问题是什么？',
            ],
            'suggested_questions': [
                f'{focus_name}当前最值得关注的经营问题是什么？',
                f'先给我{focus_name}的核心结论，再展开原因。',
                f'把{focus_name}的风险拆成财务、经营、行业三层。',
            ],
            'evidence': {
                'error_type': error.__class__.__name__,
            },
            'trace': [
                {'step': '生成结果', 'status': 'failed', 'detail': '本轮分析过程中发生异常，已返回安全结果。'},
            ],
            'plan': [
                {'step': '保留线程', 'status': 'completed', 'detail': '已保留当前企业、上一轮任务模式与追问上下文。'},
                {'step': '建议重试', 'status': 'completed', 'detail': '建议缩小问题范围后继续追问。'},
            ],
            'task_mode': str(thread.get('last_task_mode') or 'fallback'),
            'task_label': str(thread.get('last_task_label') or '问题引导'),
            'stage_label': '需要重试',
            'deliverables': ['保留上下文', '建议重试'],
            'matched_companies': [],
        }

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
                t.last_task_mode,
                t.last_task_label,
                t.thread_summary,
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
                'thread_summary': row['thread_summary'],
                'last_task_mode': row['last_task_mode'],
                'last_task_label': row['last_task_label'],
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
            'thread_summary': thread.get('thread_summary'),
            'last_task_mode': thread.get('last_task_mode'),
            'last_task_label': thread.get('last_task_label'),
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
        task_mode: str | None = None,
    ) -> dict:
        thread = self._get_or_create_thread(thread_id, user_id, company_code, company_name, question)
        normalized_question = self._normalize_question(question, thread)
        workflow_question = self._augment_question_with_thread_memory(normalized_question, thread)
        user_message = ThreadMessage(role='user', content=normalized_question)
        self._append_message(thread['thread_id'], user_message)

        failed = False
        context_task_mode = self._resolve_context_task_mode(thread, task_mode)
        try:
            execute_kwargs: dict[str, Any] = {
                'preferred_task_mode': task_mode,
                'context_task_mode': context_task_mode,
            }
            if self.supports_routing_question:
                execute_kwargs['routing_question'] = normalized_question
            payload = self.workflow.execute(workflow_question, **execute_kwargs)
            thread = self._update_focus(thread, payload)
        except Exception as error:
            failed = True
            logger.exception('Agent workflow failed for thread %s', thread['thread_id'])
            payload = self._build_failure_payload(thread, normalized_question, error)
            thread = self._update_focus(thread, payload)

        assistant_message = ThreadMessage(role='assistant', content=self._build_assistant_message(payload))
        self._append_message(thread['thread_id'], assistant_message)

        if self.audit_service is not None:
            self.audit_service.log_event(
                event_type='agent.query',
                user_id=user_id,
                target_type='agent_thread',
                target_id=thread['thread_id'],
                detail={
                    'question': normalized_question,
                    'workflow_question': workflow_question,
                    'title': payload.get('title'),
                    'focus_company_code': thread.get('focus_company_code'),
                    'task_mode': payload.get('task_mode'),
                    'context_task_mode': context_task_mode,
                    'thread_summary': thread.get('thread_summary'),
                    'status': 'failed' if failed else 'completed',
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
        payload['thread_summary'] = thread.get('thread_summary')
        payload['thread_messages'] = [item.as_dict() for item in self._list_messages(thread['thread_id'], limit=8)]
        return payload

