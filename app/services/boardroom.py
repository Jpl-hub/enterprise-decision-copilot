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

    def _safe_metric(self, value: object, suffix: str = "") -> str:
        if value is None:
            return "暂无"
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return str(value)
        return f"{numeric:.2f}{suffix}"

    def _trust_snapshot(self) -> dict:
        trust = self.quality_service.get_trust_center_summary()
        return {
            "trust_status": trust.get("trust_status"),
            "trust_score": trust.get("trust_score"),
            "findings": list(trust.get("findings") or [])[:4],
        }

    def _macro_line(self) -> str:
        macro = self.analytics_service.get_macro_digest()
        return "；".join(
            f"{item['indicator_name']}{item['indicator_value']}{item['unit']}"
            for item in macro.get("items", [])[:2]
        ) or "宏观环境以稳态跟踪为主。"

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
        trust_center = self._trust_snapshot()
        sql_playbook = self.warehouse_service.build_company_sql_playbook(company_code=company_code, company_name=company_name)
        multimodal = self.analytics_service.get_company_multimodal_digest(company_code, report_year=int(row["report_year"]))
        if brief is None or risk is None or report is None:
            return None

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
                    f"净利率 {self._safe_metric(row.get('net_margin_pct'), suffix='%')}",
                    f"ROE {self._safe_metric(row.get('roe_pct'), suffix='%')}",
                    f"经营现金流 {self._safe_metric(row.get('operating_cashflow_million'))}",
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
        synthesis = {
            "meeting_mode": "executive_boardroom",
            "primary_call": brief.get("verdict") or "继续跟踪",
            "confidence": round((0.82 + 0.76 + 0.84 + 0.79 + 0.74) / 5, 2),
            "consensus_summary": (
                f"{company_name} 当前适合进入“管理层重点跟踪”状态。"
                f"财务和市场侧支持继续推进，风控和治理侧要求把风险阈值、来源说明和 SQL 钻取链路一起带上。"
            ),
            "action_board": [
                "经营侧：围绕利润率、现金流和研发强度做季度复盘。",
                "策略侧：围绕最新机构主题和行业景气方向安排下一轮深挖。",
                "治理侧：所有对外材料强制附带真实性声明、财报锚点和复核状态。",
                "计算侧：把公司级 SQL 钻取动作沉成标准任务，便于老师现场追问时即席展开。",
            ],
            "red_lines": [
                "经营现金流转负且流动比率下探时，会议结论自动降级。",
                "若待复核异常继续增加，不允许把本轮输出标为正式材料。",
                "如果行业景气和机构观点同步转弱，需重新评估策略优先级。",
            ],
        }
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
            "highlights": [
                synthesis["consensus_summary"],
                f"会议主结论：{synthesis['primary_call']}，风险等级 {risk['risk_level']}，可信度 {synthesis['confidence']:.2f}。",
                f"SQL 动作板已准备 {len(list(sql_playbook.get('missions') or []))} 项，可继续追问财务、研报和热度变化。",
                f"宏观补充：{self._macro_line()}",
            ],
            "panelists": panelists,
            "debate_rounds": debate_rounds,
            "synthesis": synthesis,
            "sql_playbook": sql_playbook,
            "evidence": {
                "decision_brief": brief,
                "risk_forecast": risk,
                "company_report": report,
                "quality_snapshot": quality_snapshot,
                "trust_center": trust_center,
                "query_profile": brief.get("evidence", {}).get("query_profile"),
                "query_terms": brief.get("evidence", {}).get("query_terms", []),
                "semantic_stock_reports": brief.get("evidence", {}).get("semantic_stock_reports", []),
                "semantic_industry_reports": brief.get("evidence", {}).get("semantic_industry_reports", []),
                "multimodal_digest": multimodal,
                "macro_items": macro.get("items", []),
                "evidences": evidences,
            },
        }

    def build_compare_boardroom(self, company_codes: list[str], question: str) -> dict | None:
        comparison = self.analytics_service.compare_companies(company_codes)
        if comparison is None:
            return None
        company_rows = list(comparison.get("comparison_rows") or [])
        company_names = [str(item.get("company_name") or "") for item in company_rows]
        joined_names = " vs ".join(name for name in company_names if name) or "双企业"
        winner_name = str(comparison.get("winner_company_name") or company_names[0] if company_names else "领先方")
        dimensions = list(comparison.get("dimensions") or [])
        sql_playbook = self.warehouse_service.build_compare_sql_playbook(company_codes)
        trust_center = self._trust_snapshot()

        panelists = [
            self._panelist_card(
                agent_id="cfo-dual",
                role_label="财务对抗官",
                stance=f"{winner_name} 当前在综合表现和关键财务分上占优，适合被会议视为领先方。",
                confidence=0.83,
                evidence_focus=[str(item.get("dimension") or "") for item in dimensions[:3] if str(item.get("dimension") or "")],
                challenge="若季度口径一变，当前胜负判断可能需要重排。",
                sql_focus="双企业财务对比查询",
            ),
            self._panelist_card(
                agent_id="strategy-dual",
                role_label="策略对抗官",
                stance="会议需要把领先方的优势拆成可复制打法，而不是只给输赢结论。",
                confidence=0.77,
                evidence_focus=[str(item.get("conclusion") or "")[:40] for item in dimensions[:2]],
                challenge="如果双方差距主要来自单一维度，策略结论会失真。",
                sql_focus="观点热度与行业主题差异",
            ),
            self._panelist_card(
                agent_id="risk-dual",
                role_label="风险仲裁官",
                stance="对抗会不只看谁更强，更要看谁在风险水平、现金流和经营韧性上更稳。",
                confidence=0.8,
                evidence_focus=[str(item.get("dimension") or "") for item in dimensions if str(item.get("dimension") or "") == "风险水平"] or ["风险水平"],
                challenge="如果领先方同时伴随更高波动，会议不能直接给出单边结论。",
                sql_focus="风险水平与现金流对比",
            ),
            self._panelist_card(
                agent_id="sql-dual",
                role_label="对抗计算官",
                stance=f"当前 SQL 动作板已准备 {len(list(sql_playbook.get('queries') or []))} 条查询模板，可支持老师现场追问对抗细节。",
                confidence=0.75,
                evidence_focus=[f"任务数 {len(list(sql_playbook.get('missions') or []))}", f"查询模板 {len(list(sql_playbook.get('queries') or []))}"],
                challenge="如果要扩成三方或行业对抗，需要把多企业批任务进一步标准化。",
                sql_focus="双企业 SQL playbook",
            ),
        ]
        debate_rounds = [
            {
                "round": 1,
                "topic": "先判断当前谁领先",
                "speaker_notes": [
                    {"agent_id": "cfo-dual", "statement": panelists[0]["stance"]},
                    {"agent_id": "risk-dual", "statement": panelists[2]["stance"]},
                ],
                "consensus_delta": f"初步认为 {winner_name} 领先，但仍需确认这种领先是否稳健。",
            },
            {
                "round": 2,
                "topic": "把领先方优势转成打法",
                "speaker_notes": [
                    {"agent_id": "strategy-dual", "statement": panelists[1]["stance"]},
                    {"agent_id": "sql-dual", "statement": panelists[3]["stance"]},
                ],
                "consensus_delta": "会议要求输出可复制打法和追问模板，而不是只停在表格结论。",
            },
        ]
        synthesis = {
            "meeting_mode": "compare_boardroom",
            "primary_call": f"{winner_name} 当前领先",
            "confidence": 0.79,
            "consensus_summary": f"{joined_names} 当前更适合用“对抗会议”方式展示，核心结论是 {winner_name} 领先，但必须同步解释领先维度和风险代价。",
            "action_board": [
                "先固定评判口径：综合表现、盈利、成长、韧性、风险。",
                "把领先方优势转成打法，把落后方短板转成改进项。",
                "现场追问时用 SQL 动作板继续展开具体指标差异。",
            ],
            "red_lines": [
                "如果只赢一个维度，不能夸大成全面领先。",
                "如果风险水平显著更高，领先方必须降级解释。",
            ],
        }
        evidences = []
        for company in list(comparison.get("evidence", {}).get("companies") or []):
            evidences.extend(list(company.get("research_digest", {}).get("latest_rows") or []))
            evidences.extend(list(company.get("industry_digest", {}).get("latest_rows") or []))
        return {
            "company_code": ",".join(str(code) for code in company_codes),
            "company_name": joined_names,
            "question": question,
            "summary": synthesis["consensus_summary"],
            "highlights": [
                synthesis["consensus_summary"],
                f"核心赢家：{winner_name}",
                f"关键维度：{'、'.join(str(item.get('dimension') or '') for item in dimensions[:4])}",
                f"SQL 对抗动作板已准备 {len(list(sql_playbook.get('missions') or []))} 项。",
            ],
            "panelists": panelists,
            "debate_rounds": debate_rounds,
            "synthesis": synthesis,
            "sql_playbook": sql_playbook,
            "evidence": {
                "comparison": comparison,
                "trust_center": trust_center,
                "companies": comparison.get("evidence", {}).get("companies", []),
                "freshness": comparison.get("evidence", {}).get("freshness"),
                "semantic_stock_reports": evidences[:6],
                "semantic_industry_reports": [],
                "evidences": [],
            },
        }

    def build_industry_boardroom(self, question: str) -> dict:
        overview = self.analytics_service.get_industry_overview()
        dashboard = self.analytics_service.get_dashboard_payload()
        trust_center = self._trust_snapshot()
        sql_playbook = self.warehouse_service.build_industry_sql_playbook(question)
        top_industries = [str(item.get("industry_name") or "") for item in list(overview.get("top_industries") or [])[:4] if str(item.get("industry_name") or "")]
        latest_titles = [str(item.get("title") or "") for item in list(overview.get("latest_rows") or [])[:4] if str(item.get("title") or "")]
        panelists = [
            self._panelist_card(
                agent_id="macro-chair",
                role_label="宏观主持官",
                stance=f"当前赛道判断要把行业热度、宏观脉冲和企业池样本一起看，宏观补充为：{self._macro_line()}",
                confidence=0.78,
                evidence_focus=list(latest_titles[:2]) or ["行业议题待补充"],
                challenge="如果宏观脉冲和行业主题方向相反，专题会议结论必须谨慎。",
                sql_focus="行业热度与宏观联动",
            ),
            self._panelist_card(
                agent_id="research-chair",
                role_label="行业研究官",
                stance=f"当前已接入行业研报 {overview.get('count', 0)} 篇，重点覆盖 {('、'.join(top_industries) or '核心医药赛道')}。",
                confidence=0.81,
                evidence_focus=latest_titles[:3],
                challenge="如果行业研报覆盖面不足，景气结论会缺少深度。",
                sql_focus="industry_heat 行业热度视图",
            ),
            self._panelist_card(
                agent_id="strategy-chair",
                role_label="专题策略官",
                stance="专题会议的目标不是复述赛道名词，而是给出老师能记住的主题判断和后续深挖方向。",
                confidence=0.76,
                evidence_focus=[str(item.get("company_name") or "") for item in list(dashboard.get("ranking") or [])[:3]],
                challenge="如果样本池太小，赛道专题会容易被看成演示级别。",
                sql_focus="企业池与行业主题联动",
            ),
            self._panelist_card(
                agent_id="governance-chair",
                role_label="可信度官",
                stance=f"赛道专题会当前信任状态 {trust_center.get('trust_status')}，可以展示，但必须把数据来源与覆盖范围讲明白。",
                confidence=0.79,
                evidence_focus=[f"trust {trust_center.get('trust_status')}", f"score {trust_center.get('trust_score')}"],
                challenge="若来源合规和覆盖范围说不清，专题展示会失分。",
                sql_focus="trust center / source registry",
            ),
        ]
        debate_rounds = [
            {
                "round": 1,
                "topic": "先判断当前赛道是不是值得重点讲",
                "speaker_notes": [
                    {"agent_id": "research-chair", "statement": panelists[1]["stance"]},
                    {"agent_id": "macro-chair", "statement": panelists[0]["stance"]},
                ],
                "consensus_delta": "形成行业专题可讲、但必须兼顾宏观和样本边界的初步判断。",
            },
            {
                "round": 2,
                "topic": "把赛道专题转成老师能记住的展示面",
                "speaker_notes": [
                    {"agent_id": "strategy-chair", "statement": panelists[2]["stance"]},
                    {"agent_id": "governance-chair", "statement": panelists[3]["stance"]},
                ],
                "consensus_delta": "要求专题会同时给出主题、样本、可信度和追问路径。",
            },
        ]
        synthesis = {
            "meeting_mode": "industry_boardroom",
            "primary_call": "行业专题会",
            "confidence": 0.79,
            "consensus_summary": "当前赛道专题适合用“行业专题会议室”展示，把宏观脉冲、行业热度、样本池和可信度放在同一张画布上。",
            "action_board": [
                "围绕行业热度最高的 3-4 个主题建立专题叙事。",
                "把行业判断和企业池 Top 样本联动起来，避免空谈赛道。",
                "老师追问时可继续下钻到公司级会议室或对抗会。",
            ],
            "red_lines": [
                "不能只报行业热词，必须解释样本和数据来源。",
                "如果行业研报和宏观信号冲突，需明确提示分歧。",
            ],
        }
        return {
            "company_code": None,
            "company_name": "医药行业专题",
            "question": question,
            "summary": synthesis["consensus_summary"],
            "highlights": [
                synthesis["consensus_summary"],
                f"重点行业：{'、'.join(top_industries) or '医药赛道'}",
                f"最近议题：{'；'.join(latest_titles) or '专题议题整理中'}",
                f"SQL 专题动作板已准备 {len(list(sql_playbook.get('missions') or []))} 项。",
            ],
            "panelists": panelists,
            "debate_rounds": debate_rounds,
            "synthesis": synthesis,
            "sql_playbook": sql_playbook,
            "evidence": {
                "industry_overview": overview,
                "dashboard": dashboard,
                "trust_center": trust_center,
                "semantic_stock_reports": [],
                "semantic_industry_reports": overview.get("latest_rows", []),
                "macro_items": self.analytics_service.get_macro_digest().get("items", []),
                "evidences": [],
            },
        }
