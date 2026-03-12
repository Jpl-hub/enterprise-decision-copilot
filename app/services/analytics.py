from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.config import settings
from app.data_access import (
    load_financial_features,
    load_industry_reports,
    load_macro_indicators,
    load_multimodal_extracts,
    load_official_periodic_snapshots,
    load_research_reports,
    load_targets,
)


@dataclass(slots=True)
class PipelineStatus:
    has_financials: bool
    has_reports: bool
    has_macro: bool


MULTIMODAL_FIELD_LABELS = {
    "revenue_million": "营收",
    "net_profit_million": "净利润",
    "gross_margin_pct": "毛利率",
    "net_margin_pct": "净利率",
    "rd_total_million": "研发费用",
    "rd_ratio_pct": "研发强度",
    "debt_ratio_pct": "资产负债率",
    "current_assets_million": "流动资产",
    "current_liabilities_million": "流动负债",
    "current_ratio": "流动比率",
    "monetary_funds_million": "货币资金",
    "short_term_debt_million": "短期债务",
    "cash_to_short_debt": "现金短债比",
    "inventory_turnover": "存货周转",
    "receivable_turnover": "应收周转",
    "operating_cashflow_million": "经营现金流",
    "roe_pct": "ROE",
}
MULTIMODAL_PERCENT_FIELDS = {"gross_margin_pct", "net_margin_pct", "rd_ratio_pct", "debt_ratio_pct", "roe_pct"}
MULTIMODAL_PRIORITY_FIELDS = [
    "revenue_million",
    "net_profit_million",
    "net_margin_pct",
    "rd_ratio_pct",
    "debt_ratio_pct",
    "current_ratio",
    "cash_to_short_debt",
    "operating_cashflow_million",
    "roe_pct",
    "gross_margin_pct",
    "inventory_turnover",
    "receivable_turnover",
]
MULTIMODAL_META_FIELDS = {
    "company_code",
    "company_name",
    "report_year",
    "source_url",
    "published_at",
    "page_images",
    "backend",
    "model_id",
    "field_sources",
    "notes",
}
PAGE_REF_LABELS = {
    "page_refs": "财报锚点",
}


def _short_name(name: str) -> str:
    if not isinstance(name, str):
        return ''
    suffixes = ['集团股份有限公司', '股份有限公司', '科技股份有限公司', '科技股份', '有限公司', '集团股份', '集团']
    result = name
    for suffix in suffixes:
        result = result.replace(suffix, '')
    return result.strip()


def _period_sort_key(value: object) -> tuple[int, int]:
    text = str(value)
    parts = text.split("-")
    year = int(parts[0]) if parts and parts[0].isdigit() else 0
    month = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 12
    return year, month


def _numeric_value(value: object) -> float | None:
    if pd.isna(value):
        return None
    return float(value)


def _format_number(value: object, digits: int = 2, suffix: str = "") -> str:
    numeric = _numeric_value(value)
    if numeric is None:
        return "暂无"
    return f"{numeric:.{digits}f}{suffix}"


def _safe_path_text(value: object) -> str:
    return str(value or "").strip().replace("\\", "/")


class AnalyticsService:
    def __init__(self) -> None:
        self.targets = load_targets().copy()
        self.financials = load_financial_features().copy()
        self.reports = load_research_reports().copy()
        self.industry_reports = load_industry_reports().copy()
        self.macro = load_macro_indicators().copy()
        self.official_periodic_snapshots = load_official_periodic_snapshots().copy()
        self.multimodal_extracts = load_multimodal_extracts().copy()

    def _filled_multimodal_fields(self, payload: dict) -> int:
        filled = 0
        for key, value in payload.items():
            if key in MULTIMODAL_META_FIELDS:
                continue
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            if isinstance(value, list) and not value:
                continue
            if isinstance(value, dict) and not value:
                continue
            if pd.isna(value):
                continue
            filled += 1
        return filled

    def _normalize_field_sources(self, value: object) -> dict[str, list[str]]:
        if isinstance(value, dict):
            normalized: dict[str, list[str]] = {}
            for key, item in value.items():
                if isinstance(item, list):
                    refs = [str(ref).strip() for ref in item if str(ref).strip()]
                elif item is None:
                    refs = []
                else:
                    refs = [part.strip() for part in str(item).split(",") if part.strip()]
                if refs:
                    normalized[str(key).strip() or "page_refs"] = refs
            return normalized
        if isinstance(value, list):
            refs = [str(item).strip() for item in value if str(item).strip()]
            return {"page_refs": refs} if refs else {}
        if value is not None:
            refs = [part.strip() for part in str(value).split(",") if part.strip()]
            return {"page_refs": refs} if refs else {}
        return {}

    def _normalize_notes(self, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if value is None:
            return []
        text = str(value).strip()
        return [text] if text else []

    def _format_multimodal_metric(self, field: str, value: object) -> str:
        numeric = _numeric_value(value)
        if numeric is None:
            return "暂无"
        if field in MULTIMODAL_PERCENT_FIELDS:
            return f"{numeric:.2f}%"
        return f"{numeric:,.2f}"

    def _cache_asset_url(self, value: object) -> str | None:
        text = _safe_path_text(value)
        if not text:
            return None
        markers = ("data/cache/", "/data/cache/", "cache/")
        relative = None
        for marker in markers:
            if marker in text:
                relative = text.split(marker, 1)[1]
                break
        if relative is None:
            try:
                candidate = Path(text)
                if not candidate.is_absolute():
                    candidate = settings.data_dir / candidate
                relative = str(candidate.resolve().relative_to(settings.cache_dir.resolve())).replace("\\", "/")
            except Exception:
                return None
        relative = str(relative).replace("\\", "/").lstrip("/")
        return f"/cache-assets/{relative}" if relative else None

    def _multimodal_metric_items(self, payload: dict, limit: int = 6) -> list[dict]:
        items: list[dict] = []
        for field in MULTIMODAL_PRIORITY_FIELDS:
            value = payload.get(field)
            if value is None or pd.isna(value):
                continue
            items.append(
                {
                    "field": field,
                    "label": MULTIMODAL_FIELD_LABELS.get(field, field),
                    "value": _numeric_value(value),
                    "display_value": self._format_multimodal_metric(field, value),
                }
            )
            if len(items) >= limit:
                break
        return items

    def _page_asset_links(self, payload: dict, field_sources: dict[str, list[str]]) -> list[dict]:
        page_images = list(payload.get("page_images") or [])
        image_map: dict[str, str] = {}
        for item in page_images:
            text = _safe_path_text(item)
            if not text:
                continue
            file_name = Path(text).name
            asset_url = self._cache_asset_url(text)
            if file_name and asset_url:
                image_map[file_name] = asset_url

        links: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for key, refs in field_sources.items():
            group_label = PAGE_REF_LABELS.get(key, "图表锚点")
            for ref in refs:
                file_name = Path(_safe_path_text(ref)).name or str(ref)
                url = image_map.get(file_name)
                label = Path(file_name).stem.replace("_", " ").upper() or file_name
                cache_key = (label, url or file_name)
                if cache_key in seen:
                    continue
                seen.add(cache_key)
                links.append(
                    {
                        "label": label,
                        "group": group_label,
                        "url": url,
                    }
                )
        if links:
            return links[:6]

        for item in page_images[:4]:
            text = _safe_path_text(item)
            url = self._cache_asset_url(text)
            if not url:
                continue
            links.append(
                {
                    "label": Path(text).stem.replace("_", " ").upper(),
                    "group": "图表锚点",
                    "url": url,
                }
            )
        return links

    def get_pipeline_status(self) -> PipelineStatus:
        return PipelineStatus(
            has_financials=not self.financials.empty,
            has_reports=not self.reports.empty,
            has_macro=not self.macro.empty,
        )

    def has_ready_data(self) -> bool:
        status = self.get_pipeline_status()
        return status.has_financials and status.has_reports and status.has_macro

    def get_targets(self) -> list[dict]:
        return self.targets.to_dict("records")

    def _segment_to_industry_keywords(self, segment: str) -> list[str]:
        mapping = {
            "创新药": ["化学制药", "生物制品", "中药"],
            "医疗器械": ["医疗器械", "医疗设备", "医疗耗材"],
            "医疗服务": ["医疗服务", "其他医疗服务", "医疗美容"],
            "连锁药房": ["医药商业", "线下药店", "医药流通"],
            "CXO": ["医疗研发外包", "生物制品", "化学制药"],
        }
        return mapping.get(segment, ["医药生物"])

    def _normalize(self, series: pd.Series, reverse: bool = False) -> pd.Series:
        series = pd.to_numeric(series, errors='coerce')
        if series.notna().sum() == 0:
            result = pd.Series([70.0] * len(series), index=series.index)
        else:
            filled = series.fillna(series.median())
            minimum = float(filled.min())
            maximum = float(filled.max())
            if maximum == minimum:
                result = pd.Series([70.0] * len(filled), index=filled.index)
            else:
                result = (filled - minimum) / (maximum - minimum) * 100
        if reverse:
            result = 100 - result
        return result.clip(0, 100)

    def latest_snapshot(self) -> pd.DataFrame:
        if self.financials.empty:
            return self.financials.copy()
        scoped_financials = self.financials.copy()
        if not self.targets.empty:
            target_codes = set(self.targets["company_code"].astype(str).tolist())
            scoped_financials = scoped_financials[
                scoped_financials["company_code"].astype(str).isin(target_codes)
            ].copy()
        if scoped_financials.empty:
            return scoped_financials
        latest_year = int(scoped_financials["report_year"].max())
        snapshot = scoped_financials[scoped_financials["report_year"] == latest_year].copy()

        sentiment = (
            self.reports.groupby("company_code")
            .agg(
                positive_reports=("sentiment", lambda s: int((s == "positive").sum())),
                negative_reports=("sentiment", lambda s: int((s == "negative").sum())),
            )
            .reset_index()
            if not self.reports.empty
            else pd.DataFrame(columns=["company_code", "positive_reports", "negative_reports"])
        )
        snapshot = snapshot.merge(sentiment, on="company_code", how="left").fillna(
            {"positive_reports": 0, "negative_reports": 0}
        )

        snapshot["profitability_score"] = (
            self._normalize(snapshot.get("gross_margin_pct", pd.Series(index=snapshot.index, dtype=float))) * 0.20
            + self._normalize(snapshot.get("net_margin_pct", pd.Series(index=snapshot.index, dtype=float))) * 0.35
            + self._normalize(snapshot.get("roe_pct", pd.Series(index=snapshot.index, dtype=float))) * 0.45
        )
        snapshot["innovation_score"] = (
            self._normalize(snapshot.get("rd_ratio_pct", pd.Series(index=snapshot.index, dtype=float))) * 0.8
            + self._normalize(snapshot["positive_reports"]) * 0.2
        )
        snapshot["resilience_score"] = (
            self._normalize(snapshot.get("current_ratio", pd.Series(index=snapshot.index, dtype=float))) * 0.20
            + self._normalize(snapshot.get("cash_to_short_debt", pd.Series(index=snapshot.index, dtype=float))) * 0.25
            + self._normalize(snapshot.get("debt_ratio_pct", pd.Series(index=snapshot.index, dtype=float)), reverse=True) * 0.20
            + self._normalize(snapshot.get("operating_cashflow_million", pd.Series(index=snapshot.index, dtype=float))) * 0.35
        )
        snapshot["efficiency_score"] = (
            self._normalize(snapshot.get("inventory_turnover", pd.Series(index=snapshot.index, dtype=float))) * 0.45
            + self._normalize(snapshot.get("receivable_turnover", pd.Series(index=snapshot.index, dtype=float))) * 0.55
        )
        snapshot["growth_score"] = (
            self._normalize(snapshot.get("revenue_million", pd.Series(index=snapshot.index, dtype=float))) * 0.55
            + self._normalize(snapshot.get("net_profit_million", pd.Series(index=snapshot.index, dtype=float))) * 0.45
        )

        penalties = []
        flags = []
        for row in snapshot.to_dict("records"):
            penalty = 0
            company_flags = []
            debt_ratio = row.get('debt_ratio_pct')
            cash_short = row.get('cash_to_short_debt')
            op_cf = row.get('operating_cashflow_million')
            current_ratio = row.get('current_ratio')
            if pd.notna(debt_ratio) and debt_ratio > 60:
                penalty += 5
                company_flags.append("资产负债率偏高")
            if pd.notna(cash_short) and cash_short < 1:
                penalty += 5
                company_flags.append("短债覆盖能力不足")
            if pd.notna(op_cf) and op_cf < 0:
                penalty += 6
                company_flags.append("经营现金流为负")
            if pd.notna(current_ratio) and current_ratio < 1.2:
                penalty += 3
                company_flags.append("流动比率偏低")
            if row["negative_reports"] >= 1:
                penalty += 4
                company_flags.append("机构评级偏谨慎")
            penalties.append(penalty)
            flags.append(company_flags)

        snapshot["risk_penalty"] = penalties
        snapshot["risk_flags"] = flags
        snapshot["risk_level"] = snapshot["risk_penalty"].apply(
            lambda x: "高" if x >= 10 else "中" if x >= 4 else "低"
        )
        snapshot["total_score"] = (
            snapshot["profitability_score"] * 0.28
            + snapshot["innovation_score"] * 0.18
            + snapshot["resilience_score"] * 0.18
            + snapshot["efficiency_score"] * 0.12
            + snapshot["growth_score"] * 0.24
            - snapshot["risk_penalty"] * 1.2
        ).clip(0, 100)
        return snapshot.sort_values("total_score", ascending=False).reset_index(drop=True)

    def get_company_record(self, company_code: str) -> dict | None:
        snapshot = self.latest_snapshot()
        row = snapshot[snapshot['company_code'].astype(str) == str(company_code)]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

    def get_company_history(self, company_code: str) -> list[dict]:
        history = self.financials[self.financials["company_code"].astype(str) == str(company_code)].copy()
        if history.empty:
            return []
        history["report_year"] = history["report_year"].astype(int)
        history = history.sort_values("report_year")
        return history.to_dict("records")

    def get_company_trend_digest(self, company_code: str) -> dict:
        history = self.get_company_history(company_code)
        if not history:
            return {
                "years": [],
                "start_year": None,
                "end_year": None,
                "revenue_cagr_pct": 0.0,
                "profit_cagr_pct": 0.0,
                "net_margin_change_pct": 0.0,
                "operating_cashflow_change_million": 0.0,
            }

        years = [int(row["report_year"]) for row in history]
        start = history[0]
        end = history[-1]
        periods = max(len(history) - 1, 1)

        def _cagr(start_value: object, end_value: object) -> float:
            start_num = float(start_value) if pd.notna(start_value) else 0.0
            end_num = float(end_value) if pd.notna(end_value) else 0.0
            if start_num <= 0 or end_num <= 0:
                return 0.0
            return (end_num / start_num) ** (1 / periods) - 1

        return {
            "years": years,
            "start_year": years[0],
            "end_year": years[-1],
            "revenue_cagr_pct": round(_cagr(start.get("revenue_million"), end.get("revenue_million")) * 100, 2),
            "profit_cagr_pct": round(_cagr(start.get("net_profit_million"), end.get("net_profit_million")) * 100, 2),
            "net_margin_change_pct": round(
                float(end.get("net_margin_pct") or 0) - float(start.get("net_margin_pct") or 0), 2
            ),
            "operating_cashflow_change_million": round(
                float(end.get("operating_cashflow_million") or 0) - float(start.get("operating_cashflow_million") or 0), 2
            ),
        }

    def get_company_multimodal_digest(self, company_code: str, report_year: int | None = None) -> dict:
        code = str(company_code)
        if self.multimodal_extracts.empty:
            return {
                "available": False,
                "filled_field_count": 0,
                "summary": "多模态财报锚点待补齐。",
                "metrics": [],
                "page_asset_links": [],
                "notes": [],
            }

        extracts = self.multimodal_extracts[self.multimodal_extracts["company_code"].astype(str) == code].copy()
        if extracts.empty:
            return {
                "available": False,
                "filled_field_count": 0,
                "summary": "当前企业尚未完成多模态财报抽取。",
                "metrics": [],
                "page_asset_links": [],
                "notes": [],
            }
        if report_year is not None:
            scoped = extracts[extracts["report_year"].astype("Int64") == int(report_year)].copy()
            if not scoped.empty:
                extracts = scoped
        extracts["report_year"] = pd.to_numeric(extracts["report_year"], errors="coerce")
        extracts["published_at"] = extracts.get("published_at", pd.Series(index=extracts.index, dtype=object)).astype(str)
        payload = extracts.sort_values(["report_year", "published_at"], ascending=[False, False]).iloc[0].to_dict()
        field_sources = self._normalize_field_sources(payload.get("field_sources"))
        notes = self._normalize_notes(payload.get("notes"))
        metrics = self._multimodal_metric_items(payload)
        page_asset_links = self._page_asset_links(payload, field_sources)
        filled_field_count = self._filled_multimodal_fields(payload)
        summary_parts = [f"多模态抽取识别 {filled_field_count} 项字段"]
        if page_asset_links:
            summary_parts.append("页锚点 " + " / ".join(item["label"] for item in page_asset_links[:3]))
        if metrics:
            summary_parts.append("关键值包括 " + "、".join(f"{item['label']} {item['display_value']}" for item in metrics[:3]))
        return {
            "available": True,
            "company_code": code,
            "company_name": payload.get("company_name"),
            "report_year": int(payload["report_year"]) if pd.notna(payload.get("report_year")) else report_year,
            "published_at": payload.get("published_at"),
            "backend": payload.get("backend"),
            "model_id": payload.get("model_id"),
            "source_url": payload.get("source_url"),
            "filled_field_count": filled_field_count,
            "field_source_count": sum(len(refs) for refs in field_sources.values()),
            "page_asset_links": page_asset_links,
            "page_refs": [item["label"] for item in page_asset_links],
            "notes": notes,
            "metrics": metrics,
            "summary": "；".join(summary_parts) + "。",
        }

    def get_company_research_digest(self, company_code: str) -> dict:
        code = str(company_code)
        reports = self.reports[self.reports["company_code"].astype(str) == code].copy()
        if reports.empty:
            return {"count": 0, "positive": 0, "negative": 0, "latest_titles": []}
        reports["report_date"] = reports["report_date"].astype(str)
        reports = reports.sort_values("report_date", ascending=False)
        return {
            "count": int(len(reports)),
            "positive": int((reports["sentiment"] == "positive").sum()),
            "negative": int((reports["sentiment"] == "negative").sum()),
            "latest_titles": reports["title"].head(3).tolist(),
            "latest_institutions": reports["institution"].head(3).tolist(),
            "latest_rows": reports[["report_date", "title", "institution", "source_url"]].head(5).to_dict("records"),
        }

    def get_company_industry_digest(self, company_code: str) -> dict:
        target = self.targets[self.targets["company_code"].astype(str) == str(company_code)]
        if target.empty or self.industry_reports.empty:
            return {"count": 0, "industries": [], "latest_titles": []}

        segment = str(target.iloc[0]["segment"])
        keywords = self._segment_to_industry_keywords(segment)
        reports = self.industry_reports[
            self.industry_reports["industry_name"].astype(str).apply(
                lambda name: any(keyword in name for keyword in keywords)
            )
        ].copy()
        if reports.empty:
            return {"count": 0, "industries": keywords, "latest_titles": []}

        reports["report_date"] = reports["report_date"].astype(str)
        reports = reports.sort_values("report_date", ascending=False)
        return {
            "count": int(len(reports)),
            "industries": sorted(reports["industry_name"].dropna().astype(str).unique().tolist())[:6],
            "latest_titles": reports["title"].head(3).tolist(),
            "latest_institutions": reports["institution"].head(3).tolist(),
            "latest_rows": reports[["report_date", "industry_name", "title", "institution", "source_url"]].head(5).to_dict("records"),
        }

    def get_macro_digest(self) -> dict:
        if self.macro.empty:
            return {"latest_period": None, "items": []}
        macro = self.macro.copy()
        macro["period"] = macro["period"].astype(str)
        latest_period = sorted(macro["period"].unique().tolist(), key=_period_sort_key)[-1]
        latest = macro[macro["period"] == latest_period].copy()
        items = latest[["indicator_name", "indicator_value", "unit"]].to_dict("records")
        return {"latest_period": latest_period, "items": items}

    def get_industry_overview(self) -> dict:
        if self.industry_reports.empty:
            return {"count": 0, "positive": 0, "negative": 0, "latest_rows": [], "top_industries": []}
        reports = self.industry_reports.copy()
        reports["report_date"] = reports["report_date"].astype(str)
        reports = reports.sort_values("report_date", ascending=False)
        top_industries = (
            reports.groupby("industry_name")
            .size()
            .sort_values(ascending=False)
            .head(6)
            .reset_index(name="report_count")
            .to_dict("records")
        )
        return {
            "count": int(len(reports)),
            "positive": int((reports["sentiment"] == "positive").sum()),
            "negative": int((reports["sentiment"] == "negative").sum()),
            "latest_rows": reports[["report_date", "industry_name", "title", "institution", "source_url"]].head(8).to_dict("records"),
            "top_industries": top_industries,
        }

    def get_data_freshness(self) -> dict:
        target_count = int(self.targets["company_code"].astype(str).nunique()) if not self.targets.empty else 0
        annual_snapshot = self.latest_snapshot()
        annual_report_year = int(annual_snapshot["report_year"].max()) if not annual_snapshot.empty else None
        annual_report_published_at = (
            annual_snapshot["published_at"].astype(str).max()
            if not annual_snapshot.empty and "published_at" in annual_snapshot.columns
            else None
        )
        latest_research_report = self.reports["report_date"].astype(str).max() if not self.reports.empty else None
        latest_industry_report = self.industry_reports["report_date"].astype(str).max() if not self.industry_reports.empty else None
        latest_macro_period = self.macro["period"].astype(str).max() if not self.macro.empty else None

        period_summaries = []
        latest_periodic_rows = self.official_periodic_snapshots.copy()
        if not latest_periodic_rows.empty:
            latest_periodic_rows["report_year"] = pd.to_numeric(latest_periodic_rows["report_year"], errors="coerce")
            latest_periodic_rows["published_at"] = latest_periodic_rows["published_at"].astype(str)
        for period_type, period_label in (
            ("annual", "年报"),
            ("q1", "一季报"),
            ("h1", "半年报"),
            ("q3", "三季报"),
        ):
            scoped = latest_periodic_rows[latest_periodic_rows["period_type"] == period_type].copy() if not latest_periodic_rows.empty else pd.DataFrame()
            covered_companies = int(scoped["company_code"].astype(str).nunique()) if not scoped.empty else 0
            coverage_ratio = round(covered_companies / target_count, 4) if target_count else 0.0
            latest_row = (
                scoped.sort_values(["report_year", "published_at"], ascending=[False, False]).head(1).to_dict("records")[0]
                if not scoped.empty
                else None
            )
            period_summaries.append(
                {
                    "period_type": period_type,
                    "period_label": period_label,
                    "covered_companies": covered_companies,
                    "coverage_ratio": coverage_ratio,
                    "latest_report_year": int(latest_row["report_year"]) if latest_row and pd.notna(latest_row.get("report_year")) else None,
                    "latest_published_at": latest_row.get("published_at") if latest_row else None,
                    "latest_company_name": latest_row.get("company_name") if latest_row else None,
                }
            )

        latest_periodic = (
            latest_periodic_rows.sort_values(["published_at", "report_year"], ascending=[False, False]).head(1).to_dict("records")[0]
            if not latest_periodic_rows.empty
            else None
        )
        return {
            "annual_report_year": annual_report_year,
            "annual_report_published_at": annual_report_published_at,
            "latest_research_report": latest_research_report,
            "latest_industry_report": latest_industry_report,
            "latest_macro_period": latest_macro_period,
            "latest_official_disclosure": latest_periodic.get("published_at") if latest_periodic else annual_report_published_at,
            "latest_periodic_label": latest_periodic.get("period_label") if latest_periodic else None,
            "period_summaries": period_summaries,
        }

    def get_company_report(self, company_code: str) -> dict | None:
        row = self.get_company_record(company_code)
        if row is None:
            return None

        research = self.get_company_research_digest(company_code)
        industry = self.get_company_industry_digest(company_code)
        macro = self.get_macro_digest()
        multimodal = self.get_company_multimodal_digest(company_code, report_year=int(row["report_year"]))

        strengths = []
        risks = list(row.get("risk_flags") or [])

        if pd.notna(row.get("net_margin_pct")) and float(row["net_margin_pct"]) >= 20:
            strengths.append("盈利能力较强")
        if pd.notna(row.get("rd_ratio_pct")) and float(row["rd_ratio_pct"]) >= 10:
            strengths.append("研发投入强度较高")
        if pd.notna(row.get("operating_cashflow_million")) and float(row["operating_cashflow_million"]) > 0:
            strengths.append("经营现金流表现稳健")
        if research.get("positive", 0) >= max(5, research.get("negative", 0) * 3):
            strengths.append("机构观点整体偏积极")
        if not strengths:
            strengths.append("综合经营表现相对平稳")

        if pd.notna(row.get("debt_ratio_pct")) and float(row["debt_ratio_pct"]) >= 55:
            risks.append("资产负债率处于偏高区间")
        if pd.notna(row.get("current_ratio")) and float(row["current_ratio"]) < 1.3:
            risks.append("短期偿债指标仍需关注")
        if research.get("negative", 0) >= 3:
            risks.append("近期存在一定数量偏谨慎研报")
        if not risks:
            risks.append("当前未触发显著财务风险预警")

        operations_summary = (
            f"{row['company_name']} 在 {row['report_year']} 年实现营收 {float(row['revenue_million']):.2f} 百万元，"
            f"净利润 {float(row['net_profit_million']):.2f} 百万元，综合得分 {float(row['total_score']):.1f}。"
        )
        capability_summary = (
            f"净利率 {float(row['net_margin_pct']):.2f}% ，ROE {float(row['roe_pct']):.2f}% ，"
            f"研发强度 {float(row['rd_ratio_pct']):.2f}% ，经营现金流 {float(row['operating_cashflow_million']):.2f} 百万元。"
        )

        macro_summary = "；".join(
            f"{item['indicator_name']}{item['indicator_value']}{item['unit']}"
            for item in macro.get("items", [])[:3]
        ) or "宏观指标待补充。"
        trend = self.get_company_trend_digest(company_code)

        return {
            "company_code": str(company_code),
            "company_name": row["company_name"],
            "report_year": int(row["report_year"]),
            "summary": operations_summary,
            "sections": [
                {"title": "经营概况", "content": operations_summary},
                {
                    "title": "趋势变化",
                    "content": (
                        f"{trend['start_year']}-{trend['end_year']} 年营收 CAGR {trend['revenue_cagr_pct']:.2f}% ，"
                        f"净利润 CAGR {trend['profit_cagr_pct']:.2f}% ，"
                        f"净利率变化 {trend['net_margin_change_pct']:.2f} pct。"
                    ),
                },
                {"title": "能力画像", "content": capability_summary},
                {
                    "title": "机构观点",
                    "content": (
                        f"近两年公开个股研报 {research['count']} 篇，正向 {research['positive']} 篇，"
                        f"负向 {research['negative']} 篇。最新关注主题包括："
                        f"{'；'.join(research.get('latest_titles', [])[:3]) or '暂无'}。"
                    ),
                },
                {
                    "title": "行业环境",
                    "content": (
                        f"匹配行业研报 {industry['count']} 篇，重点行业："
                        f"{'、'.join(industry.get('industries', [])) or '暂无'}。"
                        f"最近行业议题包括：{'；'.join(industry.get('latest_titles', [])[:3]) or '暂无'}。"
                    ),
                },
                {"title": "宏观环境", "content": macro_summary},
                {
                    "title": "财报图表锚点",
                    "content": multimodal.get("summary") or "多模态财报锚点待补齐。",
                },
                {"title": "优势与风险", "content": f"优势：{'；'.join(strengths)}。风险：{'；'.join(risks)}。"},
            ],
            "strengths": strengths,
            "risks": risks,
            "evidence": {
                "financial_source_url": row.get("source_url"),
                "multimodal_digest": multimodal,
                "research_reports": research.get("latest_rows", []),
                "industry_reports": industry.get("latest_rows", []),
                "macro_items": macro.get("items", []),
                "trend_digest": trend,
            },
        }

    def compare_companies(self, company_codes: list[str]) -> dict | None:
        unique_codes = list(dict.fromkeys(str(code) for code in company_codes if str(code).strip()))
        company_rows = []
        periodic_rows = self.official_periodic_snapshots.copy()
        if not periodic_rows.empty:
            periodic_rows["report_year"] = pd.to_numeric(periodic_rows["report_year"], errors="coerce")
            periodic_rows["published_at"] = periodic_rows["published_at"].astype(str)

        def _build_company_freshness(row: dict, research: dict, industry: dict) -> dict:
            code = str(row["company_code"])
            scoped_periodic = (
                periodic_rows[periodic_rows["company_code"].astype(str) == code].copy()
                if not periodic_rows.empty
                else pd.DataFrame()
            )
            latest_periodic = (
                scoped_periodic.sort_values(["published_at", "report_year"], ascending=[False, False]).head(1).to_dict("records")[0]
                if not scoped_periodic.empty
                else None
            )
            latest_stock_rows = research.get("latest_rows", [])
            latest_industry_rows = industry.get("latest_rows", [])
            annual_published_at = str(row.get("published_at")) if pd.notna(row.get("published_at")) else None
            return {
                "annual_report_year": int(row["report_year"]) if pd.notna(row.get("report_year")) else None,
                "annual_report_published_at": annual_published_at,
                "latest_official_disclosure": latest_periodic.get("published_at") if latest_periodic else annual_published_at,
                "latest_periodic_label": latest_periodic.get("period_label") if latest_periodic else ("年报" if annual_published_at else None),
                "latest_stock_report": latest_stock_rows[0].get("report_date") if latest_stock_rows else None,
                "latest_industry_report": latest_industry_rows[0].get("report_date") if latest_industry_rows else None,
            }

        for code in unique_codes:
            row = self.get_company_record(code)
            if row is None:
                continue
            research = self.get_company_research_digest(code)
            industry = self.get_company_industry_digest(code)
            multimodal = self.get_company_multimodal_digest(code, report_year=int(row["report_year"]))
            company_rows.append(
                {
                    "row": row,
                    "trend": self.get_company_trend_digest(code),
                    "research": research,
                    "industry": industry,
                    "multimodal": multimodal,
                    "freshness": _build_company_freshness(row, research, industry),
                }
            )

        if len(company_rows) < 2:
            return None

        company_rows.sort(key=lambda item: float(item["row"].get("total_score") or 0), reverse=True)
        leader = company_rows[0]
        report_year = int(leader["row"]["report_year"])

        def _build_dimension(*, dimension: str, metric_key: str, higher_is_better: bool, conclusion_builder) -> dict:
            ranked = sorted(
                company_rows,
                key=lambda item: float(item["row"].get(metric_key) or 0),
                reverse=higher_is_better,
            )
            winner = ranked[0]
            return {
                "dimension": dimension,
                "winner_company_code": str(winner["row"]["company_code"]),
                "winner_company_name": winner["row"]["company_name"],
                "conclusion": conclusion_builder(winner),
                "values": [
                    {
                        "company_code": str(item["row"]["company_code"]),
                        "company_name": item["row"]["company_name"],
                        "value": round(float(item["row"].get(metric_key) or 0), 2),
                    }
                    for item in ranked
                ],
            }

        dimensions = [
            _build_dimension(
                dimension="综合表现",
                metric_key="total_score",
                higher_is_better=True,
                conclusion_builder=lambda winner: (
                    f"{winner['row']['company_name']} 综合得分 {float(winner['row']['total_score']):.1f}，当前横向表现领先。"
                ),
            ),
            _build_dimension(
                dimension="盈利能力",
                metric_key="profitability_score",
                higher_is_better=True,
                conclusion_builder=lambda winner: (
                    f"{winner['row']['company_name']} 盈利能力得分领先，"
                    f"净利率 {_format_number(winner['row'].get('net_margin_pct'), suffix='%')}，"
                    f"ROE {_format_number(winner['row'].get('roe_pct'), suffix='%')}。"
                ),
            ),
            _build_dimension(
                dimension="成长性",
                metric_key="growth_score",
                higher_is_better=True,
                conclusion_builder=lambda winner: (
                    f"{winner['row']['company_name']} 成长性更强，"
                    f"营收 CAGR {_format_number(winner['trend'].get('revenue_cagr_pct'), suffix='%')}，"
                    f"利润 CAGR {_format_number(winner['trend'].get('profit_cagr_pct'), suffix='%')}。"
                ),
            ),
            _build_dimension(
                dimension="创新投入",
                metric_key="innovation_score",
                higher_is_better=True,
                conclusion_builder=lambda winner: (
                    f"{winner['row']['company_name']} 研发与正向研报表现更突出，"
                    f"研发强度 {_format_number(winner['row'].get('rd_ratio_pct'), suffix='%')}。"
                ),
            ),
            _build_dimension(
                dimension="经营韧性",
                metric_key="resilience_score",
                higher_is_better=True,
                conclusion_builder=lambda winner: (
                    f"{winner['row']['company_name']} 韧性指标领先，"
                    f"流动比率 {_format_number(winner['row'].get('current_ratio'))}，"
                    f"现金短债比 {_format_number(winner['row'].get('cash_to_short_debt'))}。"
                ),
            ),
            _build_dimension(
                dimension="风险水平",
                metric_key="risk_penalty",
                higher_is_better=False,
                conclusion_builder=lambda winner: (
                    f"{winner['row']['company_name']} 风险暴露更低，"
                    f"风险等级 {winner['row']['risk_level']}，"
                    f"风险惩罚 {float(winner['row']['risk_penalty']):.1f}。"
                ),
            ),
        ]

        comparison_rows = []
        evidence_rows = []
        freshness_rows = []
        for item in company_rows:
            row = item["row"]
            trend = item["trend"]
            research = item["research"]
            industry = item["industry"]
            multimodal = item["multimodal"]
            freshness = item["freshness"]
            comparison_rows.append(
                {
                    "company_code": str(row["company_code"]),
                    "company_name": row["company_name"],
                    "total_score": round(float(row["total_score"]), 2),
                    "risk_level": row["risk_level"],
                    "revenue_million": round(float(row["revenue_million"]), 2),
                    "net_profit_million": round(float(row["net_profit_million"]), 2),
                    "net_margin_pct": _numeric_value(row.get("net_margin_pct")),
                    "roe_pct": _numeric_value(row.get("roe_pct")),
                    "rd_ratio_pct": _numeric_value(row.get("rd_ratio_pct")),
                    "revenue_cagr_pct": _numeric_value(trend.get("revenue_cagr_pct")),
                    "profit_cagr_pct": _numeric_value(trend.get("profit_cagr_pct")),
                    "research_report_count": int(research.get("count", 0)),
                    "industry_report_count": int(industry.get("count", 0)),
                    "multimodal_field_count": int(multimodal.get("filled_field_count", 0)),
                }
            )
            evidence_rows.append(
                {
                    "company_code": str(row["company_code"]),
                    "company_name": row["company_name"],
                    "financial_source_url": row.get("source_url"),
                    "financial_published_at": freshness.get("annual_report_published_at"),
                    "trend_digest": trend,
                    "research_digest": research,
                    "industry_digest": industry,
                    "multimodal_digest": multimodal,
                    "risk_flags": row.get("risk_flags", []),
                    "freshness_digest": freshness,
                }
            )
            freshness_rows.append(freshness)

        latest_freshness = max(
            freshness_rows,
            key=lambda item: (
                str(item.get("latest_official_disclosure") or ""),
                str(item.get("latest_periodic_label") or ""),
            ),
            default=None,
        )
        freshness_summary = {
            "annual_report_year": report_year,
            "latest_official_disclosure": latest_freshness.get("latest_official_disclosure") if latest_freshness else None,
            "latest_periodic_label": latest_freshness.get("latest_periodic_label") if latest_freshness else None,
            "latest_stock_report": max((str(item.get("latest_stock_report") or "") for item in freshness_rows), default="") or None,
            "latest_industry_report": max((str(item.get("latest_industry_report") or "") for item in freshness_rows), default="") or None,
        }

        profit_dimension = next(item for item in dimensions if item["dimension"] == "盈利能力")
        growth_dimension = next(item for item in dimensions if item["dimension"] == "成长性")
        risk_dimension = next(item for item in dimensions if item["dimension"] == "风险水平")

        highlights = [
            (
                f"综合领先：{leader['row']['company_name']} 总分 {float(leader['row']['total_score']):.1f}，"
                f"在 {report_year} 年样本中横向表现更强。"
            ),
            profit_dimension["conclusion"],
            growth_dimension["conclusion"],
            risk_dimension["conclusion"],
        ]
        if leader["row"].get("risk_flags"):
            highlights.append(f"{leader['row']['company_name']} 仍需关注：{'；'.join(leader['row']['risk_flags'])}。")
        if leader["multimodal"].get("available"):
            highlights.append(
                f"财报图表锚点：{leader['row']['company_name']}{leader['multimodal'].get('summary')}"
            )

        summary = (
            f"基于 {report_year} 年真实披露数据与多年度趋势，{leader['row']['company_name']} 当前综合表现领先；"
            f"盈利优势体现在 {profit_dimension['winner_company_name']}，"
            f"成长弹性则由 {growth_dimension['winner_company_name']} 更突出。"
        )

        return {
            "report_year": report_year,
            "winner_company_code": str(leader["row"]["company_code"]),
            "winner_company_name": leader["row"]["company_name"],
            "summary": summary,
            "highlights": highlights,
            "comparison_rows": comparison_rows,
            "dimensions": dimensions,
            "evidence": {"companies": evidence_rows, "freshness": freshness_summary},
        }

    def get_dashboard_payload(self) -> dict:
        status = self.get_pipeline_status()
        if self.financials.empty:
            return {
                "status": status,
                "targets": self.get_targets(),
                "metrics": None,
                "freshness": self.get_data_freshness(),
                "ranking": [],
                "watchlist": [],
                "macro": [],
            }
        snapshot = self.latest_snapshot()
        leader = snapshot.iloc[0]
        metrics = {
            "sample_count": int(snapshot["company_code"].nunique()),
            "latest_year": int(snapshot["report_year"].max()),
            "avg_score": round(float(snapshot["total_score"].mean()), 1),
            "leader_name": leader["company_name"],
            "leader_score": round(float(leader["total_score"]), 1),
            "research_report_count": int(len(self.reports)),
            "industry_report_count": int(len(self.industry_reports)),
        }
        ranking = snapshot[["company_code", "company_name", "total_score", "risk_level"]].head(8)
        watchlist = snapshot.sort_values(["risk_penalty", "total_score"], ascending=[False, True]).head(5)
        macro = [] if self.macro.empty else self.macro.to_dict('records')
        return {
            "status": status,
            "targets": self.get_targets(),
            "metrics": metrics,
            "freshness": self.get_data_freshness(),
            "ranking": ranking.to_dict("records"),
            "watchlist": watchlist[["company_code", "company_name", "risk_level", "risk_flags"]].to_dict("records"),
            "macro": macro,
        }

    def find_company_matches(self, text: str) -> list[dict]:
        matches = []
        target_rows = self.targets[["company_code", "company_name"]].drop_duplicates().to_dict("records")
        seen = set()
        for row in target_rows:
            code = str(row['company_code'])
            target_name = str(row['company_name'])
            short_name = _short_name(target_name)
            if (
                code in text
                or target_name in text
                or short_name in text
                or text in target_name
                or (short_name and text in short_name)
            ):
                if code not in seen:
                    seen.add(code)
                    full = self.get_company_record(code)
                    company_name = full['company_name'] if full else target_name
                    matches.append({'company_code': code, 'company_name': company_name, 'short_name': short_name})
        return matches

