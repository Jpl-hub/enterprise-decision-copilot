from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.agents.models import AgentIntent, ToolResult, WorkflowContext
from app.services.analytics import AnalyticsService
from app.services.decision import DecisionService
from app.services.quality import DataQualityService
from app.services.risk import RiskService


class AgentTool(Protocol):
    name: str
    label: str
    description: str
    supported_intents: tuple[AgentIntent, ...]

    def run(self, context: WorkflowContext, analytics_service: AnalyticsService) -> ToolResult:
        ...


@dataclass(slots=True)
class AgentSkillSpec:
    skill_id: str
    tool_name: str
    label: str
    description: str
    supported_intents: tuple[AgentIntent, ...]
    tool: AgentTool


@dataclass(slots=True)
class AgentSkillRegistry:
    skills: list[AgentSkillSpec]
    by_intent: dict[AgentIntent, AgentSkillSpec]
    by_tool_name: dict[str, AgentSkillSpec]


class FallbackTool:
    name = 'fallback_tool'
    label = '默认引导'
    description = '负责在未锁定企业或问题意图不清晰时返回默认引导。'
    supported_intents = (AgentIntent.FALLBACK,)

    def run(self, context: WorkflowContext, analytics_service: AnalyticsService) -> ToolResult:
        return ToolResult(
            payload={
                'title': '问题已接收',
                'summary': '当前未命中明确企业对象，你可以直接输入企业简称、全称或股票代码。',
                'highlights': ['例如：分析恒瑞医药、比较迈瑞医疗和联影医疗。'],
                'suggested_questions': ['分析恒瑞医药', '比较迈瑞医疗和联影医疗'],
            },
            detail='未命中具体企业，返回默认引导。',
        )


class OverviewTool:
    name = 'industry_overview_tool'
    label = '全局概览分析'
    description = '负责聚合样本企业、研报覆盖和宏观环境，输出行业级起手判断。'
    supported_intents = (AgentIntent.OVERVIEW,)

    def run(self, context: WorkflowContext, analytics_service: AnalyticsService) -> ToolResult:
        payload = analytics_service.get_dashboard_payload()
        metrics = payload.get('metrics')
        if not metrics:
            return FallbackTool().run(context, analytics_service)
        top_names = '、'.join(item['company_name'] for item in payload['ranking'][:3])
        macro_digest = analytics_service.get_macro_digest()
        macro_line = '宏观环境数据已接入。'
        if macro_digest['items']:
            selected = macro_digest['items'][:2]
            macro_line = '；'.join(
                f"{item['indicator_name']}{item['indicator_value']}{item['unit']}" for item in selected
            )
        return ToolResult(
            payload={
                'title': '行业全景分析',
                'summary': (
                    f"当前样本共 {metrics['sample_count']} 家企业，"
                    f"{metrics['latest_year']} 年平均综合得分 {metrics['avg_score']}，"
                    f"领先企业为 {metrics['leader_name']}。"
                ),
                'highlights': [
                    f'Top3 企业：{top_names}。',
                    (
                        f"公开个股研报 {metrics.get('research_report_count', 0)} 篇，"
                        f"行业研报 {metrics.get('industry_report_count', 0)} 篇。"
                    ),
                    '当前风险显著企业主要体现在经营现金流和评级偏谨慎。',
                    macro_line,
                ],
                'suggested_questions': [
                    '分析恒瑞医药',
                    '比较迈瑞医疗和联影医疗',
                    '结合行业研报分析医药赛道趋势',
                    '谁的风险最高',
                ],
            },
            detail='已聚合企业排名、风险清单、研报覆盖与宏观摘要。',
        )


class DataQualityTool:
    name = 'data_quality_tool'
    label = '数据质量分析'
    description = '负责输出财报覆盖、异常分布与人工复核队列。'
    supported_intents = (AgentIntent.DATA_QUALITY,)

    def __init__(self, quality_service: DataQualityService) -> None:
        self.quality_service = quality_service

    def run(self, context: WorkflowContext, analytics_service: AnalyticsService) -> ToolResult:
        summary = self.quality_service.get_quality_summary()
        if context.matches:
            company_code = str(context.matches[0]['company_code'])
            company_name = str(context.matches[0]['company_name'])
            snapshot = self.quality_service.get_company_quality_snapshot(company_code)
            anomalies = snapshot.get('company_anomalies', [])
            queue = snapshot.get('company_review_queue', [])
            highlights = [
                f'该企业命中异常 {len(anomalies)} 条，待处理问题 {len(queue)} 条。',
                f"全局官方财报覆盖率 {float(snapshot.get('official_report_coverage_ratio') or 0) * 100:.1f}% ，待处理问题 {int(snapshot.get('pending_review_count') or 0)} 项。",
            ]
            if anomalies:
                first = anomalies[0]
                highlights.append(
                    f"最高优先异常：{first['report_year']} 年影响程度 {first['anomaly_score']}，"
                    f"缺失字段 {len(first.get('critical_fields_missing', []))} 项。"
                )
            if queue:
                highlights.append(f"最近待处理问题：{queue[0]['finding_type']}。")
            return ToolResult(
                payload={
                    'title': f'{company_name} 数据底座状态',
                    'summary': f'已完成 {company_name} 财报字段质量扫描，并整理出当前待处理异常。',
                    'highlights': highlights,
                    'suggested_questions': [
                        f'继续分析{company_name}的经营风险',
                        '查看最新异常处理建议',
                        '查看全局数据覆盖和缺口分布',
                    ],
                    'evidence': {
                        'company_snapshot': snapshot,
                        'top_anomalies': anomalies,
                        'recent_reviews': queue,
                    },
                },
                detail=f'已输出 {company_name} 企业级数据状态摘要。',
            )

        highlights = [
            f"官方财报覆盖率 {float(summary.get('official_report_coverage_ratio') or 0) * 100:.1f}% ，"
            f"已下载 {summary.get('official_report_downloaded_slots', 0)} / {summary.get('official_report_expected_slots', 0)} 槽位。",
            f"待处理问题 {summary.get('pending_review_count', 0)} 项，异常企业 {summary.get('anomaly_company_count', 0)} 家。",
        ]
        top_anomalies = summary.get('top_anomalies', [])
        if top_anomalies:
            first = top_anomalies[0]
            highlights.append(
                f"当前最高风险异常：{first['company_name']} {first['report_year']} 年，影响程度 {first['anomaly_score']}。"
            )
        return ToolResult(
            payload={
                'title': '数据底座状态看板',
                'summary': '已聚合财报覆盖、字段异常和待处理问题，可直接判断当前数据底座是否稳定。',
                'highlights': highlights,
                'suggested_questions': [
                    '查看待处理异常',
                    '分析迈瑞医疗数据质量',
                    '结合数据质量解释风险结论',
                ],
                'evidence': {
                    'summary': summary,
                    'top_anomalies': top_anomalies,
                    'exchange_status': summary.get('exchange_status', []),
                },
            },
            detail='已输出全局数据底座摘要。',
        )


class CompanyDiagnosisTool:
    name = 'company_diagnosis_tool'
    label = '企业诊断分析'
    description = '负责单企业经营诊断、财务表现和行业证据汇总。'
    supported_intents = (AgentIntent.COMPANY_DIAGNOSIS,)

    def run(self, context: WorkflowContext, analytics_service: AnalyticsService) -> ToolResult:
        company_code = str(context.matches[0]['company_code'])
        row = analytics_service.get_company_record(company_code)
        if row is None:
            return FallbackTool().run(context, analytics_service)
        research = analytics_service.get_company_research_digest(company_code)
        industry = analytics_service.get_company_industry_digest(company_code)
        return ToolResult(
            payload={
                'title': f"{row['company_name']} 企业诊断",
                'summary': (
                    f"基于 {int(row['report_year'])} 年真实披露数据，"
                    f"{row['company_name']} 当前综合得分 {row['total_score']:.1f}，风险等级 {row['risk_level']}。"
                ),
                'highlights': [
                    f"营收 {row['revenue_million']:.2f} 百万元，净利润 {row['net_profit_million']:.2f} 百万元。",
                    (
                        f"净利率 {row['net_margin_pct'] if row['net_margin_pct'] == row['net_margin_pct'] else '暂无'}，"
                        f"ROE {row['roe_pct'] if row['roe_pct'] == row['roe_pct'] else '暂无'}。"
                    ),
                    (
                        f"研发强度 {row['rd_ratio_pct'] if row['rd_ratio_pct'] == row['rd_ratio_pct'] else '暂无'}，"
                        f"经营现金流 {row['operating_cashflow_million'] if row['operating_cashflow_million'] == row['operating_cashflow_million'] else '暂无'} 百万元。"
                    ),
                    (
                        f"近两年公开个股研报 {research['count']} 篇，"
                        f"正向观点 {research['positive']} 篇，负向观点 {research['negative']} 篇。"
                    ),
                    (
                        f"相关行业研报覆盖 {industry['count']} 篇，重点行业包括："
                        f"{'、'.join(industry['industries']) if industry['industries'] else '暂无匹配'}。"
                    ),
                    f"主要风险提示：{'；'.join(row['risk_flags']) if row['risk_flags'] else '当前未触发明显风险项'}。",
                ],
                'suggested_questions': [
                    '把它和药明康德对比一下',
                    '结合行业研报看它的机会和风险',
                    '它的增长和盈利谁更强',
                    '基于当前数据生成一段投资研究摘要',
                ],
            },
            detail=(
                f"已完成 {row['company_name']} 单企业诊断，使用 1 份年度快照、"
                f"{research['count']} 篇个股研报与 {industry['count']} 篇行业研报。"
            ),
        )


class CompanyReportTool:
    name = 'company_report_tool'
    label = '企业综合分析'
    description = '负责生成偏正式的企业综合报告与结构化段落。'
    supported_intents = (AgentIntent.COMPANY_REPORT,)

    def run(self, context: WorkflowContext, analytics_service: AnalyticsService) -> ToolResult:
        company_code = str(context.matches[0]['company_code'])
        report = analytics_service.get_company_report(company_code)
        if report is None:
            return FallbackTool().run(context, analytics_service)
        return ToolResult(
            payload={
                'title': f"{report['company_name']} 综合报告",
                'summary': report['summary'],
                'highlights': [section['content'] for section in report['sections']],
                'suggested_questions': [
                    '把它和同行龙头对比一下',
                    '结合行业研报看它的机会和风险',
                    '给我生成更正式的答辩摘要',
                ],
                'evidence': report['evidence'],
            },
            detail=(
                f"已生成 {report['company_name']} 综合报告，"
                f"包含 {len(report['sections'])} 个分析段落与来源证据。"
            ),
        )


class CompanyDecisionBriefTool:
    name = 'company_decision_brief_tool'
    label = '决策建议生成'
    description = '负责生成管理层视角的判断、动作建议与证据引用。'
    supported_intents = (AgentIntent.COMPANY_DECISION_BRIEF,)

    def __init__(self, decision_service: DecisionService) -> None:
        self.decision_service = decision_service

    def run(self, context: WorkflowContext, analytics_service: AnalyticsService) -> ToolResult:
        company_code = str(context.matches[0]['company_code'])
        brief = self.decision_service.build_company_decision_brief(company_code, context.question)
        if brief is None:
            return FallbackTool().run(context, analytics_service)
        return ToolResult(
            payload={
                'title': f"{brief['company_name']} 决策简报",
                'summary': brief['summary'],
                'highlights': brief['key_judgements'] + brief['action_recommendations'] + brief.get('evidence_highlights', [])[:2],
                'suggested_questions': [
                    '把它和同行龙头对比一下',
                    '生成更正式的经营分析报告',
                    '继续展开风险与机会说明',
                ],
                'evidence': brief['evidence'],
            },
            detail=f"已生成 {brief['company_name']} 决策简报并完成语义证据召回。",
        )


class CompanyRiskForecastTool:
    name = 'company_risk_forecast_tool'
    label = '风险预测分析'
    description = '负责三层风险拆解、风险模型调用与监测项生成。'
    supported_intents = (AgentIntent.COMPANY_RISK_FORECAST,)

    def __init__(self, risk_service: RiskService) -> None:
        self.risk_service = risk_service

    def run(self, context: WorkflowContext, analytics_service: AnalyticsService) -> ToolResult:
        company_code = str(context.matches[0]['company_code'])
        forecast = self.risk_service.build_company_risk_forecast(company_code)
        if forecast is None:
            return FallbackTool().run(context, analytics_service)
        return ToolResult(
            payload={
                'title': f"{forecast['company_name']} 风险预测",
                'summary': forecast['summary'],
                'highlights': forecast['drivers'] + forecast['monitoring_items'],
                'suggested_questions': [
                    '给它提经营决策建议',
                    '生成更正式的企业综合报告',
                    '和同行对比风险水平',
                ],
                'evidence': forecast['evidence'],
            },
            detail=f"已生成 {forecast['company_name']} 风险预测结果。",
        )


class CompareCompaniesTool:
    name = 'company_compare_tool'
    label = '企业对比分析'
    description = '负责横向比较多家企业的经营表现、风险与证据差异。'
    supported_intents = (AgentIntent.COMPANY_COMPARE,)

    def run(self, context: WorkflowContext, analytics_service: AnalyticsService) -> ToolResult:
        comparison = analytics_service.compare_companies([str(match['company_code']) for match in context.matches])
        if comparison is None:
            return FallbackTool().run(context, analytics_service)
        return ToolResult(
            payload={
                'title': '企业对比分析',
                'summary': comparison['summary'],
                'highlights': comparison['highlights'],
                'suggested_questions': [
                    '谁的盈利质量更高',
                    '谁的研发投入更强',
                    '谁更值得重点跟踪风险',
                ],
                'evidence': comparison['evidence'],
            },
            detail=f"已完成 {len(comparison['comparison_rows'])} 家企业横向对比并输出关键胜出维度。",
        )


class IndustryTrendTool:
    name = 'industry_trend_tool'
    label = '行业趋势分析'
    description = '负责行业研报聚合、景气变化判断和宏观联动摘要。'
    supported_intents = (AgentIntent.INDUSTRY_TREND,)

    def run(self, context: WorkflowContext, analytics_service: AnalyticsService) -> ToolResult:
        overview = analytics_service.get_industry_overview()
        macro_digest = analytics_service.get_macro_digest()
        top_industries = '、'.join(item['industry_name'] for item in overview.get('top_industries', [])[:4]) or '暂无'
        macro_line = '；'.join(
            f"{item['indicator_name']}{item['indicator_value']}{item['unit']}"
            for item in macro_digest.get('items', [])[:3]
        ) or '宏观数据待补充'
        latest_titles = [row['title'] for row in overview.get('latest_rows', [])[:4]]
        return ToolResult(
            payload={
                'title': '医药赛道趋势分析',
                'summary': f"当前已接入行业研报 {overview['count']} 篇，重点覆盖 {top_industries}。",
                'highlights': [
                    f"行业研报正向观点 {overview['positive']} 篇，负向观点 {overview['negative']} 篇。",
                    f"最近的行业议题包括：{'；'.join(latest_titles) if latest_titles else '暂无'}。",
                    f"宏观环境摘要：{macro_line}。",
                ],
                'suggested_questions': [
                    '分析迈瑞医疗',
                    '分析恒瑞医药',
                    '生成一段行业趋势答辩摘要',
                ],
            },
            detail='已完成行业研报聚合、情绪统计与宏观联动摘要。',
        )


def build_agent_tools(
    decision_service: DecisionService,
    risk_service: RiskService,
    quality_service: DataQualityService,
) -> list[AgentTool]:
    return [
        FallbackTool(),
        OverviewTool(),
        DataQualityTool(quality_service),
        CompanyDiagnosisTool(),
        CompanyReportTool(),
        CompanyDecisionBriefTool(decision_service),
        CompanyRiskForecastTool(risk_service),
        CompareCompaniesTool(),
        IndustryTrendTool(),
    ]


def build_agent_skill_registry(tools: list[AgentTool]) -> AgentSkillRegistry:
    skills: list[AgentSkillSpec] = []
    by_intent: dict[AgentIntent, AgentSkillSpec] = {}
    by_tool_name: dict[str, AgentSkillSpec] = {}

    for tool in tools:
        skill = AgentSkillSpec(
            skill_id=tool.name.replace('_tool', ''),
            tool_name=tool.name,
            label=tool.label,
            description=tool.description,
            supported_intents=tool.supported_intents,
            tool=tool,
        )
        skills.append(skill)
        by_tool_name[tool.name] = skill
        for intent in tool.supported_intents:
            by_intent[intent] = skill

    return AgentSkillRegistry(skills=skills, by_intent=by_intent, by_tool_name=by_tool_name)
