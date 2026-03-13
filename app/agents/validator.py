from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agents.models import WorkflowContext
from app.agents.tools import AgentSkillSpec


@dataclass(frozen=True, slots=True)
class ValidationCheck:
    name: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {
            'name': self.name,
            'status': self.status,
            'detail': self.detail,
        }


class AgentResultValidator:
    def validate(
        self,
        *,
        skill: AgentSkillSpec | None,
        context: WorkflowContext,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if skill is None:
            return {
                'status': 'warning',
                'check_count': 1,
                'warning_count': 1,
                'failed_count': 0,
                'missing_payload_fields': [],
                'missing_evidence_keys': [],
                'checks': [
                    {
                        'name': 'skill_contract',
                        'status': 'warning',
                        'detail': '当前返回结果没有命中明确的 skill 合同，后续应补齐。',
                    }
                ],
                'contract': None,
            }

        checks: list[ValidationCheck] = []
        payload_fields = skill.contract.required_payload_fields
        missing_payload_fields = [
            field_name
            for field_name in payload_fields
            if not self._has_required_field(payload, field_name)
        ]
        if missing_payload_fields:
            checks.append(
                ValidationCheck(
                    name='payload_fields',
                    status='failed',
                    detail=f"缺少关键输出字段：{'、'.join(missing_payload_fields)}。",
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    name='payload_fields',
                    status='passed',
                    detail=f'已满足 {len(payload_fields)} 个关键输出字段要求。',
                )
            )

        matched_count = len(context.matches)
        if matched_count < skill.contract.minimum_match_count:
            checks.append(
                ValidationCheck(
                    name='entity_lock',
                    status='failed',
                    detail=(
                        f'当前 skill 需要至少 {skill.contract.minimum_match_count} 个锁定对象，'
                        f'实际只命中 {matched_count} 个。'
                    ),
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    name='entity_lock',
                    status='passed',
                    detail=(
                        f'对象锁定满足要求，命中 {matched_count} 个，'
                        f'合同要求至少 {skill.contract.minimum_match_count} 个。'
                    ),
                )
            )

        highlights = payload.get('highlights')
        highlight_count = len(highlights) if isinstance(highlights, list) else 0
        if highlight_count < skill.contract.min_highlight_count:
            checks.append(
                ValidationCheck(
                    name='highlights',
                    status='warning',
                    detail=(
                        f'当前只有 {highlight_count} 条高亮，'
                        f'低于合同建议值 {skill.contract.min_highlight_count} 条。'
                    ),
                )
            )
        else:
            checks.append(
                ValidationCheck(
                    name='highlights',
                    status='passed',
                    detail=f'高亮数量满足要求，共 {highlight_count} 条。',
                )
            )

        evidence = payload.get('evidence')
        evidence_payload = evidence if isinstance(evidence, dict) else {}
        missing_evidence_keys = [
            field_name
            for field_name in skill.contract.required_evidence_keys
            if not self._has_value(evidence_payload.get(field_name))
        ]
        if skill.contract.required_evidence_keys:
            if missing_evidence_keys:
                checks.append(
                    ValidationCheck(
                        name='evidence_contract',
                        status='warning',
                        detail=f"证据合同未完全满足，缺少：{'、'.join(missing_evidence_keys)}。",
                    )
                )
            else:
                checks.append(
                    ValidationCheck(
                        name='evidence_contract',
                        status='passed',
                        detail=f'关键证据字段已满足 {len(skill.contract.required_evidence_keys)} 项要求。',
                    )
                )

        failed_count = sum(1 for item in checks if item.status == 'failed')
        warning_count = sum(1 for item in checks if item.status == 'warning')
        status = 'passed'
        if failed_count:
            status = 'failed'
        elif warning_count:
            status = 'warning'

        return {
            'status': status,
            'check_count': len(checks),
            'warning_count': warning_count,
            'failed_count': failed_count,
            'missing_payload_fields': missing_payload_fields,
            'missing_evidence_keys': missing_evidence_keys,
            'checks': [item.as_dict() for item in checks],
            'contract': skill.contract.as_dict(),
        }

    def _has_value(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, tuple, set, dict)):
            return len(value) > 0
        return True

    def _has_required_field(self, payload: dict[str, Any], field_name: str) -> bool:
        if field_name not in payload:
            return False
        value = payload.get(field_name)
        if isinstance(value, str):
            return bool(value.strip())
        return value is not None
