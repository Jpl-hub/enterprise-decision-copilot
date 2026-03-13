from __future__ import annotations

from app.services.analytics import AnalyticsService
from app.services.risk_model import RiskModelService


class RiskService:
    def __init__(self, analytics_service: AnalyticsService, risk_model_service: RiskModelService | None = None) -> None:
        self.analytics_service = analytics_service
        self.risk_model_service = risk_model_service or RiskModelService()

    def build_company_risk_forecast(self, company_code: str) -> dict | None:
        row = self.analytics_service.get_company_record(company_code)
        if row is None:
            return None

        trend = self.analytics_service.get_company_trend_digest(company_code)
        research = self.analytics_service.get_company_research_digest(company_code)
        industry = self.analytics_service.get_company_industry_digest(company_code)
        multimodal = self.analytics_service.get_company_multimodal_digest(company_code, report_year=int(row["report_year"]))
        freshness = self.analytics_service._build_company_freshness_digest(row, research, industry)
        history = self.analytics_service.get_company_history(company_code)
        model_prediction = self.risk_model_service.predict_company(history)

        score = 18.0
        drivers = []

        debt_ratio = float(row.get('debt_ratio_pct') or 0)
        cash_to_short_debt = float(row.get('cash_to_short_debt') or 0)
        operating_cashflow = float(row.get('operating_cashflow_million') or 0)
        current_ratio = float(row.get('current_ratio') or 0)
        revenue_cagr = float(trend.get('revenue_cagr_pct') or 0)
        profit_cagr = float(trend.get('profit_cagr_pct') or 0)
        cashflow_change = float(trend.get('operating_cashflow_change_million') or 0)
        negative_reports = int(research.get('negative') or 0)

        if debt_ratio >= 60:
            score += 18
            drivers.append('资产负债率偏高，需关注杠杆压力。')
        elif debt_ratio >= 50:
            score += 10
            drivers.append('资产负债率进入关注区间。')

        if cash_to_short_debt < 1:
            score += 18
            drivers.append('短债覆盖能力不足。')
        elif cash_to_short_debt < 1.5:
            score += 8
            drivers.append('短债覆盖缓冲偏弱。')

        if operating_cashflow < 0:
            score += 22
            drivers.append('经营现金流为负，短期运营承压。')
        elif operating_cashflow > 0 and current_ratio >= 1.5:
            score -= 8
            drivers.append('现金流与流动性表现稳健，对风险有对冲作用。')

        if current_ratio < 1.2:
            score += 12
            drivers.append('流动比率偏低，短期偿债压力上升。')

        if revenue_cagr < 0:
            score += 10
            drivers.append('营收趋势走弱，未来增长存在不确定性。')
        elif revenue_cagr >= 10:
            score -= 4
            drivers.append('营收趋势保持较快增长。')

        if profit_cagr < 0:
            score += 12
            drivers.append('利润趋势下行，盈利稳定性需要重点观察。')
        elif profit_cagr >= 10:
            score -= 6
            drivers.append('利润趋势保持上行。')

        if cashflow_change < 0:
            score += 8
            drivers.append('经营现金流同比趋势转弱。')

        if negative_reports > 0:
            report_penalty = min(15, negative_reports * 4)
            score += report_penalty
            drivers.append(f'近两年存在 {negative_reports} 篇偏谨慎研报。')

        heuristic_score = max(0.0, min(100.0, score))
        score = heuristic_score
        if model_prediction is not None:
            score = round(heuristic_score * 0.65 + float(model_prediction['predicted_score']) * 0.35, 1)
            drivers.append(f"表格模型预测下一期高风险概率 {float(model_prediction['high_risk_probability']) * 100:.1f}% 。")
        if score >= 65:
            risk_level = '高'
        elif score >= 35:
            risk_level = '中'
        else:
            risk_level = '低'

        if not drivers:
            drivers.append('当前未触发显著风险因子，需保持常规监测。')

        monitoring_items = [
            f'资产负债率：{debt_ratio:.2f}%',
            f'流动比率：{current_ratio:.2f}',
            f'现金短债比：{cash_to_short_debt:.2f}',
            f'经营现金流：{operating_cashflow:.2f} 百万元',
            f'营收 CAGR：{revenue_cagr:.2f}%',
            f'利润 CAGR：{profit_cagr:.2f}%',
        ]

        scenario_summary = (
            f"{row['company_name']} 未来一阶段风险预测为 {risk_level} 风险，预测分值 {score:.1f}。"
            f"结合 {trend['start_year']}-{trend['end_year']} 年趋势、{research['count']} 篇个股研报和 {industry['count']} 篇行业研报，"
            '建议持续跟踪现金流、负债结构和机构观点变化。'
        )

        return {
            'company_code': str(company_code),
            'company_name': row['company_name'],
            'risk_score': round(score, 1),
            'risk_level': risk_level,
            'summary': scenario_summary,
            'drivers': drivers,
            'monitoring_items': monitoring_items,
            'heuristic_score': round(heuristic_score, 1),
            'model_prediction': model_prediction,
            'evidence': {
                'financial_source_url': row.get('source_url'),
                'trend_digest': trend,
                'research_digest': research,
                'industry_digest': industry,
                'multimodal_digest': multimodal,
                'heuristic_score': round(heuristic_score, 1),
                'model_prediction': model_prediction,
                'evidences': self.analytics_service._build_unified_evidences(
                    financial_source_url=row.get('source_url'),
                    multimodal=multimodal,
                    stock_reports=research.get('latest_rows', []),
                    industry_reports=industry.get('latest_rows', []),
                ),
                **freshness,
            },
        }
