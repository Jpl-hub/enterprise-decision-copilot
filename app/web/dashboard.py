from __future__ import annotations


def build_dashboard_context(app_name: str, payload: dict) -> dict:
    return {
        "app_name": app_name,
        "payload": payload,
        "industry": payload.get("targets", [{}])[0].get("industry", "目标行业") if payload.get("targets") else "目标行业",
        "suggested_entries": [
            {
                "title": "企业诊断",
                "description": "单企业经营质量、盈利、研发、现金流诊断",
                "tag": "Agent",
            },
            {
                "title": "行业联动",
                "description": "企业财务 + 行业研报 + 宏观指标联动分析",
                "tag": "RAG",
            },
            {
                "title": "决策简报",
                "description": "经营判断、行动建议与语义证据召回",
                "tag": "Brief",
            },
            {
                "title": "风险预测",
                "description": "未来风险等级、驱动因素与监测指标输出",
                "tag": "Risk",
            },
        ],
        "persona_entries": [
            {
                "title": "投资者场景",
                "description": "自然语言问数、企业对比、行业趋势与价值线索发现。",
                "prompt": "比较迈瑞医疗和联影医疗，并给出投资研究摘要",
                "tag": "Investor",
            },
            {
                "title": "企业管理者场景",
                "description": "经营诊断、行业对标、行动建议和战略优化支持。",
                "prompt": "给恒瑞医药提经营决策建议，并说明原因",
                "tag": "Manager",
            },
            {
                "title": "监管风控场景",
                "description": "异常监测、风险预测、风险来源拆解与持续跟踪。",
                "prompt": "预测联影医疗的风险，并列出监测指标",
                "tag": "Risk Control",
            },
        ],
    }
