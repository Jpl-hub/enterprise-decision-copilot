from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from math import log2

import pandas as pd

from app.config import settings
from app.data_access import load_targets
from app.services.analytics import AnalyticsService
from app.services.retrieval import RetrievalService


@dataclass(slots=True)
class ReviewRecord:
    company_code: str
    report_year: int
    finding_level: str
    finding_type: str
    note: str
    status: str
    created_at: str

    def as_dict(self) -> dict:
        return {
            "company_code": self.company_code,
            "report_year": self.report_year,
            "finding_level": self.finding_level,
            "finding_type": self.finding_type,
            "note": self.note,
            "status": self.status,
            "created_at": self.created_at,
        }


class DataQualityService:
    def __init__(
        self,
        official_quality_path: Path | None = None,
        inventory_quality_path: Path | None = None,
        inventory_path: Path | None = None,
        review_queue_path: Path | None = None,
        multimodal_extract_dir: Path | None = None,
    ) -> None:
        quality_dir = settings.data_dir / "quality"
        raw_official_dir = settings.raw_dir / "official"
        review_dir = settings.data_dir / "review"
        self.official_quality_path = official_quality_path or (quality_dir / "financial_features_official_quality.csv")
        self.inventory_quality_path = inventory_quality_path or (quality_dir / "official_reports_quality.json")
        self.inventory_path = inventory_path or (raw_official_dir / "report_inventory.csv")
        self.review_queue_path = review_queue_path or (review_dir / "manual_review_queue.csv")
        self.multimodal_extract_dir = multimodal_extract_dir or (settings.cache_dir / "official_extract_multimodal")
        self.retrieval_eval_cases_path = settings.data_dir / "evals" / "retrieval_eval_cases.json"
        self.review_queue_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_csv(self, path: Path, dtype: dict[str, str] | None = None) -> pd.DataFrame:
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(path, dtype=dtype)

    def _read_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _read_json_list(self, path: Path) -> list[dict]:
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, list) else []

    def _load_source_registry_frame(self) -> pd.DataFrame:
        candidates = [
            settings.processed_dir / "source_registry.csv",
            settings.data_dir / "lake" / "silver" / "source_registry" / "part-0000.csv",
            settings.data_dir / "lake" / "bronze" / "source_registry" / "part-0000.csv",
        ]
        for path in candidates:
            if path.exists():
                return self._read_csv(path)
        return pd.DataFrame()

    def _latest_text(self, series: pd.Series) -> str | None:
        values = [str(item).strip() for item in series.dropna().tolist() if str(item).strip()]
        return max(values) if values else None

    def _split_csv_field(self, value: object) -> list[str]:
        if value is None or pd.isna(value):
            return []
        return [item for item in str(value).split(",") if item and item.lower() != "nan"]

    def _pending_key(self, row: dict) -> tuple[str, int, str]:
        return (
            str(row.get("company_code") or ""),
            int(row.get("report_year") or 0),
            str(row.get("finding_type") or "").strip(),
        )

    def _append_review_records(self, records: list[ReviewRecord]) -> None:
        if not records:
            return
        write_header = not self.review_queue_path.exists() or self.review_queue_path.stat().st_size == 0
        with self.review_queue_path.open("a", encoding="utf-8-sig", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(records[0].as_dict().keys()))
            if write_header:
                writer.writeheader()
            for record in records:
                writer.writerow(record.as_dict())

    def _safe_int(self, value: object, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _promotion_manifest_path(self, exchange: str) -> Path:
        exchange_key = str(exchange or "").strip().upper()
        if exchange_key == "SSE":
            return settings.raw_dir / "official" / "sse" / "report_manifest.json"
        if exchange_key == "SZSE":
            return settings.raw_dir / "official" / "szse" / "report_manifest.json"
        if exchange_key == "BSE":
            return settings.raw_dir / "official" / "bse" / "report_manifest.json"
        return Path()

    def _load_promotion_manifest_index(self, exchange: str) -> dict[tuple[str, int], dict]:
        rows = self._read_json_list(self._promotion_manifest_path(exchange))
        indexed: dict[tuple[str, int], dict] = {}
        for item in rows:
            code = str(item.get("company_code") or item.get("query_company_code") or "").strip()
            year = self._safe_int(item.get("year"), 0)
            if not code or year <= 0:
                continue
            indexed[(code, year)] = item
        return indexed

    def _filled_multimodal_fields(self, payload: dict) -> int:
        ignored = {
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
        filled = 0
        for key, value in payload.items():
            if key in ignored:
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

    def _normalize_multimodal_notes(self, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if value is None:
            return []
        text = str(value).strip()
        return [text] if text else []

    def _normalize_multimodal_field_sources(self, value: object) -> dict[str, list[str]]:
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
            return {"page_refs": refs}
        if value is not None:
            refs = [part.strip() for part in str(value).split(",") if part.strip()]
            if refs:
                return {"page_refs": refs}
        return {}

    def _load_multimodal_extracts(self) -> list[dict]:
        if not self.multimodal_extract_dir.exists():
            return []
        records: list[dict] = []
        for path in sorted(self.multimodal_extract_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            company_code = str(payload.get("company_code") or "").strip()
            report_year = self._safe_int(payload.get("report_year"), 0)
            if not company_code or report_year <= 0:
                continue
            records.append(
                {
                    "company_code": company_code,
                    "report_year": report_year,
                    "company_name": str(payload.get("company_name") or "").strip() or None,
                    "backend": str(payload.get("backend") or "").strip() or "unknown",
                    "model_id": str(payload.get("model_id") or "").strip() or None,
                    "source_url": str(payload.get("source_url") or "").strip() or None,
                    "page_images": list(payload.get("page_images") or []),
                    "field_source_count": len(self._normalize_multimodal_field_sources(payload.get("field_sources"))),
                    "filled_field_count": self._filled_multimodal_fields(payload),
                    "notes": self._normalize_multimodal_notes(payload.get("notes")),
                }
            )
        return records

    def _read_retrieval_eval_cases(self) -> list[dict]:
        if not self.retrieval_eval_cases_path.exists():
            return []
        try:
            payload = json.loads(self.retrieval_eval_cases_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        return payload if isinstance(payload, list) else []

    def _row_matches_keywords(self, row: dict, keywords: list[str]) -> bool:
        haystack = " ".join(
            str(row.get(key) or "")
            for key in ("title", "matched_excerpt", "institution", "industry_name", "source_url")
        )
        return any(keyword and keyword in haystack for keyword in keywords)

    def _dcg_at_k(self, relevances: list[int], k: int) -> float:
        score = 0.0
        for idx, rel in enumerate(relevances[:k], start=1):
            if rel <= 0:
                continue
            score += rel / log2(idx + 1)
        return score

    def get_retrieval_evaluation_summary(self) -> dict:
        cases = self._read_retrieval_eval_cases()
        if not cases:
            return {
                "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "case_count": 0,
                "hit_at_3": 0.0,
                "hit_at_5": 0.0,
                "mrr": 0.0,
                "ndcg_at_5": 0.0,
                "retrieval_mode": "hybrid_tfidf_rerank",
                "strategy_labels": ["char_tfidf", "word_tfidf", "entity_expansion", "keyword_overlap", "recency_rerank"],
                "cases": [],
            }

        analytics = AnalyticsService()
        retrieval = RetrievalService(analytics)
        case_results: list[dict] = []
        hit3_total = 0
        hit5_total = 0
        rr_total = 0.0
        ndcg_total = 0.0
        retrieval_mode = None
        strategy_labels: list[str] = []

        for raw_case in cases:
            case_id = str(raw_case.get("case_id") or "").strip()
            scope = str(raw_case.get("scope") or "company").strip()
            query = str(raw_case.get("query") or "").strip()
            target_code = str(raw_case.get("company_code") or "").strip() or None
            relevant_keywords = [str(item).strip() for item in list(raw_case.get("relevant_keywords") or []) if str(item).strip()]
            if not case_id or not query or not relevant_keywords:
                continue

            if scope == "company" and target_code:
                result = retrieval.retrieve_company_evidence(target_code, query, limit=5)
                rows = list(result.get("stock_reports") or []) + list(result.get("industry_reports") or [])
            else:
                result = retrieval.retrieve_industry_evidence(query, limit=5)
                rows = list(result.get("industry_reports") or [])

            if retrieval_mode is None:
                profile = result.get("query_profile") or {}
                retrieval_mode = str(profile.get("retrieval_mode") or "hybrid_tfidf_rerank")
                strategy_labels = [str(item) for item in list(profile.get("strategy_labels") or []) if str(item)]

            relevances = [1 if self._row_matches_keywords(row, relevant_keywords) else 0 for row in rows]
            hit_at_3 = any(relevances[:3])
            hit_at_5 = any(relevances[:5])
            reciprocal_rank = 0.0
            for idx, rel in enumerate(relevances, start=1):
                if rel:
                    reciprocal_rank = 1.0 / idx
                    break
            dcg = self._dcg_at_k(relevances, 5)
            ideal_rels = sorted(relevances, reverse=True)
            idcg = self._dcg_at_k(ideal_rels, 5) or 1.0
            ndcg = dcg / idcg

            hit3_total += int(hit_at_3)
            hit5_total += int(hit_at_5)
            rr_total += reciprocal_rank
            ndcg_total += ndcg
            case_results.append(
                {
                    "case_id": case_id,
                    "scope": scope,
                    "query": query,
                    "target_code": target_code,
                    "relevant_keywords": relevant_keywords,
                    "hit_at_3": hit_at_3,
                    "hit_at_5": hit_at_5,
                    "reciprocal_rank": round(reciprocal_rank, 4),
                    "ndcg_at_5": round(ndcg, 4),
                    "top_titles": [str(row.get("title") or "未命名证据").strip() for row in rows[:5]],
                    "matched_titles": [
                        str(row.get("title") or "未命名证据").strip()
                        for row, rel in zip(rows[:5], relevances[:5], strict=False)
                        if rel
                    ],
                }
            )

        case_count = len(case_results)
        if case_count == 0:
            return {
                "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "case_count": 0,
                "hit_at_3": 0.0,
                "hit_at_5": 0.0,
                "mrr": 0.0,
                "ndcg_at_5": 0.0,
                "retrieval_mode": retrieval_mode or "hybrid_tfidf_rerank",
                "strategy_labels": strategy_labels,
                "cases": [],
            }

        return {
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "case_count": case_count,
            "hit_at_3": round(hit3_total / case_count, 4),
            "hit_at_5": round(hit5_total / case_count, 4),
            "mrr": round(rr_total / case_count, 4),
            "ndcg_at_5": round(ndcg_total / case_count, 4),
            "retrieval_mode": retrieval_mode or "hybrid_tfidf_rerank",
            "strategy_labels": strategy_labels,
            "cases": case_results,
        }

    def get_multimodal_extract_summary(self) -> dict:
        extracts = self._load_multimodal_extracts()
        inventory = self._read_csv(self.inventory_path, dtype={"company_code": str, "disclosure_company_code": str})
        downloaded = (
            inventory[(inventory["status"] == "downloaded") & (inventory["file_exists"] == True)]
            if not inventory.empty
            else pd.DataFrame()
        )
        expected_reports = int(len(downloaded))
        coverage_ratio = round(len(extracts) / expected_reports, 4) if expected_reports else 0.0
        backends = sorted({str(item.get("backend") or "unknown") for item in extracts})
        avg_filled = round(
            sum(int(item.get("filled_field_count") or 0) for item in extracts) / len(extracts),
            2,
        ) if extracts else 0.0
        return {
            "report_count": len(extracts),
            "expected_report_count": expected_reports,
            "coverage_ratio": coverage_ratio,
            "avg_filled_field_count": avg_filled,
            "backends": backends,
            "recent_extracts": sorted(
                extracts,
                key=lambda item: (item["report_year"], item["company_code"]),
                reverse=True,
            )[:8],
        }

    def get_review_queue(self) -> list[dict]:
        queue = self._read_csv(self.review_queue_path, dtype={"company_code": str})
        if queue.empty:
            return []
        queue["report_year"] = queue["report_year"].astype(int)
        queue = queue.sort_values(["status", "created_at"], ascending=[True, False])
        return queue.to_dict("records")

    def get_financial_anomalies(self, limit: int = 12) -> list[dict]:
        quality = self._read_csv(self.official_quality_path, dtype={"company_code": str})
        inventory = self._read_csv(self.inventory_path, dtype={"company_code": str, "disclosure_company_code": str})
        if quality.empty:
            return []

        def _score(row: pd.Series) -> int:
            missing = len(self._split_csv_field(row.get("critical_fields_missing")))
            flags = len(self._split_csv_field(row.get("anomaly_flags")))
            return missing * 3 + flags

        quality = quality.copy()
        quality["anomaly_score"] = quality.apply(_score, axis=1)
        quality = quality[(quality["anomaly_score"] > 0) | (quality["field_coverage_ratio"].fillna(0) < 0.85)]
        if not inventory.empty:
            merged = inventory[["company_code", "year", "exchange", "source_url"]].copy()
            merged = merged.rename(columns={"year": "report_year", "source_url": "financial_source_url"})
            quality = quality.merge(merged, on=["company_code", "report_year"], how="left")
        quality = quality.sort_values(["anomaly_score", "field_coverage_ratio"], ascending=[False, True]).head(limit)
        records = []
        for row in quality.to_dict("records"):
            records.append(
                {
                    "company_code": str(row["company_code"]),
                    "company_name": row["company_name"],
                    "report_year": int(row["report_year"]),
                    "field_coverage_ratio": round(float(row.get("field_coverage_ratio") or 0), 4),
                    "critical_fields_missing": self._split_csv_field(row.get("critical_fields_missing")),
                    "anomaly_flags": self._split_csv_field(row.get("anomaly_flags")),
                    "anomaly_score": int(row.get("anomaly_score") or 0),
                    "exchange": row.get("exchange"),
                    "financial_source_url": row.get("financial_source_url"),
                }
            )
        return records

    def get_company_quality_snapshot(self, company_code: str) -> dict:
        code = str(company_code)
        summary = self.get_quality_summary()
        anomalies = [
            item
            for item in self.get_financial_anomalies(limit=50)
            if str(item.get("company_code") or "") == code
        ]
        queue = [
            item
            for item in self.get_review_queue()
            if str(item.get("company_code") or "") == code
        ]
        multimodal_extracts = [
            item
            for item in self._load_multimodal_extracts()
            if str(item.get("company_code") or "") == code
        ]
        return {
            "official_report_coverage_ratio": summary.get("official_report_coverage_ratio", 0.0),
            "pending_review_count": summary.get("pending_review_count", 0),
            "company_anomalies": anomalies[:5],
            "company_review_queue": queue[:5],
            "multimodal_extract_count": len(multimodal_extracts),
            "multimodal_extracts": multimodal_extracts[:5],
        }

    def build_auto_review_candidates(self, limit: int = 20) -> list[dict]:
        candidates: list[dict] = []
        anomalies = self.get_financial_anomalies(limit=max(limit, 30))
        for item in anomalies:
            critical_missing = item.get("critical_fields_missing") or []
            anomaly_flags = item.get("anomaly_flags") or []
            note_parts = [
                f"{item['company_name']}{item['report_year']} 年字段覆盖率 {float(item.get('field_coverage_ratio') or 0) * 100:.1f}%",
            ]
            if critical_missing:
                note_parts.append(f"关键字段缺失：{'、'.join(critical_missing[:6])}")
            if anomaly_flags:
                note_parts.append(f"异常标记：{'、'.join(anomaly_flags[:4])}")
            if item.get("financial_source_url"):
                note_parts.append(f"来源：{item['financial_source_url']}")
            level = "high" if int(item.get("anomaly_score") or 0) >= 8 else "medium"
            candidates.append(
                {
                    "company_code": str(item["company_code"]),
                    "report_year": int(item["report_year"]),
                    "finding_level": level,
                    "finding_type": "官方财报字段异常复核",
                    "note": "；".join(note_parts),
                    "_priority": 2 if level == "high" else 1,
                }
            )

        inventory_quality = self._read_json(self.inventory_quality_path)
        missing_slots = inventory_quality.get("target_coverage", {}).get("missing_slots", [])
        for item in missing_slots:
            company_code = str(item.get("company_code") or "")
            report_year = int(item.get("year") or 0)
            if not company_code or report_year <= 0:
                continue
            company_name = str(item.get("company_name") or company_code)
            exchange = str(item.get("exchange") or "未知交易所")
            candidates.append(
                {
                    "company_code": company_code,
                    "report_year": report_year,
                    "finding_level": "high",
                    "finding_type": "官方财报缺失补采",
                    "note": f"{company_name}{report_year} 年官方财报在 {exchange} 交易所清单中缺失，需补采并校验入湖。",
                    "_priority": 3,
                }
            )

        multimodal_extracts = self._load_multimodal_extracts()
        multimodal_keys = {(item["company_code"], item["report_year"]): item for item in multimodal_extracts}
        inventory = self._read_csv(self.inventory_path, dtype={"company_code": str, "disclosure_company_code": str})
        if not inventory.empty:
            downloaded = inventory[(inventory["status"] == "downloaded") & (inventory["file_exists"] == True)].copy()
            for row in downloaded.to_dict("records"):
                key = (str(row.get("company_code") or ""), self._safe_int(row.get("year"), 0))
                if not key[0] or key[1] <= 0:
                    continue
                extract = multimodal_keys.get(key)
                if extract is None:
                    candidates.append(
                        {
                            "company_code": key[0],
                            "report_year": key[1],
                            "finding_level": "medium",
                            "finding_type": "多模态抽取缺失复核",
                            "note": f"{row.get('company_name') or key[0]}{key[1]} 年已下载官方财报，但尚未生成多模态抽取结果。",
                            "_priority": 2,
                        }
                    )
                    continue
                if int(extract.get("filled_field_count") or 0) < 6:
                    candidates.append(
                        {
                            "company_code": key[0],
                            "report_year": key[1],
                            "finding_level": "medium",
                            "finding_type": "多模态抽取低覆盖复核",
                            "note": (
                                f"{row.get('company_name') or key[0]}{key[1]} 年多模态抽取字段数偏低，"
                                f"当前仅识别 {int(extract.get('filled_field_count') or 0)} 个字段，"
                                f"后端 {extract.get('backend') or 'unknown'}。"
                            ),
                            "_priority": 1,
                        }
                    )

        candidates = sorted(candidates, key=lambda item: item["_priority"], reverse=True)
        deduped: list[dict] = []
        seen: set[tuple[str, int, str]] = set()
        for item in candidates:
            key = (item["company_code"], item["report_year"], item["finding_type"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append({k: v for k, v in item.items() if k != "_priority"})
            if len(deduped) >= limit:
                break
        return deduped

    def sync_auto_review_queue(self, limit: int = 12) -> dict:
        limit = max(1, min(int(limit), 100))
        candidates = self.build_auto_review_candidates(limit=max(limit * 2, 20))
        queue = self.get_review_queue()
        pending_keys = {
            self._pending_key(row)
            for row in queue
            if str(row.get("status") or "pending").strip().lower() == "pending"
        }

        created_records: list[ReviewRecord] = []
        skipped_count = 0
        now = datetime.now().isoformat(timespec="seconds")
        for item in candidates:
            key = (item["company_code"], int(item["report_year"]), item["finding_type"])
            if key in pending_keys:
                skipped_count += 1
                continue
            record = ReviewRecord(
                company_code=item["company_code"],
                report_year=int(item["report_year"]),
                finding_level=item["finding_level"],
                finding_type=item["finding_type"],
                note=item["note"],
                status="pending",
                created_at=now,
            )
            created_records.append(record)
            pending_keys.add(key)
            if len(created_records) >= limit:
                break

        self._append_review_records(created_records)
        return {
            "created_count": len(created_records),
            "skipped_count": skipped_count,
            "created": [record.as_dict() for record in created_records],
        }

    def _compute_issue_breakdown(self) -> dict[str, int]:
        inventory_quality = self._read_json(self.inventory_quality_path)
        coverage = inventory_quality.get("target_coverage", {})
        anomalies = self.get_financial_anomalies(limit=500)
        inventory = self._read_csv(self.inventory_path, dtype={"company_code": str, "disclosure_company_code": str})
        multimodal_extracts = self._load_multimodal_extracts()
        multimodal_keys = {(item["company_code"], item["report_year"]): item for item in multimodal_extracts}
        multimodal_missing = 0
        multimodal_low_coverage = 0
        if not inventory.empty:
            downloaded = inventory[(inventory["status"] == "downloaded") & (inventory["file_exists"] == True)].copy()
            for row in downloaded.to_dict("records"):
                key = (str(row.get("company_code") or ""), self._safe_int(row.get("year"), 0))
                if not key[0] or key[1] <= 0:
                    continue
                extract = multimodal_keys.get(key)
                if extract is None:
                    multimodal_missing += 1
                    continue
                if int(extract.get("filled_field_count") or 0) < 6:
                    multimodal_low_coverage += 1
        return {
            "missing_reports": int(len(coverage.get("missing_slots") or [])),
            "field_gaps": int(len(anomalies)),
            "multimodal_missing": int(multimodal_missing),
            "multimodal_low_coverage": int(multimodal_low_coverage),
        }

    def get_quality_summary(self) -> dict:
        inventory_quality = self._read_json(self.inventory_quality_path)
        multimodal_summary = self.get_multimodal_extract_summary()
        queue = self.get_review_queue()
        anomalies = self.get_financial_anomalies(limit=8)
        pending_reviews = [item for item in queue if str(item.get("status") or "pending") == "pending"]
        coverage = inventory_quality.get("target_coverage", {})
        exchange_status = inventory_quality.get("exchanges", [])
        universe_expected = int(sum(int(item.get("rows") or 0) for item in exchange_status))
        universe_downloaded = int(sum(int(item.get("downloaded_rows") or 0) for item in exchange_status))
        issue_breakdown = self._compute_issue_breakdown()
        target_pool = load_targets()
        return {
            "official_report_coverage_ratio": round(float(coverage.get("coverage_ratio") or 0), 4),
            "official_report_downloaded_slots": int(coverage.get("downloaded_slots") or 0),
            "official_report_expected_slots": int(coverage.get("expected_slots") or 0),
            "missing_report_slots": int(len(coverage.get("missing_slots") or [])),
            "target_pool_company_count": int(len(target_pool)),
            "target_pool_ready": bool(float(coverage.get("coverage_ratio") or 0) >= 0.95),
            "universe_report_downloaded_slots": universe_downloaded,
            "universe_report_expected_slots": universe_expected,
            "universe_report_coverage_ratio": round(universe_downloaded / universe_expected, 4) if universe_expected else 0.0,
            "pending_review_count": int(len(pending_reviews)),
            "anomaly_company_count": int(len(anomalies)),
            "issue_breakdown": issue_breakdown,
            "exchange_status": exchange_status,
            "top_anomalies": anomalies,
            "recent_reviews": queue[:8],
            "multimodal_extract_report_count": int(multimodal_summary.get("report_count", 0)),
            "multimodal_expected_report_count": int(multimodal_summary.get("expected_report_count", 0)),
            "multimodal_extract_coverage_ratio": float(multimodal_summary.get("coverage_ratio", 0.0)),
            "multimodal_avg_filled_field_count": float(multimodal_summary.get("avg_filled_field_count", 0.0)),
            "multimodal_backends": list(multimodal_summary.get("backends", [])),
            "multimodal_recent_extracts": list(multimodal_summary.get("recent_extracts", [])),
        }

    def get_foundation_summary(self) -> dict:
        quality_dir = settings.data_dir / "quality"
        quality_report = self._read_json(quality_dir / "quality_report.json")
        warehouse_summary = self._read_json(quality_dir / "warehouse_summary.json")
        multimodal_summary = self.get_multimodal_extract_summary()

        warehouse_tables = list(warehouse_summary.get("tables", []))
        layer_map: dict[str, dict[str, int | str]] = {}
        total_rows = 0
        for item in warehouse_tables:
            layer = str(item.get("schema_name") or "unknown")
            rows = self._safe_int(item.get("rows"), 0)
            total_rows += rows
            bucket = layer_map.setdefault(layer, {"layer": layer, "table_count": 0, "row_count": 0})
            bucket["table_count"] = self._safe_int(bucket.get("table_count"), 0) + 1
            bucket["row_count"] = self._safe_int(bucket.get("row_count"), 0) + rows

        dataset_profiles: list[dict] = []
        top_null_fields: list[dict] = []
        for key, payload in quality_report.items():
            if not isinstance(payload, dict) or "rows" not in payload:
                continue
            table_name = str(payload.get("table") or key)
            null_ratio = payload.get("null_ratio") or {}
            hotspots = []
            for field, ratio in null_ratio.items():
                try:
                    numeric_ratio = float(ratio)
                except (TypeError, ValueError):
                    continue
                if numeric_ratio <= 0:
                    continue
                hotspots.append(
                    {
                        "table": table_name,
                        "field": str(field),
                        "null_ratio": round(numeric_ratio, 4),
                    }
                )
            hotspots = sorted(hotspots, key=lambda item: item["null_ratio"], reverse=True)
            if hotspots:
                top_null_fields.extend(hotspots[:3])
            dataset_profiles.append(
                {
                    "table": table_name,
                    "rows": self._safe_int(payload.get("rows"), 0),
                    "columns": len(payload.get("columns") or []),
                    "duplicate_rows": self._safe_int(payload.get("duplicate_rows"), 0),
                    "max_null_ratio": hotspots[0]["null_ratio"] if hotspots else 0.0,
                    "hotspot_fields": hotspots[:3],
                }
            )

        dataset_profiles = sorted(
            dataset_profiles,
            key=lambda item: (item["rows"], item["max_null_ratio"]),
            reverse=True,
        )
        top_null_fields = sorted(top_null_fields, key=lambda item: item["null_ratio"], reverse=True)[:8]

        return {
            "warehouse_db": warehouse_summary.get("warehouse_db"),
            "warehouse_table_count": self._safe_int(warehouse_summary.get("table_count"), 0),
            "mart_views": list(warehouse_summary.get("mart_views") or []),
            "csv_artifact_count": len(quality_report.get("artifacts") or []),
            "parquet_artifact_count": len(quality_report.get("parquet_artifacts") or []),
            "total_warehouse_rows": total_rows,
            "lake_layers": sorted(
                layer_map.values(),
                key=lambda item: self._safe_int(item.get("row_count"), 0),
                reverse=True,
            ),
            "dataset_profiles": dataset_profiles[:8],
            "top_null_fields": top_null_fields,
            "official_inventory_rows": self._safe_int(
                (quality_report.get("official_report_inventory") or {}).get("rows"),
                0,
            ),
            "multimodal_extract_report_count": self._safe_int(multimodal_summary.get("report_count"), 0),
        }

    def get_preparation_summary(self) -> dict:
        processed_dir = settings.processed_dir
        quality_dir = settings.data_dir / "quality"
        model_dir = settings.cache_dir / "models"
        source_registry = self._load_source_registry_frame()
        financials = self._read_csv(processed_dir / "financial_features.csv", dtype={"company_code": str})
        research_reports = self._read_csv(processed_dir / "research_reports.csv", dtype={"company_code": str})
        industry_reports = self._read_csv(processed_dir / "industry_reports.csv")
        macro = self._read_csv(processed_dir / "macro_indicators.csv")
        universe = self._read_csv(processed_dir / "industry_company_universe.csv", dtype={"company_code": str})
        periodic = self._read_csv(processed_dir / "official_periodic_snapshots.csv", dtype={"company_code": str})
        promotion_plan = self._read_json(quality_dir / "target_promotion_plan.json")
        promoted_summary = self._read_json(quality_dir / "promoted_official_reports_summary.json")
        target_pool = load_targets()
        processed_files = list(processed_dir.glob("*.csv"))
        extracts = self._load_multimodal_extracts()
        promotion_years = [self._safe_int(item, 0) for item in (promoted_summary.get("years") or []) if self._safe_int(item, 0) > 0]
        if not promotion_years:
            promotion_years = [2024, 2023, 2022]
        annual_years: list[int] = []
        if not financials.empty and "report_year" in financials.columns:
            annual_years = sorted({self._safe_int(value) for value in financials["report_year"].dropna().tolist() if self._safe_int(value) > 0})

        source_status = [
            {
                "source_key": "official_financial_reports",
                "label": "官方财报",
                "rows": int(len(financials)),
                "latest": self._latest_text(financials["published_at"]) if "published_at" in financials.columns else None,
                "coverage_note": f"{len(target_pool)} 家核心企业主样本",
            },
            {
                "source_key": "stock_research_reports",
                "label": "个股研报",
                "rows": int(len(research_reports)),
                "latest": self._latest_text(research_reports["report_date"]) if "report_date" in research_reports.columns else None,
                "coverage_note": f"{research_reports['company_code'].astype(str).nunique() if not research_reports.empty else 0} 家企业",
            },
            {
                "source_key": "industry_research_reports",
                "label": "行业研报",
                "rows": int(len(industry_reports)),
                "latest": self._latest_text(industry_reports["report_date"]) if "report_date" in industry_reports.columns else None,
                "coverage_note": f"{industry_reports['industry_name'].nunique() if not industry_reports.empty and 'industry_name' in industry_reports.columns else 0} 个赛道",
            },
            {
                "source_key": "macro_indicators",
                "label": "宏观指标",
                "rows": int(len(macro)),
                "latest": self._latest_text(macro["period"]) if "period" in macro.columns else None,
                "coverage_note": f"{macro['indicator_name'].nunique() if not macro.empty and 'indicator_name' in macro.columns else 0} 个指标",
            },
        ]

        multimodal_sft_path = settings.data_dir / "datasets" / "official_multimodal_sft.jsonl"
        multimodal_sft_sample_count = 0
        if multimodal_sft_path.exists():
            with multimodal_sft_path.open("r", encoding="utf-8") as fp:
                multimodal_sft_sample_count = sum(1 for line in fp if line.strip())

        top_candidates = [
            {
                "company_code": str(item.get("company_code") or ""),
                "company_name": str(item.get("company_name") or ""),
                "industry_name": str(item.get("industry_name") or "") or None,
                "report_count": self._safe_int(item.get("report_count"), 0),
                "institution_count": self._safe_int(item.get("institution_count"), 0),
                "latest_report_date": str(item.get("latest_report_date") or "") or None,
                "priority_score": round(float(item.get("candidate_priority_score") or 0.0), 2),
            }
            for item in (promotion_plan.get("candidates") or [])[:6]
        ]

        selected_candidates = list(promotion_plan.get("candidates") or [])
        promotion_indexes = {
            "SSE": self._load_promotion_manifest_index("SSE"),
            "SZSE": self._load_promotion_manifest_index("SZSE"),
            "BSE": self._load_promotion_manifest_index("BSE"),
        }
        exchange_rollup: dict[str, dict[str, int | str]] = {}
        promoted_companies: list[dict] = []
        promoted_report_download_count = 0
        promoted_report_missing_count = 0
        promoted_ready_company_count = 0
        promoted_partial_company_count = 0
        for item in selected_candidates:
            exchange = str(item.get("exchange") or "").strip().upper()
            company_code = str(item.get("company_code") or "").strip()
            if not exchange or not company_code:
                continue
            indexed = promotion_indexes.get(exchange, {})
            downloaded_years: list[int] = []
            missing_years: list[int] = []
            published_at_values: list[str] = []
            for year in promotion_years:
                manifest_row = indexed.get((company_code, year)) or {}
                local_path = Path(str(manifest_row.get("local_path") or "")) if manifest_row.get("local_path") else None
                downloaded = (
                    str(manifest_row.get("status") or "").strip().lower() == "downloaded"
                    and local_path is not None
                    and local_path.exists()
                )
                if downloaded:
                    downloaded_years.append(year)
                    published_at = str(manifest_row.get("published_at") or "").strip()
                    if published_at:
                        published_at_values.append(published_at)
                else:
                    missing_years.append(year)
            promoted_report_download_count += len(downloaded_years)
            promoted_report_missing_count += len(missing_years)
            if downloaded_years and not missing_years:
                promoted_ready_company_count += 1
            elif downloaded_years:
                promoted_partial_company_count += 1
            bucket = exchange_rollup.setdefault(
                exchange,
                {"exchange": exchange, "selected_companies": 0, "downloaded_reports": 0, "missing_reports": 0},
            )
            bucket["selected_companies"] = self._safe_int(bucket.get("selected_companies"), 0) + 1
            bucket["downloaded_reports"] = self._safe_int(bucket.get("downloaded_reports"), 0) + len(downloaded_years)
            bucket["missing_reports"] = self._safe_int(bucket.get("missing_reports"), 0) + len(missing_years)
            promoted_companies.append(
                {
                    "company_code": company_code,
                    "company_name": str(item.get("company_name") or company_code),
                    "exchange": exchange,
                    "industry_name": str(item.get("industry_name") or "") or None,
                    "priority_score": round(float(item.get("candidate_priority_score") or 0.0), 2),
                    "downloaded_reports": len(downloaded_years),
                    "downloaded_years": downloaded_years,
                    "missing_years": missing_years,
                    "latest_published_at": max(published_at_values) if published_at_values else None,
                }
            )
        promoted_exchange_status = sorted(
            exchange_rollup.values(),
            key=lambda item: (
                self._safe_int(item.get("downloaded_reports"), 0),
                self._safe_int(item.get("selected_companies"), 0),
            ),
            reverse=True,
        )
        promoted_companies = sorted(
            promoted_companies,
            key=lambda item: (item["downloaded_reports"], item["priority_score"]),
            reverse=True,
        )

        risk_model_file_count = len(list(model_dir.glob("*")))
        universe_company_count = int(universe["company_code"].astype(str).nunique()) if not universe.empty and "company_code" in universe.columns else 0
        notes = [
            f"当前核心企业池 {len(target_pool)} 家，外围企业池 {universe_company_count} 家，已经具备下一轮扩样基础。",
            f"当前年度主样本覆盖 {min(annual_years) if annual_years else '未知'}-{max(annual_years) if annual_years else '未知'}，仍要继续补更细的季度和更大的企业池。",
            f"扩样候选已准备 {self._safe_int(promotion_plan.get('candidate_count'), 0)} 家，首批推荐 {self._safe_int(promotion_plan.get('selected_count'), 0)} 家，可直接进入下一轮抓取。",
        ]
        if selected_candidates:
            notes.append(
                f"首批扩样年报已下载 {promoted_report_download_count}/{promoted_report_download_count + promoted_report_missing_count} 份，"
                f"其中完整就绪 {promoted_ready_company_count} 家，部分缺失 {promoted_partial_company_count} 家。"
            )
        if multimodal_sft_sample_count <= 10:
            notes.append(f"多模态训练样本当前只有 {multimodal_sft_sample_count} 条，准备明显不足，需要继续扩充。")
        if risk_model_file_count:
            notes.append(f"风险模型目录已有 {risk_model_file_count} 个产物，但序列模型和系统化评测结果仍未稳定入库。")
        else:
            notes.append("模型目录当前没有稳定产物，训练准备不足。")

        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_count": int(source_registry["source_type"].nunique()) if not source_registry.empty and "source_type" in source_registry.columns else 0,
            "processed_dataset_count": len(processed_files),
            "target_pool_company_count": int(len(target_pool)),
            "universe_company_count": universe_company_count,
            "annual_years": annual_years,
            "latest_macro_period": self._latest_text(macro["period"]) if "period" in macro.columns else None,
            "latest_stock_report_date": self._latest_text(research_reports["report_date"]) if "report_date" in research_reports.columns else None,
            "latest_industry_report_date": self._latest_text(industry_reports["report_date"]) if "report_date" in industry_reports.columns else None,
            "periodic_report_rows": int(len(periodic)),
            "promotion_candidate_count": self._safe_int(promotion_plan.get("candidate_count"), 0),
            "selected_candidate_count": self._safe_int(promotion_plan.get("selected_count"), 0),
            "promotion_years": promotion_years,
            "promoted_report_download_count": promoted_report_download_count,
            "promoted_report_missing_count": promoted_report_missing_count,
            "promoted_ready_company_count": promoted_ready_company_count,
            "promoted_partial_company_count": promoted_partial_company_count,
            "multimodal_sft_sample_count": multimodal_sft_sample_count,
            "multimodal_extract_count": len(extracts),
            "risk_model_file_count": risk_model_file_count,
            "source_status": source_status,
            "top_candidates": top_candidates,
            "promoted_exchange_status": promoted_exchange_status,
            "promoted_companies": promoted_companies[:8],
            "preparation_notes": notes,
        }

    def get_governance_summary(self) -> dict:
        processed_dir = settings.processed_dir
        quality_dir = settings.data_dir / "quality"
        source_registry = self._load_source_registry_frame()
        financials = self._read_csv(processed_dir / "financial_features.csv", dtype={"company_code": str})
        research_reports = self._read_csv(processed_dir / "research_reports.csv", dtype={"company_code": str})
        periodic = self._read_csv(processed_dir / "official_periodic_snapshots.csv", dtype={"company_code": str})
        quality_report = self._read_json(quality_dir / "quality_report.json")
        targets = load_targets()
        target_frame = pd.DataFrame(targets)
        multimodal_extracts = pd.DataFrame(self._load_multimodal_extracts())

        source_catalog = source_registry.fillna("").to_dict("records") if not source_registry.empty else []

        financial_group = {}
        if not financials.empty:
            financial_group = {
                code: group
                for code, group in financials.groupby(financials["company_code"].astype(str))
            }
        research_group = {}
        if not research_reports.empty:
            research_group = {
                code: group
                for code, group in research_reports.groupby(research_reports["company_code"].astype(str))
            }
        periodic_group = {}
        if not periodic.empty:
            periodic_group = {
                code: group
                for code, group in periodic.groupby(periodic["company_code"].astype(str))
            }
        multimodal_group = {}
        if not multimodal_extracts.empty:
            multimodal_group = {
                code: group
                for code, group in multimodal_extracts.groupby(multimodal_extracts["company_code"].astype(str))
            }

        company_coverage: list[dict] = []
        if not target_frame.empty:
            for row in target_frame.to_dict("records"):
                code = str(row.get("company_code") or "")
                finance_rows = financial_group.get(code, pd.DataFrame())
                research_rows = research_group.get(code, pd.DataFrame())
                periodic_rows = periodic_group.get(code, pd.DataFrame())
                multimodal_rows = multimodal_group.get(code, pd.DataFrame())
                annual_years = []
                if not finance_rows.empty and "report_year" in finance_rows.columns:
                    annual_years = sorted(
                        {
                            self._safe_int(value)
                            for value in finance_rows["report_year"].dropna().tolist()
                            if self._safe_int(value) > 0
                        }
                    )
                latest_disclosure = None
                if not periodic_rows.empty and "published_at" in periodic_rows.columns:
                    latest_disclosure = self._latest_text(periodic_rows["published_at"])
                elif not finance_rows.empty and "published_at" in finance_rows.columns:
                    latest_disclosure = self._latest_text(finance_rows["published_at"])
                company_coverage.append(
                    {
                        "company_code": code,
                        "company_name": str(row.get("company_name") or code),
                        "exchange": str(row.get("exchange") or ""),
                        "industry": str(row.get("industry") or "") or None,
                        "annual_years": annual_years,
                        "annual_report_count": len(annual_years),
                        "periodic_report_count": int(len(periodic_rows)),
                        "research_report_count": int(len(research_rows)),
                        "multimodal_extract_count": int(len(multimodal_rows)),
                        "latest_disclosure": latest_disclosure,
                        "latest_research_report": self._latest_text(research_rows["report_date"]) if not research_rows.empty and "report_date" in research_rows.columns else None,
                    }
                )
        company_coverage = sorted(
            company_coverage,
            key=lambda item: (
                item["annual_report_count"],
                item["periodic_report_count"],
                item["research_report_count"],
            ),
            reverse=True,
        )

        extraction_map = {
            "financial_features": ("financial", "规则抽取 + 人工复核", "经营诊断 / 企业对比 / 风险判断"),
            "research_reports": ("research", "公开页面解析", "问答检索 / 观点证据"),
            "industry_reports": ("research", "公开页面解析", "行业趋势 / 对比背景"),
            "macro_indicators": ("macro", "公开统计录入", "宏观脉冲 / 决策背景"),
            "source_registry": ("registry", "人工维护", "来源登记 / 合规说明"),
            "company_fact": ("derived", "湖仓聚合", "工作台摘要 / 对比视图"),
        }
        field_quality: list[dict] = []
        for dataset_name, payload in quality_report.items():
            if not isinstance(payload, dict) or "null_ratio" not in payload:
                continue
            source_type, extraction_method, usage_scope = extraction_map.get(
                dataset_name,
                ("unknown", "待识别", "治理补充"),
            )
            for field_name, ratio in (payload.get("null_ratio") or {}).items():
                try:
                    null_ratio = float(ratio)
                except (TypeError, ValueError):
                    continue
                if field_name in {"company_code", "source_url"}:
                    continue
                review_status = "稳定" if null_ratio <= 0.05 else "需关注" if null_ratio <= 0.2 else "重点复核"
                field_quality.append(
                    {
                        "dataset": dataset_name,
                        "field": str(field_name),
                        "source_type": source_type,
                        "extraction_method": extraction_method,
                        "null_ratio": round(null_ratio, 4),
                        "review_status": review_status,
                        "usage_scope": usage_scope,
                    }
                )
        field_quality = sorted(
            field_quality,
            key=lambda item: (item["null_ratio"], item["dataset"], item["field"]),
            reverse=True,
        )[:16]

        evidence_mapping = [
            {
                "module": "首页问答",
                "output_label": "问题理解与任务分流",
                "primary_sources": ["financial_features", "research_reports", "industry_reports", "macro_indicators"],
                "evidence_fields": ["query_terms", "task_mode", "thread_memory"],
                "verification_rule": "每次问答必须回传任务模式、线程记忆和证据关键词。",
            },
            {
                "module": "企业分析",
                "output_label": "经营诊断结论",
                "primary_sources": ["financial_features", "research_reports", "macro_indicators", "official_extract_multimodal"],
                "evidence_fields": ["sections", "trend_digest", "multimodal_digest", "financial_source_url"],
                "verification_rule": "结论页需能回到财报原文、图表锚点和研报证据。",
            },
            {
                "module": "企业对比",
                "output_label": "双企业横向判断",
                "primary_sources": ["company_fact", "research_reports", "industry_reports", "official_periodic_snapshots"],
                "evidence_fields": ["comparison_rows", "dimensions", "freshness_digest", "multimodal_digest"],
                "verification_rule": "每个对比结论都必须带来源时效和证据摘要。",
            },
            {
                "module": "风险判断",
                "output_label": "风险等级与监测项",
                "primary_sources": ["financial_features", "risk_model_artifacts", "research_reports"],
                "evidence_fields": ["risk_score", "heuristic_score", "model_prediction", "monitoring_items"],
                "verification_rule": "风险页同时展示规则分、模型概率和监测项，避免黑箱判断。",
            },
            {
                "module": "报告导出",
                "output_label": "结构化分析材料",
                "primary_sources": ["company_report", "decision_brief", "citations", "quality_summary"],
                "evidence_fields": ["sections", "citations", "quality_snapshot", "exported_at"],
                "verification_rule": "导出内容必须带时间戳、引用清单和质量快照。",
            },
        ]

        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "source_catalog": source_catalog,
            "company_coverage": company_coverage,
            "field_quality": field_quality,
            "evidence_mapping": evidence_mapping,
        }

    def submit_manual_review(
        self,
        company_code: str,
        report_year: int,
        finding_level: str,
        finding_type: str,
        note: str,
    ) -> dict:
        record = ReviewRecord(
            company_code=str(company_code),
            report_year=int(report_year),
            finding_level=finding_level,
            finding_type=finding_type,
            note=note.strip(),
            status="pending",
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
        self._append_review_records([record])
        return record.as_dict()
