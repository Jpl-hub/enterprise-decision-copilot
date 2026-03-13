from __future__ import annotations

from app.agents.models import AgentIntent, WorkflowContext
from app.agents.router import IntentRouter
from app.agents.tools import AgentSkillRegistry, AgentTool, build_agent_skill_registry
from app.agents.validator import AgentResultValidator
from app.services.analytics import AnalyticsService


class AgentWorkflow:
    def __init__(
        self,
        analytics_service: AnalyticsService,
        intent_router: IntentRouter,
        tools: list[AgentTool],
        result_validator: AgentResultValidator | None = None,
    ) -> None:
        self.analytics_service = analytics_service
        self.intent_router = intent_router
        self.skill_registry: AgentSkillRegistry = build_agent_skill_registry(tools)
        self.result_validator = result_validator or AgentResultValidator()
        self.tools = {skill.tool_name: skill.tool for skill in self.skill_registry.skills}
        self.intent_labels = {
            AgentIntent.FALLBACK: '问题引导',
            AgentIntent.OVERVIEW: '全局概览',
            AgentIntent.DATA_QUALITY: '数据底座',
            AgentIntent.COMPANY_DIAGNOSIS: '企业诊断',
            AgentIntent.COMPANY_REPORT: '综合分析',
            AgentIntent.COMPANY_DECISION_BRIEF: '决策建议',
            AgentIntent.EXECUTIVE_BOARDROOM: '决策会议室',
            AgentIntent.COMPANY_RISK_FORECAST: '风险判断',
            AgentIntent.COMPANY_COMPARE: '企业对比',
            AgentIntent.INDUSTRY_TREND: '行业趋势',
        }
        self.task_mode_aliases = {
            'fallback': AgentIntent.FALLBACK,
            'overview': AgentIntent.OVERVIEW,
            'data_quality': AgentIntent.DATA_QUALITY,
            'company_diagnosis': AgentIntent.COMPANY_DIAGNOSIS,
            'company_report': AgentIntent.COMPANY_REPORT,
            'company_decision_brief': AgentIntent.COMPANY_DECISION_BRIEF,
            'executive_boardroom': AgentIntent.EXECUTIVE_BOARDROOM,
            'company_risk_forecast': AgentIntent.COMPANY_RISK_FORECAST,
            'company_compare': AgentIntent.COMPANY_COMPARE,
            'industry_trend': AgentIntent.INDUSTRY_TREND,
        }
        self.follow_up_keywords = (
            '展开', '详细', '具体', '细说', '继续', '进一步', '再说', '往下', '补充', '拆开', '拆成', '分成', '为什么', '怎么看', '怎么做',
        )

    def _select_tool_name(self, intent: AgentIntent) -> str:
        skill = self.skill_registry.by_intent.get(intent) or self.skill_registry.by_intent.get(AgentIntent.FALLBACK)
        return skill.tool_name if skill is not None else 'fallback_tool'

    def _intent_label(self, intent: AgentIntent) -> str:
        return self.intent_labels.get(intent, '默认分析')

    def _tool_label(self, tool_name: str) -> str:
        skill = self.skill_registry.by_tool_name.get(tool_name)
        return skill.label if skill is not None else '分析工具'

    def _resolve_preferred_task_mode(self, preferred_task_mode: str | None) -> AgentIntent | None:
        if not preferred_task_mode:
            return None
        return self.task_mode_aliases.get(preferred_task_mode.strip().lower())

    def _has_explicit_task_signal(self, question: str, matches: list[dict]) -> bool:
        if len(matches) >= 2:
            return True
        keyword_groups = (
            self.intent_router.compare_keywords,
            self.intent_router.risk_keywords,
            self.intent_router.report_keywords,
            self.intent_router.decision_keywords,
            self.intent_router.boardroom_keywords,
            self.intent_router.industry_keywords,
            self.intent_router.quality_keywords,
        )
        return any(keyword in question for keywords in keyword_groups for keyword in keywords)

    def _looks_like_follow_up(self, question: str) -> bool:
        stripped = question.strip()
        if not stripped:
            return False
        return any(keyword in stripped for keyword in self.follow_up_keywords) or len(stripped) <= 14

    def _resolve_contextual_intent(
        self,
        question: str,
        matches: list[dict],
        detected_intent: AgentIntent,
        context_task_mode: str | None,
    ) -> tuple[AgentIntent, bool]:
        context_intent = self._resolve_preferred_task_mode(context_task_mode)
        if context_intent is None:
            return detected_intent, False
        if self._has_explicit_task_signal(question, matches):
            return detected_intent, False
        if detected_intent in {AgentIntent.OVERVIEW, AgentIntent.COMPANY_DIAGNOSIS} and self._looks_like_follow_up(question):
            return context_intent, context_intent != detected_intent
        return detected_intent, False

    def _task_meta(self, intent: AgentIntent) -> tuple[str, list[str]]:
        mapping = {
            AgentIntent.FALLBACK: ('等待用户锁定任务', ['对象范围', '问题方向']),
            AgentIntent.OVERVIEW: ('已形成全局扫描', ['样本概览', '外部环境', '优先对象']),
            AgentIntent.DATA_QUALITY: ('已形成底座判断', ['覆盖状态', '异常热区', '可信度']),
            AgentIntent.COMPANY_DIAGNOSIS: ('已形成企业诊断', ['经营判断', '风险信号', '建议动作']),
            AgentIntent.COMPANY_REPORT: ('已形成综合报告', ['经营概况', '趋势变化', '证据引用']),
            AgentIntent.COMPANY_DECISION_BRIEF: ('已形成决策建议', ['结论摘要', '行动建议', '证据引用']),
            AgentIntent.EXECUTIVE_BOARDROOM: ('已形成会议共识', ['多角色观点', '会议纪要', 'SQL动作板']),
            AgentIntent.COMPANY_RISK_FORECAST: ('已形成风险判断', ['风险等级', '模型概率', '监测项']),
            AgentIntent.COMPANY_COMPARE: ('已形成对比判断', ['赢家结论', '维度差异', '证据入口']),
            AgentIntent.INDUSTRY_TREND: ('已形成行业扫描', ['景气变化', '主题动向', '宏观摘要']),
        }
        return mapping.get(intent, ('已完成分析', ['分析结论']))

    def _plan_for_intent(self, context: WorkflowContext) -> None:
        if context.intent == AgentIntent.COMPANY_COMPARE:
            context.add_plan('确认对比范围', '确认参与对比的企业集合，并统一年度口径。')
            context.add_plan('抽取横向证据', '抽取多家企业的财报、研报与风险信号进行横向比对。')
            context.add_plan('形成胜负判断', '归并维度差异、风险差距和证据锚点，输出赢家结论。')
        elif context.intent == AgentIntent.DATA_QUALITY:
            context.add_plan('检查数据覆盖', '检查官方财报覆盖、多模态抽取和异常分布。')
            context.add_plan('整理待处理问题', '汇总自动检测出的异常和缺口，识别优先处理的问题。')
        elif context.intent == AgentIntent.COMPANY_RISK_FORECAST:
            context.add_plan('提取风险特征', '提取财务、经营和行业风险特征。')
            context.add_plan('生成风险判断', '综合规则引擎与风险模型生成风险判断。')
        elif context.intent == AgentIntent.EXECUTIVE_BOARDROOM:
            context.add_plan('召集角色代理', '召集财务、市场、风险、治理和SQL角色进入会议。')
            context.add_plan('展开协同会诊', '对经营、机会、风险和数据可信度进行交叉质询。')
            context.add_plan('沉淀会议纪要', '输出共识、分歧、红线和SQL动作板。')
        elif context.intent in {AgentIntent.COMPANY_DECISION_BRIEF, AgentIntent.COMPANY_REPORT, AgentIntent.COMPANY_DIAGNOSIS}:
            context.add_plan('汇总企业证据', '汇总企业财报、研报和趋势证据。')
            context.add_plan('形成经营判断', '形成经营判断、风险机会和建议动作。')
            context.add_plan('绑定证据锚点', '把财报页图、研报摘要与原始链接绑定到结论上。')
        elif context.intent == AgentIntent.INDUSTRY_TREND:
            context.add_plan('整理行业资料', '聚合行业研报与宏观指标，识别景气与主题变化。')
            context.add_plan('输出赛道判断', '抽取行业主题、景气变化和宏观脉冲。')
        elif context.intent == AgentIntent.OVERVIEW:
            context.add_plan('汇总全局信息', '汇总样本企业、研报覆盖和宏观摘要。')
            context.add_plan('识别优先动作', '识别值得深挖的企业对象与后续问题。')
        else:
            context.add_plan('问题引导', '回退到默认引导，帮助用户锁定企业与任务。')

    def _validation_trace_detail(self, validation: dict[str, object]) -> str:
        status = str(validation.get('status') or 'warning')
        check_count = int(validation.get('check_count') or 0)
        warning_count = int(validation.get('warning_count') or 0)
        failed_count = int(validation.get('failed_count') or 0)
        if status == 'passed':
            return f'已完成 {check_count} 项合同校验，当前输出满足 skill 要求。'
        segments = [f'已完成 {check_count} 项合同校验']
        if warning_count:
            segments.append(f'存在 {warning_count} 项提示')
        if failed_count:
            segments.append(f'存在 {failed_count} 项失败')
        return '，'.join(segments) + '。'

    def _finalize_payload(
        self,
        *,
        context: WorkflowContext,
        payload: dict,
        route_candidates: list[dict],
    ) -> dict:
        skill = self.skill_registry.by_intent.get(context.intent)
        validation = self.result_validator.validate(skill=skill, context=context, payload=payload)
        validation_status = str(validation.get('status') or 'warning')
        context.add_plan('校验交付结果', '按领域 skill 合同检查字段完整性、对象锁定和关键证据。')
        context.add_trace(
            '结果校验',
            self._validation_trace_detail(validation),
            status='completed' if validation_status == 'passed' else validation_status,
        )
        payload['trace'] = [step.as_dict() for step in context.trace]
        payload['plan'] = [step.as_dict() for step in context.plan]
        payload['matched_companies'] = context.matches
        payload['intent'] = context.intent.value
        payload['task_mode'] = context.intent.value
        payload['task_label'] = self._intent_label(context.intent)
        payload['skill_id'] = skill.skill_id if skill is not None else None
        payload['skill_label'] = skill.label if skill is not None else None
        payload['validation'] = validation
        payload['route_candidates'] = route_candidates
        return payload

    def execute(
        self,
        question: str,
        preferred_task_mode: str | None = None,
        context_task_mode: str | None = None,
        routing_question: str | None = None,
    ) -> dict:
        cleaned_question = (routing_question or question).strip()
        execution_question = question.strip()
        matches = self.analytics_service.find_company_matches(cleaned_question) if cleaned_question else []
        context = WorkflowContext(question=execution_question, matches=matches)
        preferred_intent = self._resolve_preferred_task_mode(preferred_task_mode)
        route_candidates: list[dict] = []
        context.add_plan('接收问题', '接收用户问题并准备识别企业对象。')
        if matches:
            matched_names = '、'.join(match['company_name'] for match in matches)
            context.add_trace('识别对象', f'已匹配企业：{matched_names}。')
            context.add_plan('锁定对象', f'已识别分析对象：{matched_names}。')
        else:
            context.add_trace('识别对象', '未匹配到明确企业，将按全局分析链路处理。')
            context.add_plan('锁定对象', '当前问题未显式命中企业，将走全局分析或回退引导。')

        if not cleaned_question:
            context.intent = AgentIntent.FALLBACK
            context.add_plan('判断任务类型', '问题为空，进入默认引导。')
            route_candidates = [
                {
                    'intent': AgentIntent.FALLBACK.value,
                    'label': self._intent_label(AgentIntent.FALLBACK),
                    'score': 10.0,
                    'reasons': ['问题为空，进入默认引导'],
                }
            ]
            stage_label, deliverables = self._task_meta(AgentIntent.FALLBACK)
            payload = {
                'title': '问题已接收',
                'summary': '当前未输入具体问题，可以先输入企业名称、股票代码或分析方向。',
                'highlights': ['例如：分析恒瑞医药、比较迈瑞医疗和联影医疗。'],
                'suggested_questions': ['分析恒瑞医药', '比较迈瑞医疗和联影医疗'],
                'stage_label': stage_label,
                'deliverables': deliverables,
            }
            return self._finalize_payload(context=context, payload=payload, route_candidates=route_candidates)
        elif not self.analytics_service.has_ready_data():
            status = self.analytics_service.get_pipeline_status()
            context.add_trace(
                '检查数据状态',
                (
                    f"财报={'是' if status.has_financials else '否'}，"
                    f"研报={'是' if status.has_reports else '否'}，"
                    f"宏观={'是' if status.has_macro else '否'}。"
                ),
            )
            context.add_plan('检查数据状态', '检查真实数据是否已经完成接入。')
            stage_label, deliverables = self._task_meta(AgentIntent.FALLBACK)
            payload = {
                'title': '真实数据尚未全部接入',
                'summary': '当前系统骨架已完成，但还需要先抓取并整理交易所财报、东方财富研报和国家统计局宏观数据。',
                'highlights': [
                    f"财报数据就绪：{'是' if status.has_financials else '否'}",
                    f"研报数据就绪：{'是' if status.has_reports else '否'}",
                    f"宏观数据就绪：{'是' if status.has_macro else '否'}",
                ],
                'suggested_questions': ['下一步怎么抓取交易所财报？'],
                'matched_companies': matches,
                'intent': AgentIntent.FALLBACK.value,
                'task_mode': AgentIntent.FALLBACK.value,
                'task_label': self._intent_label(AgentIntent.FALLBACK),
                'stage_label': stage_label,
                'deliverables': deliverables,
            }
            return self._finalize_payload(context=context, payload=payload, route_candidates=route_candidates)
        else:
            if preferred_intent is not None:
                context.intent = preferred_intent
                context.add_plan('判断任务类型', f"已按任务模式进入：{self._intent_label(context.intent)}。")
                context.add_trace('任务识别', f"当前由任务模式指定为：{self._intent_label(context.intent)}。")
                route_candidates = [
                    {
                        'intent': context.intent.value,
                        'label': self._intent_label(context.intent),
                        'score': 10.0,
                        'reasons': ['由界面任务模式直接指定'],
                    }
                ]
            else:
                scored_candidates = self.intent_router.score_intents(cleaned_question, matches)
                route_candidates = [
                    {
                        'intent': item['intent'].value,
                        'label': self._intent_label(item['intent']),
                        'score': item['score'],
                        'reasons': item['reasons'],
                    }
                    for item in scored_candidates[:3]
                ]
                detected_intent = scored_candidates[0]['intent']
                resolved_intent, adopted_context = self._resolve_contextual_intent(
                    cleaned_question,
                    matches,
                    detected_intent,
                    context_task_mode,
                )
                context.intent = resolved_intent
                if route_candidates:
                    top = route_candidates[0]
                    context.add_trace(
                        '路由依据',
                        f"首选 {top['label']}，评分 {top['score']}，依据：{'；'.join(top['reasons']) or '默认规则'}。",
                    )
                if adopted_context:
                    context.add_plan('承接上下文', f"本轮问题未显式改任务，继续沿用上一轮：{self._intent_label(context.intent)}。")
                    context.add_trace('承接上下文', f"沿用线程上一轮任务模式：{self._intent_label(context.intent)}。")
                context.add_plan('判断任务类型', f"当前问题属于：{self._intent_label(context.intent)}。")
                context.add_trace('任务识别', f"已识别为：{self._intent_label(context.intent)}。")
            self._plan_for_intent(context)

        context.selected_tool = self._select_tool_name(context.intent)
        context.add_trace('选择分析路径', f"将进入：{self._tool_label(context.selected_tool)}。")
        context.add_plan('选择分析路径', f"选择执行路径：{self._tool_label(context.selected_tool)}。")
        tool = self.tools[context.selected_tool]
        result = tool.run(context, self.analytics_service)
        context.add_trace('生成结果', result.detail)
        context.add_plan('输出结果', '已汇总分析结果、建议动作与证据。')
        stage_label, deliverables = self._task_meta(context.intent)
        payload = dict(result.payload)
        payload['stage_label'] = stage_label
        payload['deliverables'] = deliverables
        return self._finalize_payload(context=context, payload=payload, route_candidates=route_candidates)


