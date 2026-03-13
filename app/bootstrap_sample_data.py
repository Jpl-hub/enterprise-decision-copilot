from __future__ import annotations

import csv
import json
from pathlib import Path


FINANCIAL_COLUMNS = [
    "company_code",
    "company_name",
    "report_year",
    "revenue_million",
    "net_profit_million",
    "gross_margin_pct",
    "net_margin_pct",
    "rd_ratio_pct",
    "debt_ratio_pct",
    "current_ratio",
    "cash_to_short_debt",
    "inventory_turnover",
    "receivable_turnover",
    "operating_cashflow_million",
    "roe_pct",
    "source_url",
    "published_at",
]

RESEARCH_COLUMNS = [
    "company_code",
    "company_name",
    "report_date",
    "title",
    "analyst_view",
    "institution",
    "sentiment",
    "content",
    "source_url",
]

INDUSTRY_COLUMNS = [
    "industry_code",
    "industry_name",
    "report_date",
    "title",
    "institution",
    "sentiment",
    "content",
    "source_url",
]

UNIVERSE_COLUMNS = [
    "company_code",
    "company_name",
    "exchange",
    "market",
    "industry_code",
    "industry_name",
    "report_count",
    "institution_count",
    "positive_count",
    "neutral_count",
    "negative_count",
    "latest_report_date",
    "earliest_report_date",
    "in_target_pool",
    "latest_report_title",
    "latest_source_url",
]

MACRO_COLUMNS = ["period", "indicator_name", "indicator_value", "unit", "source_url"]

PERIODIC_COLUMNS = [
    "exchange",
    "company_code",
    "company_name",
    "period_type",
    "period_label",
    "report_year",
    "title",
    "published_at",
    "source_url",
]

QUALITY_COLUMNS = [
    "company_code",
    "company_name",
    "report_year",
    "filled_fields",
    "field_coverage_ratio",
    "critical_fields_missing",
    "anomaly_flags",
]

MODEL_FEATURE_COLUMNS = [
    "revenue_million",
    "net_profit_million",
    "gross_margin_pct",
    "net_margin_pct",
    "rd_ratio_pct",
    "debt_ratio_pct",
    "current_ratio",
    "cash_to_short_debt",
    "inventory_turnover",
    "receivable_turnover",
    "operating_cashflow_million",
    "roe_pct",
    "revenue_yoy_pct",
    "profit_yoy_pct",
    "cashflow_yoy_change_million",
    "debt_ratio_change_pct",
    "current_ratio_change",
]

SAMPLE_COMPANIES = {
    "600276": {
        "company_name": "恒瑞医药",
        "exchange": "SSE",
        "industry_name": "化学制药",
        "metrics": {
            2022: [21200, 4100, 84.0, 19.3, 23.0, 29.0, 2.10, 3.20, 1.60, 8.00, 3600, 15.8],
            2023: [22800, 4350, 83.0, 19.1, 24.0, 30.0, 2.00, 3.10, 1.70, 7.90, 3800, 16.2],
            2024: [24100, 4520, 82.0, 18.8, 25.0, 31.0, 1.90, 3.00, 1.80, 7.70, 4000, 16.0],
        },
    },
    "300760": {
        "company_name": "迈瑞医疗",
        "exchange": "SZSE",
        "industry_name": "医疗器械",
        "metrics": {
            2022: [30300, 9600, 65.0, 31.7, 11.2, 28.0, 2.20, 4.10, 3.20, 4.80, 10500, 31.0],
            2023: [34900, 11500, 66.0, 33.0, 11.4, 27.0, 2.40, 4.40, 3.40, 5.00, 12400, 32.0],
            2024: [39500, 12800, 67.0, 32.4, 11.8, 26.0, 2.50, 4.60, 3.50, 5.10, 13800, 31.5],
        },
    },
    "300015": {
        "company_name": "爱尔眼科",
        "exchange": "SZSE",
        "industry_name": "医疗服务",
        "metrics": {
            2022: [16100, 2500, 45.0, 15.5, 1.6, 38.0, 1.60, 1.80, 6.10, 9.10, 2800, 18.0],
            2023: [17900, 2900, 46.0, 16.2, 1.7, 39.0, 1.50, 1.70, 6.00, 9.00, 2950, 19.0],
            2024: [20100, 3300, 47.0, 16.4, 1.9, 40.0, 1.40, 1.60, 5.80, 8.80, 3100, 20.0],
        },
    },
    "603939": {
        "company_name": "益丰药房",
        "exchange": "SSE",
        "industry_name": "医药商业",
        "metrics": {
            2022: [17400, 1160, 38.0, 6.7, 1.1, 56.0, 1.25, 0.95, 8.90, 18.00, 800, 12.0],
            2023: [19800, 1320, 39.0, 6.8, 1.2, 57.0, 1.22, 0.92, 9.10, 18.50, 760, 12.5],
            2024: [22400, 1490, 40.0, 6.7, 1.2, 58.0, 1.18, 0.88, 9.20, 19.00, 710, 13.0],
        },
    },
    "688271": {
        "company_name": "联影医疗",
        "exchange": "SSE",
        "industry_name": "医疗器械",
        "metrics": {
            2022: [9200, 1800, 48.0, 19.6, 12.5, 34.0, 1.80, 2.50, 2.10, 3.20, 1600, 15.0],
            2023: [10800, 2100, 49.0, 19.4, 13.0, 33.0, 1.90, 2.60, 2.20, 3.30, 1900, 16.0],
            2024: [12600, 2500, 50.0, 19.8, 13.6, 32.0, 2.00, 2.80, 2.30, 3.50, 2300, 17.0],
        },
    },
    "603259": {
        "company_name": "药明康德",
        "exchange": "SSE",
        "industry_name": "医疗研发外包",
        "metrics": {
            2022: [39200, 8600, 41.0, 21.9, 6.4, 36.0, 1.70, 1.70, 4.60, 4.50, 6200, 22.0],
            2023: [40300, 9100, 42.0, 22.6, 6.6, 35.0, 1.80, 1.80, 4.80, 4.40, 6600, 23.0],
            2024: [42100, 9600, 43.0, 22.8, 6.8, 34.0, 1.90, 1.90, 4.90, 4.30, 7000, 24.0],
        },
    },
}

SAMPLE_RESEARCH_REPORTS = [
    ["300760", "迈瑞医疗", "2026-02-12", "迈瑞医疗海外增长和 AI 医疗设备双轮驱动", "海外订单与 AI 设备升级继续拉动高端器械增长。", "国盛证券", "positive", "迈瑞医疗海外业务增长稳健，AI 医疗设备升级推动高端监护和体外诊断产品放量，同时现金流和盈利能力保持强势。", "https://data.eastmoney.com/report/300760-overseas-growth.html"],
    ["300760", "迈瑞医疗", "2025-11-18", "迈瑞医疗需要关注海外汇率与集采扰动", "汇率波动和部分集采节奏可能带来短期扰动。", "中信建投", "negative", "迈瑞医疗海外增长仍强，但需关注部分区域汇率波动、国内集采节奏和渠道调整带来的阶段性风险。", "https://data.eastmoney.com/report/300760-risk-watch.html"],
    ["688271", "联影医疗", "2026-01-20", "联影医疗高端影像设备国产替代继续推进", "高端影像设备装机与海外突破形成新催化。", "华泰证券", "positive", "联影医疗在高端影像设备领域持续推进国产替代，海外市场打开新空间，但经营上仍要关注装机节奏和费用投放。", "https://data.eastmoney.com/report/688271-upstream-device.html"],
    ["688271", "联影医疗", "2025-10-22", "联影医疗经营风险主要来自订单兑现节奏", "订单兑现节奏和医院采购周期是核心风险。", "招商证券", "negative", "联影医疗当前最需要警惕的经营风险是订单兑现节奏波动，以及医院采购周期变化对收入确认的影响。", "https://data.eastmoney.com/report/688271-risk.html"],
    ["600276", "恒瑞医药", "2026-02-08", "恒瑞医药创新药布局进入收获阶段", "创新药商业化与研发投入形成共振。", "广发证券", "positive", "恒瑞医药创新药布局持续深化，研发投入保持高位，创新药商业化节奏和国际合作是未来两年的核心看点。", "https://data.eastmoney.com/report/600276-innovation.html"],
    ["600276", "恒瑞医药", "2025-09-26", "恒瑞医药研发投入维持高位", "高研发强度支撑中长期产品梯队。", "兴业证券", "positive", "恒瑞医药研发投入维持高位，创新药产品梯队不断丰富，短期利润承压但中长期创新逻辑稳固。", "https://data.eastmoney.com/report/600276-rd.html"],
    ["300015", "爱尔眼科", "2026-01-15", "爱尔眼科现金流稳中向好但扩张节奏要控", "现金流改善，但扩张与并购节奏需要管理。", "天风证券", "positive", "爱尔眼科现金流维持稳健，门店扩张和外延并购仍是成长主线，但扩张节奏需要和盈利质量同步匹配。", "https://data.eastmoney.com/report/300015-cashflow.html"],
    ["300015", "爱尔眼科", "2025-10-30", "爱尔眼科扩张压力和商誉消化仍需跟踪", "扩张带来的管理复杂度和商誉压力仍需观察。", "国金证券", "negative", "爱尔眼科的现金流表现总体平稳，但扩张压力、区域整合和商誉消化情况仍需持续跟踪。", "https://data.eastmoney.com/report/300015-expansion.html"],
    ["603939", "益丰药房", "2026-01-10", "益丰药房门店扩张延续但现金短债比承压", "门店扩张延续，现金短债比是短期监测点。", "海通证券", "negative", "益丰药房门店扩张与处方外流逻辑仍在，但现金短债比和短期偿债能力仍需重点监测。", "https://data.eastmoney.com/report/603939-pharmacy.html"],
    ["603939", "益丰药房", "2025-09-18", "益丰药房区域整合提升效率", "区域整合和统采提升盈利质量。", "东方证券", "positive", "益丰药房通过区域整合和统采优化提升效率，但门店扩张后的经营现金流波动仍需观察。", "https://data.eastmoney.com/report/603939-efficiency.html"],
    ["603259", "药明康德", "2026-02-06", "CXO 景气边际改善，药明康德全球订单恢复", "全球订单恢复与产能利用率改善。", "中泰证券", "positive", "CXO 行业景气边际改善，药明康德全球订单恢复，政策扰动缓和后基本面有望回归。", "https://data.eastmoney.com/report/603259-cxo.html"],
    ["603259", "药明康德", "2025-11-05", "药明康德需关注外部政策扰动", "海外政策与客户结构变化仍是风险点。", "申万宏源", "negative", "药明康德仍需关注外部政策扰动、客户结构变化和订单转换节奏，这些因素会影响 CXO 景气判断。", "https://data.eastmoney.com/report/603259-policy.html"],
]

SAMPLE_INDUSTRY_REPORTS = [
    ["801150", "医疗器械", "2026-01-28", "医疗器械行业景气修复，AI 医疗带来新增量", "中金公司", "positive", "医疗器械赛道景气修复，AI 医疗、出海和高端设备国产替代成为新一轮增长主线。", "https://data.eastmoney.com/report/industry-device-ai.html"],
    ["801150", "医疗器械", "2025-11-12", "医疗器械行业海外订单与集采博弈并存", "国联证券", "neutral", "医疗器械行业海外订单改善明显，但国内集采和医院采购周期波动仍会影响短期景气判断。", "https://data.eastmoney.com/report/industry-device-risk.html"],
    ["801180", "医疗研发外包", "2026-02-02", "CXO 赛道政策扰动减弱，景气边际回升", "国泰君安", "positive", "CXO 赛道近期政策扰动减弱，景气边际回升，订单恢复与产能利用率改善是核心信号。", "https://data.eastmoney.com/report/industry-cxo-policy.html"],
    ["801140", "化学制药", "2026-01-08", "创新药行业研发投入和商业化继续分化", "广发证券", "positive", "创新药行业仍处于研发投入与商业化并行阶段，具备全球竞争力的品种开始进入收获期。", "https://data.eastmoney.com/report/industry-innovation-drug.html"],
    ["801170", "医疗服务", "2025-12-15", "医疗服务行业扩张提速但现金流约束需关注", "华西证券", "neutral", "医疗服务行业需求韧性较强，但扩张提速后现金流和管理效率仍是关键约束变量。", "https://data.eastmoney.com/report/industry-medical-service.html"],
]

SAMPLE_MACRO_ROWS = [
    ["2025-10", "GDP同比增速", 5.1, "%", "https://www.stats.gov.cn/sj/zxfb/202510/t20251018.html"],
    ["2025-11", "社会消费品零售总额同比", 4.8, "%", "https://www.stats.gov.cn/sj/zxfb/202511/t20251115.html"],
    ["2025-12", "医疗卫生固定资产投资同比", 7.3, "%", "https://www.stats.gov.cn/sj/zxfb/202512/t20251216.html"],
]

SAMPLE_PERIODIC_ROWS = [
    ["SZSE", "300760", "迈瑞医疗", "annual", "年报", 2024, "迈瑞医疗：2024年年度报告", "2025-04-29", "https://disc.static.szse.cn/download/300760_2024_annual.pdf"],
    ["SZSE", "300760", "迈瑞医疗", "q1", "一季报", 2025, "迈瑞医疗：2025年一季报", "2025-04-24", "https://disc.static.szse.cn/download/300760_2025_q1.pdf"],
    ["SZSE", "300760", "迈瑞医疗", "h1", "半年报", 2025, "迈瑞医疗：2025年半年报", "2025-08-28", "https://disc.static.szse.cn/download/300760_2025_h1.pdf"],
    ["SZSE", "300760", "迈瑞医疗", "q3", "三季报", 2025, "迈瑞医疗：2025年三季报", "2025-10-28", "https://disc.static.szse.cn/download/300760_2025_q3.pdf"],
    ["SSE", "688271", "联影医疗", "annual", "年报", 2024, "联影医疗：2024年年度报告", "2025-03-30", "https://query.sse.com.cn/security/stock/queryCompanyBulletin.do?stockCode=688271&year=2024"],
    ["SSE", "688271", "联影医疗", "q1", "一季报", 2025, "联影医疗：2025年一季报", "2025-04-26", "https://query.sse.com.cn/security/stock/queryCompanyBulletin.do?stockCode=688271&period=q1"],
]


def _published_at(year: int) -> str:
    return {2022: "2023-03-28", 2023: "2024-03-29", 2024: "2025-03-30"}[year]


def _financial_url(company_code: str, year: int, exchange: str) -> str:
    if exchange == "SZSE":
        return f"https://disc.static.szse.cn/download/{company_code}_{year}_annual.pdf"
    return f"https://query.sse.com.cn/security/stock/queryCompanyBulletin.do?stockCode={company_code}&year={year}"


def _financial_rows() -> list[dict]:
    rows: list[dict] = []
    for company_code, payload in SAMPLE_COMPANIES.items():
        for year, metrics in payload["metrics"].items():
            rows.append(
                {
                    "company_code": company_code,
                    "company_name": payload["company_name"],
                    "report_year": year,
                    "revenue_million": metrics[0],
                    "net_profit_million": metrics[1],
                    "gross_margin_pct": metrics[2],
                    "net_margin_pct": metrics[3],
                    "rd_ratio_pct": metrics[4],
                    "debt_ratio_pct": metrics[5],
                    "current_ratio": metrics[6],
                    "cash_to_short_debt": metrics[7],
                    "inventory_turnover": metrics[8],
                    "receivable_turnover": metrics[9],
                    "operating_cashflow_million": metrics[10],
                    "roe_pct": metrics[11],
                    "source_url": _financial_url(company_code, year, payload["exchange"]),
                    "published_at": _published_at(year),
                }
            )
    return rows


def _universe_rows() -> list[dict]:
    rows: list[dict] = []
    for company_code, payload in SAMPLE_COMPANIES.items():
        company_reports = [item for item in SAMPLE_RESEARCH_REPORTS if item[0] == company_code]
        positive = sum(1 for item in company_reports if item[6] == "positive")
        negative = sum(1 for item in company_reports if item[6] == "negative")
        rows.append(
            {
                "company_code": company_code,
                "company_name": payload["company_name"],
                "exchange": payload["exchange"],
                "market": "A股",
                "industry_code": payload["industry_name"],
                "industry_name": payload["industry_name"],
                "report_count": len(company_reports),
                "institution_count": len({item[5] for item in company_reports}),
                "positive_count": positive,
                "neutral_count": len(company_reports) - positive - negative,
                "negative_count": negative,
                "latest_report_date": max(item[2] for item in company_reports),
                "earliest_report_date": min(item[2] for item in company_reports),
                "in_target_pool": True,
                "latest_report_title": sorted(company_reports, key=lambda item: item[2], reverse=True)[0][3],
                "latest_source_url": sorted(company_reports, key=lambda item: item[2], reverse=True)[0][8],
            }
        )
    return rows


def _quality_rows() -> list[dict]:
    return [
        {
            "company_code": company_code,
            "company_name": payload["company_name"],
            "report_year": 2024,
            "filled_fields": 12,
            "field_coverage_ratio": 1.0,
            "critical_fields_missing": "",
            "anomaly_flags": "",
        }
        for company_code, payload in SAMPLE_COMPANIES.items()
    ]


def _inventory_rows(base_dir: Path) -> tuple[list[dict], list[dict], list[dict]]:
    report_inventory: list[dict] = []
    sse_manifest: list[dict] = []
    szse_manifest: list[dict] = []
    pdf_root = base_dir / "data" / "raw" / "official"
    for company_code, payload in SAMPLE_COMPANIES.items():
        exchange = payload["exchange"]
        exchange_key = "sse" if exchange == "SSE" else "szse"
        for year in (2022, 2023, 2024):
            pdf_path = pdf_root / exchange_key / "pdfs" / f"{company_code}_{year}_annual_{exchange_key}.pdf"
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            if not pdf_path.exists():
                pdf_path.write_text("sample official report placeholder", encoding="utf-8")
            row = {
                "exchange": exchange,
                "company_code": company_code,
                "disclosure_company_code": company_code,
                "company_name": payload["company_name"],
                "year": year,
                "title": f"{payload['company_name']}：{year}年年度报告",
                "published_at": _published_at(year),
                "source_url": _financial_url(company_code, year, exchange),
                "local_path": str(pdf_path.relative_to(base_dir)).replace("\\", "/"),
                "file_exists": True,
                "size_bytes": 128,
                "status": "downloaded",
                "manifest_path": f"data/raw/official/{exchange_key}/report_manifest.json",
            }
            report_inventory.append(row)
            if exchange == "SSE":
                sse_manifest.append(row)
            elif exchange == "SZSE":
                szse_manifest.append(row)
    return report_inventory, sse_manifest, szse_manifest


def _multimodal_payloads() -> dict[str, dict]:
    return {
        "300760_2024.json": {
            "company_code": "300760",
            "company_name": "迈瑞医疗",
            "report_year": 2024,
            "backend": "modelscope",
            "model_id": "Qwen/Qwen2.5-VL-7B-Instruct",
            "source_url": "https://disc.static.szse.cn/download/300760_2024_annual.pdf",
            "published_at": "2025-04-29",
            "page_images": ["data/cache/official_page_images/300760_2024/page_01.png"],
            "field_sources": {"revenue_million": ["page_01.png"], "net_profit_million": ["page_01.png"]},
            "notes": ["样例多模态抽取结果，仅用于无真实缓存环境下的回归。"],
            "revenue_million": 39500.0,
            "net_profit_million": 12800.0,
            "gross_margin_pct": 67.0,
            "net_margin_pct": 32.4,
            "rd_ratio_pct": 11.8,
            "debt_ratio_pct": 26.0,
            "current_ratio": 2.5,
            "cash_to_short_debt": 4.6,
            "operating_cashflow_million": 13800.0,
            "roe_pct": 31.5,
        },
        "688271_2024.json": {
            "company_code": "688271",
            "company_name": "联影医疗",
            "report_year": 2024,
            "backend": "modelscope",
            "model_id": "Qwen/Qwen2.5-VL-7B-Instruct",
            "source_url": "https://query.sse.com.cn/security/stock/queryCompanyBulletin.do?stockCode=688271&year=2024",
            "published_at": "2025-03-30",
            "page_images": ["data/cache/official_page_images/688271_2024/page_01.png"],
            "field_sources": {"revenue_million": ["page_01.png"]},
            "notes": ["样例多模态抽取结果，仅用于无真实缓存环境下的回归。"],
            "revenue_million": 12600.0,
            "net_profit_million": 2500.0,
            "gross_margin_pct": 50.0,
            "net_margin_pct": 19.8,
            "rd_ratio_pct": 13.6,
            "debt_ratio_pct": 32.0,
            "current_ratio": 2.0,
            "cash_to_short_debt": 2.8,
            "operating_cashflow_million": 2300.0,
            "roe_pct": 17.0,
        },
    }


def _risk_tabular_artifact() -> dict:
    return {
        "model_type": "logistic_regression",
        "trained_at": "2026-03-01T10:00:00",
        "sample_count": 18,
        "positive_samples": 2,
        "feature_columns": MODEL_FEATURE_COLUMNS,
        "coefficients": [0.08, 0.06, -0.03, -0.02, -0.01, 0.12, -0.08, -0.14, -0.01, -0.02, -0.10, -0.04, -0.06, -0.05, -0.03, 0.05, -0.04],
        "intercept": -0.25,
        "imputer_statistics": [0.0] * len(MODEL_FEATURE_COLUMNS),
        "scaler_mean": [0.0] * len(MODEL_FEATURE_COLUMNS),
        "scaler_scale": [1.0] * len(MODEL_FEATURE_COLUMNS),
        "metrics": {
            "accuracy": 0.78,
            "precision": 0.67,
            "recall": 0.50,
            "f1": 0.57,
            "roc_auc": 0.812,
            "positive_rate": 0.11,
        },
    }


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    with path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    path.write_text(content, encoding="utf-8")


def ensure_sample_data(base_dir: Path) -> None:
    data_dir = base_dir / "data"
    processed_dir = data_dir / "processed"
    quality_dir = data_dir / "quality"
    raw_official_dir = data_dir / "raw" / "official"
    cache_dir = data_dir / "cache"
    dataset_dir = data_dir / "datasets"

    financial_rows = _financial_rows()
    inventory_rows, sse_manifest, szse_manifest = _inventory_rows(base_dir)

    _write_csv(processed_dir / "financial_features.csv", FINANCIAL_COLUMNS, financial_rows)
    _write_csv(
        processed_dir / "research_reports.csv",
        RESEARCH_COLUMNS,
        [dict(zip(RESEARCH_COLUMNS, row)) for row in SAMPLE_RESEARCH_REPORTS],
    )
    _write_csv(
        processed_dir / "industry_reports.csv",
        INDUSTRY_COLUMNS,
        [dict(zip(INDUSTRY_COLUMNS, row)) for row in SAMPLE_INDUSTRY_REPORTS],
    )
    _write_csv(processed_dir / "industry_company_universe.csv", UNIVERSE_COLUMNS, _universe_rows())
    _write_csv(processed_dir / "macro_indicators.csv", MACRO_COLUMNS, [dict(zip(MACRO_COLUMNS, row)) for row in SAMPLE_MACRO_ROWS])
    _write_csv(
        processed_dir / "official_periodic_snapshots.csv",
        PERIODIC_COLUMNS,
        [dict(zip(PERIODIC_COLUMNS, row)) for row in SAMPLE_PERIODIC_ROWS],
    )

    _write_csv(quality_dir / "financial_features_official_quality.csv", QUALITY_COLUMNS, _quality_rows())
    _write_json(
        quality_dir / "official_reports_quality.json",
        {
            "target_coverage": {
                "coverage_ratio": 1.0,
                "downloaded_slots": len(inventory_rows),
                "expected_slots": len(inventory_rows),
                "missing_slots": [],
            },
            "exchanges": [
                {"exchange": "SSE", "manifest_exists": True, "rows": len(sse_manifest), "downloaded_rows": len(sse_manifest), "file_missing_rows": 0, "companies": ["600276", "603939", "688271", "603259"]},
                {"exchange": "SZSE", "manifest_exists": True, "rows": len(szse_manifest), "downloaded_rows": len(szse_manifest), "file_missing_rows": 0, "companies": ["300760", "300015"]},
            ],
        },
    )
    _write_json(
        quality_dir / "quality_report.json",
        {
            "financial_features": {"null_ratio": {"net_margin_pct": 0.0, "current_ratio": 0.0, "rd_ratio_pct": 0.0}},
            "research_reports": {"null_ratio": {"content": 0.0, "institution": 0.0}},
            "macro_indicators": {"null_ratio": {"indicator_value": 0.0}},
        },
    )
    _write_json(
        quality_dir / "target_promotion_plan.json",
        {
            "generated_at": "2026-03-01T12:00:00",
            "candidates": [
                {"company_code": "300896", "company_name": "爱美客", "exchange": "SZSE", "industry_name": "医疗消费", "report_count": 8, "institution_count": 4, "latest_report_date": "2026-01-08", "candidate_priority_score": 88.4},
                {"company_code": "002821", "company_name": "凯莱英", "exchange": "SZSE", "industry_name": "医疗服务", "report_count": 7, "institution_count": 3, "latest_report_date": "2025-12-18", "candidate_priority_score": 82.1},
            ],
        },
    )
    _write_json(
        quality_dir / "promoted_official_reports_summary.json",
        {
            "years": [2024, 2023, 2022],
            "downloaded_reports": 0,
            "missing_reports": 6,
        },
    )
    _write_json(
        quality_dir / "compute_pipeline_manifest.json",
        {
            "generated_at": "2026-03-01T12:30:00",
            "current_engine": "python + duckdb",
            "next_engine": "spark-ready batch",
            "warehouse_db": None,
            "parquet_artifact_count": 0,
            "mart_views": ["mart.company_overview", "mart.industry_heat"],
            "jobs": [
                {
                    "job_id": "refresh-official-core",
                    "label": "官方财报核心刷新",
                    "owner": "data-pipeline",
                    "spark_ready": True,
                    "status": "ready",
                }
            ],
        },
    )
    _write_json(
        quality_dir / "warehouse_summary.json",
        {
            "warehouse_db": None,
            "table_count": 0,
            "latest_company_rows": 0,
            "mart_views": [],
            "tables": [],
        },
    )

    _write_csv(
        raw_official_dir / "report_inventory.csv",
        [
            "exchange",
            "company_code",
            "disclosure_company_code",
            "company_name",
            "year",
            "title",
            "published_at",
            "source_url",
            "local_path",
            "file_exists",
            "size_bytes",
            "status",
            "manifest_path",
        ],
        inventory_rows,
    )
    _write_json(raw_official_dir / "sse" / "report_manifest.json", sse_manifest)
    _write_json(raw_official_dir / "szse" / "report_manifest.json", szse_manifest)
    _write_json(raw_official_dir / "bse" / "report_manifest.json", [])

    for file_name, payload in _multimodal_payloads().items():
        _write_json(cache_dir / "official_extract_multimodal" / file_name, payload)

    _write_json(cache_dir / "models" / "risk_tabular_model.json", _risk_tabular_artifact())
    _write_json(
        cache_dir / "models" / "risk_tabular_metadata.json",
        {
            "sample_count": 18,
            "positive_samples": 2,
            "metrics": {"roc_auc": 0.812},
        },
    )
    _write_text(
        dataset_dir / "official_multimodal_sft.jsonl",
        "\n".join(
            [
                json.dumps({"id": "sft-300760-1", "messages": [{"role": "user", "content": "总结迈瑞医疗财报图表"}, {"role": "assistant", "content": "迈瑞医疗营收和净利润保持增长。"}]}, ensure_ascii=False),
                json.dumps({"id": "sft-688271-1", "messages": [{"role": "user", "content": "总结联影医疗风险点"}, {"role": "assistant", "content": "联影医疗需要关注订单兑现节奏。"}]}, ensure_ascii=False),
            ]
        )
        + "\n",
    )
