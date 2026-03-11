from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from app.config import settings
from app.data_access import load_targets


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
        self.review_queue_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_csv(self, path: Path, dtype: dict[str, str] | None = None) -> pd.DataFrame:
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(path, dtype=dtype)

    def _read_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

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
                    "field_source_count": len(payload.get("field_sources") or {}),
                    "filled_field_count": self._filled_multimodal_fields(payload),
                    "notes": list(payload.get("notes") or []),
                }
            )
        return records

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
