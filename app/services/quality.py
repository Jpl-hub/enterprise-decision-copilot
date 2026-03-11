from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from app.config import settings


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
    ) -> None:
        quality_dir = settings.data_dir / "quality"
        raw_official_dir = settings.raw_dir / "official"
        review_dir = settings.data_dir / "review"
        self.official_quality_path = official_quality_path or (quality_dir / "financial_features_official_quality.csv")
        self.inventory_quality_path = inventory_quality_path or (quality_dir / "official_reports_quality.json")
        self.inventory_path = inventory_path or (raw_official_dir / "report_inventory.csv")
        self.review_queue_path = review_queue_path or (review_dir / "manual_review_queue.csv")
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
        return {
            "official_report_coverage_ratio": summary.get("official_report_coverage_ratio", 0.0),
            "pending_review_count": summary.get("pending_review_count", 0),
            "company_anomalies": anomalies[:5],
            "company_review_queue": queue[:5],
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

    def get_quality_summary(self) -> dict:
        inventory_quality = self._read_json(self.inventory_quality_path)
        queue = self.get_review_queue()
        anomalies = self.get_financial_anomalies(limit=8)
        pending_reviews = [item for item in queue if str(item.get("status") or "pending") == "pending"]
        coverage = inventory_quality.get("target_coverage", {})
        return {
            "official_report_coverage_ratio": round(float(coverage.get("coverage_ratio") or 0), 4),
            "official_report_downloaded_slots": int(coverage.get("downloaded_slots") or 0),
            "official_report_expected_slots": int(coverage.get("expected_slots") or 0),
            "missing_report_slots": int(len(coverage.get("missing_slots") or [])),
            "pending_review_count": int(len(pending_reviews)),
            "anomaly_company_count": int(len(anomalies)),
            "exchange_status": inventory_quality.get("exchanges", []),
            "top_anomalies": anomalies,
            "recent_reviews": queue[:8],
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
