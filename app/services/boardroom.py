from __future__ import annotations

from app.services.analytics import AnalyticsService
from app.services.decision import DecisionService
from app.services.quality import DataQualityService
from app.services.risk import RiskService
from app.services.warehouse import WarehouseService


class BoardroomService:
    def __init__(
        self,
        analytics_service: AnalyticsService,
        decision_service: DecisionService,
        risk_service: RiskService,
        quality_service: DataQualityService,
        warehouse_service: WarehouseService | None = None,
    ) -> None:
        self.analytics_service = analytics_service
        self.decision_service = decision_service
        self.risk_service = risk_service
        self.quality_service = quality_service
        self.warehouse_service = warehouse_service or WarehouseService()

    def _build_sql_playbook(self, company_code: str, company_name: str) -> dict:
        return self.warehouse_service.build_company_sql_playbook(company_code=company_code, company_name=company_name)

    def _panelist_card(
        self,
        *,
        agent_id: str,
        role_label: str,
        stance: str,
        confidence: float,
        evidence_focus: list[str],
        challenge: str,
        sql_focus: str | None = None,
    ) -> dict:
        return {
            "agent_id": agent_id,
            "role_label": role_label,
            "stance": stance,
            "confidence": round(confidence, 2),
            "evidence_focus": evidence_focus[:4],
            "challenge": challenge,
            "sql_focus": sql_focus,
        }

    def build_company_boardroom(self, company_code: str, question: str) -> dict | None:
        row = self.analytics_service.get_company_record(company_code)
        if row is None:
            return None

        company_name = str(row["company_name"])
        trend = self.analytics_service.get_company_trend_digest(company_code)
        brief = self.decision_service.build_company_decision_brief(company_code, question)
        risk = self.risk_service.build_company_risk_forecast(company_code)
        report = self.analytics_service.get_company_report(company_code)
        research = self.analytics_service.get_company_research_digest(company_code)
        industry = self.analytics_service.get_company_industry_digest(company_code)
        macro = self.analytics_service.get_macro_digest()
        quality_snapshot = self.quality_service.get_company_quality_snapshot(company_code)
        trust_center = self.quality_service.get_trust_center_summary()
        sql_playbook = self._build_sql_playbook(company_code=company_code, company_name=company_name)
        multimodal = self.analytics_service.get_company_multimodal_digest(company_code, report_year=int(row["report_year"]))

        if brief is None or risk is None or report is None:
            return None

        macro_line = "；".join(
            f"{item['indicator_name']}{item['indicator_value']}{item['unit']}"
            for item in macro.get("items", [])[:2]
        ) or "宏观环境以稳态跟踪为主。"
        market_focus = [
            *[str(item).strip() for item in list(research.get("latest_titles") or [])[:2] if str(item).strip()],
            *[str(item).strip() for item in list(industry.get("latest_titles") or [])[:2] if str(item).strip()],
        ]
        data_issue_count = len(list(quality_snapshot.get("company_anomalies") or [])) + len(list(quality_snapshot.get("company_review_queue") or []))

        panelists = [
            self._panelist_card(
                agent_id="cfo",
                role_label="财务分析官",
                stance=(
                    f"{company_name} 当前营收 CAGR {float(trend.get('revenue_cagr_pct') or 0):.2f}% 、"
                    f"利润 CAGR {float(trend.get('profit_cagr_pct') or 0):.2f}% ，"
                    f"综合得分 {float(row.get('total_score') or 0):.1f}，适合继续深挖盈利质量。"
                ),
                confidence=0.82,
                evidence_focus=[
                    f"净利率 {_safe_metric(row.get('net_margin_pct'), suffix='%')}",
                    f"ROE {_safe_metric(row.get('roe_pct'), suffix='%')}",
                    f"经营现金流 {_safe_metric(row.get('operating_cashflow_million'))}",
                ],
                challenge="如果后续现金流和利润剪刀差继续扩大，需要下调会议结论。",
                sql_focus="mart.company_overview 财务主表",
            ),
            self._panelist_card(
                agent_id="cmo",
                role_label="市场策略官",
                stance=(
                    f"机构与行业证据显示 {company_name} 仍具备主题承接力，"
                    f"当前个股研报 {research.get('count', 0)} 篇、行业研报 {industry.get('count', 0)} 篇。"
                ),
                confidence=0.76,
                evidence_focus=market_focus or ["研报主题仍需扩容"],
                challenge="若行业景气与机构观点出现背离，市场侧需要重新排序优先级。",
                sql_focus="company_research_heat / industry_heat 热度视图",
            ),
            self._panelist_card(
                agent_id="cro",
                role_label="风险控制官",
                stance=(
                    f"风险模型当前判断为 {risk['risk_level']} 风险，预测分值 {float(risk['risk_score']):.1f}，"
                    "会议可以推进，但必须保留季度监测和红线约束。"
                ),
                confidence=0.84,
                evidence_focus=list(risk.get("monitoring_items") or [])[:3],
                challenge="若负债率、流动比率或经营现金流拐头，需要立即触发风险复议。",
                sql_focus="风险特征回放与季度监控",
            ),
            self._panelist_card(
                agent_id="dgo",
                role_label="数据治理官",
                stance=(
                    f"当前系统信任状态 {trust_center.get('trust_status')}，"
                    f"{company_name} 侧待处理问题 {data_issue_count} 项，"
                    "结论可对外展示，但需保留真实性声明和复核入口。"
                ),
                confidence=0.79,
                evidence_focus=[
                    f"官方覆盖率 {float(quality_snapshot.get('official_report_coverage_ratio') or 0) * 100:.1f}%",
                    f"异常 {len(list(quality_snapshot.get('company_anomalies') or []))} 条",
                    f"复核队列 {len(list(quality_snapshot.get('company_review_queue') or []))} 条",
                ],
                challenge="若存在未复核异常，不建议把会议结论直接作为最终外发材料。",
                sql_focus="数据治理 / 可信度控制面",
            ),
            self._panelist_card(
                agent_id="sql-chief",
                role_label="计算与SQL官",
                stance=(
                    f"单机湖仓当前引擎为 {sql_playbook.get('current_engine') or 'python + duckdb'}，"
                    "已具备管理层追问所需的 SQL 化钻取能力。"
                ),
                confidence=0.74,
                evidence_focus=[
                    f"仓层就绪：{'是' if sql_playbook.get('warehouse_ready') else '否'}",
                    f"任务数 {len(list(sql_playbook.get('missions') or []))}",
                    f"查询模板 {len(list(sql_playbook.get('queries') or []))}",
                ],
                challenge="如果公司池和季度粒度继续扩张，需要尽快把批任务和查询层做成标准作业。",
                sql_focus="DuckDB mart / Spark-ready 任务清单",
            ),
        ]

        debate_rounds = [
            {
                "round": 1,
                "topic": "先看能不能继续重点推进",
                "speaker_notes": [
                    {"agent_id": "cfo", "statement": panelists[0]["stance"]},
                    {"agent_id": "cmo", "statement": panelists[1]["stance"]},
                    {"agent_id": "cro", "statement": panelists[2]["stance"]},
                ],
                "consensus_delta": "形成“可以推进，但要保留风控约束”的初步共识。",
            },
            {
                "round": 2,
                "topic": "争议点放在数据可信度和扩样准备",
                "speaker_notes": [
                    {"agent_id": "dgo", "statement": panelists[3]["stance"]},
                    {"agent_id": "sql-chief", "statement": panelists[4]["stance"]},
                    {"agent_id": "cfo", "statement": "如果 SQL 钻取和财报锚点同步可追溯，管理层材料可信度会显著提高。"},
                ],
                "consensus_delta": "要求所有结论附带来源与治理状态，不允许黑箱输出。",
            },
            {
                "round": 3,
                "topic": "收敛成管理层动作",
                "speaker_notes": [
                    {"agent_id": "cmo", "statement": "先围绕高景气和机构高频主题做资源聚焦。"},
                    {"agent_id": "cro", "statement": "同步设季度红线和触发阈值。"},
                    {"agent_id": "sql-chief", "statement": "把财务、研报、风险、治理查询做成标准追问动作。"},
                ],
                "consensus_delta": "会议结论转化为三条可执行动作和一套后续追问清单。",
            },
        ]

        action_board = [
            "经营侧：围绕利润率、现金流和研发强度做季度复盘。",
            "策略侧：围绕最新机构主题和行业景气方向安排下一轮深挖。",
            "治理侧：所有对外材料强制附带真实性声明、财报锚点和复核状态。",
            "计算侧：把公司级 SQL 钻取动作沉成标准任务，便于老师现场追问时即席展开。",
        ]
        red_lines = [
            "经营现金流转负且流动比率下探时，会议结论自动降级。",
            "若待复核异常继续增加，不允许把本轮输出标为正式材料。",
            "如果行业景气和机构观点同步转弱，需重新评估策略优先级。",
        ]
        synthesis = {
            "meeting_mode": "executive_boardroom",
            "primary_call": brief.get("verdict") or "继续跟踪",
            "confidence": round((0.82 + 0.76 + 0.84 + 0.79 + 0.74) / 5, 2),
            "consensus_summary": (
                f"{company_name} 当前适合进入“管理层重点跟踪”状态。"
                f"财务和市场侧支持继续推进，风控和治理侧要求把风险阈值、来源说明和 SQL 钻取链路一起带上。"
            ),
            "action_board": action_board,
            "red_lines": red_lines,
        }

        highlights = [
            synthesis["consensus_summary"],
            f"会议主结论：{synthesis['primary_call']}，风险等级 {risk['risk_level']}，可信度 {synthesis['confidence']:.2f}。",
            f"SQL 动作板已准备 {len(list(sql_playbook.get('missions') or []))} 项，可继续追问财务、研报和热度变化。",
            f"宏观补充：{macro_line}",
        ]

        evidences = self.analytics_service._build_unified_evidences(
            financial_source_url=row.get("source_url"),
            multimodal=multimodal,
            stock_reports=list(brief.get("evidence", {}).get("semantic_stock_reports") or []),
            industry_reports=list(brief.get("evidence", {}).get("semantic_industry_reports") or []),
            limit=10,
        )

        return {
            "company_code": str(company_code),
            "company_name": company_name,
            "question": question,
            "summary": synthesis["consensus_summary"],
            "highlights": highlights,
            "panelists": panelists,
            "debate_rounds": debate_rounds,
            "synthesis": synthesis,
            "sql_playbook": sql_playbook,
            "evidence": {
                "decision_brief": brief,
                "risk_forecast": risk,
                "company_report": report,
                "quality_snapshot": quality_snapshot,
                "trust_center": {
                    "trust_status": trust_center.get("trust_status"),
                    "trust_score": trust_center.get("trust_score"),
                    "findings": list(trust_center.get("findings") or [])[:4],
                },
                "query_profile": brief.get("evidence", {}).get("query_profile"),
                "query_terms": brief.get("evidence", {}).get("query_terms", []),
                "semantic_stock_reports": brief.get("evidence", {}).get("semantic_stock_reports", []),
                "semantic_industry_reports": brief.get("evidence", {}).get("semantic_industry_reports", []),
                "multimodal_digest": multimodal,
                "macro_items": macro.get("items", []),
                "evidences": evidences,
            },
        }


def _safe_metric(value: object, suffix: str = "") -> str:
    if value is None:
        return "暂无"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{numeric:.2f}{suffix}"
