from app.agents.models import AgentIntent, WorkflowContext
from app.agents.tools import AgentSkillSpec, SkillContract
from app.agents.validator import AgentResultValidator
from app.core.container import build_service_container


class DummyTool:
    name = 'dummy_tool'
    label = '测试工具'
    description = '用于测试 skill 合同校验。'
    supported_intents = (AgentIntent.COMPANY_REPORT,)

    def run(self, context: WorkflowContext, analytics_service) -> None:
        raise NotImplementedError


def test_agent_answer_exposes_skill_validation_contract() -> None:
    container = build_service_container()

    payload = container.agent_service.answer('结合行业研报看迈瑞医疗的机会和风险')

    assert payload['validation']['status'] == 'passed'
    assert payload['validation']['contract']['domain'] == 'enterprise_decision'
    assert payload['validation']['contract']['output_kind'] == 'decision_brief'
    assert any(step['step'] == '结果校验' for step in payload['trace'])


def test_result_validator_warns_when_required_evidence_missing() -> None:
    validator = AgentResultValidator()
    skill = AgentSkillSpec(
        skill_id='dummy',
        tool_name='dummy_tool',
        label='测试工具',
        description='用于测试 skill 合同校验。',
        supported_intents=(AgentIntent.COMPANY_REPORT,),
        contract=SkillContract(
            domain='enterprise_analysis',
            output_kind='formal_report',
            required_payload_fields=('title', 'summary', 'highlights', 'evidence'),
            required_evidence_keys=('multimodal_digest', 'evidences'),
            minimum_match_count=1,
        ),
        tool=DummyTool(),
    )
    context = WorkflowContext(
        question='分析迈瑞医疗',
        matches=[{'company_code': '300760', 'company_name': '迈瑞医疗'}],
        intent=AgentIntent.COMPANY_REPORT,
    )

    result = validator.validate(
        skill=skill,
        context=context,
        payload={
            'title': '迈瑞医疗综合报告',
            'summary': '已输出综合分析。',
            'highlights': ['收入稳健', '利润改善'],
            'evidence': {},
        },
    )

    assert result['status'] == 'warning'
    assert result['missing_evidence_keys'] == ['multimodal_digest', 'evidences']


def test_result_validator_fails_when_entity_lock_is_missing() -> None:
    validator = AgentResultValidator()
    skill = AgentSkillSpec(
        skill_id='dummy',
        tool_name='dummy_tool',
        label='测试工具',
        description='用于测试 skill 合同校验。',
        supported_intents=(AgentIntent.COMPANY_COMPARE,),
        contract=SkillContract(
            domain='comparison',
            output_kind='comparison_report',
            required_payload_fields=('title', 'summary', 'highlights'),
            minimum_match_count=2,
        ),
        tool=DummyTool(),
    )
    context = WorkflowContext(
        question='比较两家公司',
        matches=[{'company_code': '300760', 'company_name': '迈瑞医疗'}],
        intent=AgentIntent.COMPANY_COMPARE,
    )

    result = validator.validate(
        skill=skill,
        context=context,
        payload={
            'title': '企业对比分析',
            'summary': '已输出对比判断。',
            'highlights': ['迈瑞医疗当前领先'],
        },
    )

    assert result['status'] == 'failed'
    assert result['failed_count'] >= 1
