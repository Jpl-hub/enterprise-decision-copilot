from __future__ import annotations

from dataclasses import dataclass
import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from app.services.analytics import AnalyticsService


POSITIVE_QUERY_KEYWORDS = ("机会", "增长", "景气", "出海", "海外", "创新", "龙头", "扩张")
RISK_QUERY_KEYWORDS = ("风险", "承压", "预警", "下滑", "波动", "拖累", "不确定")
QUERY_HINT_KEYWORDS = (
    "机会",
    "风险",
    "增长",
    "盈利",
    "现金流",
    "创新",
    "研发",
    "国际",
    "海外",
    "AI",
    "医疗",
    "集采",
    "器械",
    "药店",
    "CXO",
)
STOP_TOKENS = {"结合", "以及", "这个", "那个", "情况", "说明", "分析", "一下", "企业", "公司", "行业", "研报"}
IDENTIFIER_COLUMNS = {"company_code", "industry_code", "security_code", "disclosure_company_code"}


@dataclass(slots=True)
class CorpusIndex:
    frame: pd.DataFrame
    chunk_frame: pd.DataFrame
    vectorizer: TfidfVectorizer | None
    matrix: object | None
    text_column: str


class RetrievalService:
    def __init__(self, analytics_service: AnalyticsService) -> None:
        self.analytics_service = analytics_service
        self.stock_index = self._build_index(
            analytics_service.reports,
            ["company_name", "title", "analyst_view", "institution", "content"],
        )
        self.industry_index = self._build_index(
            analytics_service.industry_reports,
            ["industry_name", "title", "institution", "content"],
        )

    def _build_index(self, frame: pd.DataFrame, columns: list[str]) -> CorpusIndex:
        if frame.empty:
            empty = frame.copy()
            return CorpusIndex(frame=empty, chunk_frame=empty, vectorizer=None, matrix=None, text_column="_search_text")

        corpus = frame.copy().reset_index(drop=True)
        corpus["_report_id"] = corpus.index.astype(int)
        corpus["_document"] = corpus[columns].fillna("").astype(str).agg(" ".join, axis=1).apply(self._normalize_text)

        chunk_rows: list[dict] = []
        for row in corpus.to_dict("records"):
            for chunk_id, chunk_text in enumerate(self._chunk_document(row), start=1):
                search_text = self._normalize_text(
                    " ".join(
                        [
                            str(row.get("company_name") or row.get("industry_name") or ""),
                            str(row.get("title") or ""),
                            str(row.get("analyst_view") or ""),
                            str(row.get("institution") or ""),
                            chunk_text,
                        ]
                    )
                )
                chunk_rows.append(
                    {
                        **row,
                        "_chunk_id": chunk_id,
                        "_chunk_text": chunk_text,
                        "_search_text": search_text,
                    }
                )

        chunk_frame = pd.DataFrame(chunk_rows)
        vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            min_df=1,
            max_features=12000,
            sublinear_tf=True,
        )
        matrix = vectorizer.fit_transform(chunk_frame["_search_text"])
        return CorpusIndex(frame=corpus, chunk_frame=chunk_frame, vectorizer=vectorizer, matrix=matrix, text_column="_search_text")

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "")).strip()

    def _chunk_document(self, row: dict, max_chars: int = 140) -> list[str]:
        primary = self._normalize_text(str(row.get("content") or ""))
        title = self._normalize_text(str(row.get("title") or ""))
        view = self._normalize_text(str(row.get("analyst_view") or ""))

        segments = [segment.strip() for segment in re.split(r"[。；！？\n]", primary) if segment.strip()]
        if not segments:
            fallback = "；".join(item for item in [title, view] if item)
            return [fallback] if fallback else [title or "暂无研报摘要"]

        chunks: list[str] = []
        current = ""
        for segment in segments:
            if len(segment) > max_chars:
                if current:
                    chunks.append(current)
                    current = ""
                for idx in range(0, len(segment), max_chars):
                    part = segment[idx: idx + max_chars].strip()
                    if part:
                        chunks.append(part)
                continue
            proposed = f"{current}；{segment}" if current else segment
            if len(proposed) > max_chars and current:
                chunks.append(current)
                current = segment
            else:
                current = proposed
        if current:
            chunks.append(current)

        if title:
            chunks.insert(0, title)
        return chunks[:8]

    def _normalize_result_row(self, row: dict) -> dict:
        normalized: dict = {}
        for key, value in row.items():
            if key in IDENTIFIER_COLUMNS and pd.notna(value):
                try:
                    normalized[key] = str(int(value))
                except Exception:
                    normalized[key] = str(value).strip()
                continue
            normalized[key] = value
        return normalized

    def _build_excerpt(self, row: dict, max_chars: int = 180) -> str:
        title = self._normalize_text(str(row.get("title") or ""))
        excerpt = self._normalize_text(str(row.get("_chunk_text") or ""))
        if title and excerpt.startswith(title + "；"):
            excerpt = self._normalize_text(excerpt[len(title) + 1:])
        if not excerpt or excerpt == title or len(excerpt) <= 6:
            for key in ("content", "analyst_view"):
                candidate = self._normalize_text(str(row.get(key) or ""))
                if candidate and candidate != title and len(candidate) > 6:
                    excerpt = candidate
                    break
        if title and any(excerpt.startswith(prefix) for prefix in ("机构：", "评级：", "作者：", "细分行业：", "信息编号：")):
            excerpt = title
        return excerpt[:max_chars]

    def _latest_rows(self, frame: pd.DataFrame, columns: list[str], limit: int) -> list[dict]:
        if frame.empty:
            return []
        ranked = frame.copy()
        ranked["report_date"] = ranked["report_date"].astype(str)
        ranked = ranked.sort_values("report_date", ascending=False).head(limit)
        rows = []
        for row in ranked[columns].to_dict("records"):
            row = self._normalize_result_row(row)
            row["matched_excerpt"] = self._normalize_text(str(row.get("content") or row.get("title") or ""))[:140]
            row["relevance_score"] = 0.0
            row["rerank_score"] = 0.0
            row["ranking_signals"] = ["fallback_latest"]
            rows.append(row)
        return rows

    def _extract_query_keywords(self, query: str) -> list[str]:
        normalized = self._normalize_text(query)
        terms: list[str] = []
        for token in re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]{2,}", normalized):
            compact = token.strip()
            if len(compact) > 10:
                continue
            if compact in STOP_TOKENS or compact in terms:
                continue
            terms.append(compact)
        for phrase in QUERY_HINT_KEYWORDS:
            if phrase in normalized and phrase not in terms:
                terms.append(phrase)
        return terms[:8]

    def _sentiment_bias(self, query: str, sentiment: str | None) -> float:
        text = self._normalize_text(query)
        sentiment = str(sentiment or "")
        if any(keyword in text for keyword in RISK_QUERY_KEYWORDS):
            if sentiment == "negative":
                return 0.12
            if sentiment == "positive":
                return -0.03
        if any(keyword in text for keyword in POSITIVE_QUERY_KEYWORDS):
            if sentiment == "positive":
                return 0.08
            if sentiment == "negative":
                return -0.02
        return 0.0

    def _keyword_overlap(self, query_terms: list[str], chunk_text: str, title: str) -> tuple[float, list[str]]:
        matched = [term for term in query_terms if term and (term in chunk_text or term in title)]
        if not query_terms:
            return 0.0, []
        return min(0.18, 0.06 * len(matched)), matched

    def _date_boost(self, report_date: str, min_ord: int, max_ord: int) -> float:
        try:
            ordinal = pd.to_datetime(report_date).toordinal()
        except Exception:
            return 0.0
        if max_ord <= min_ord:
            return 0.02
        return round(((ordinal - min_ord) / (max_ord - min_ord)) * 0.08, 4)

    def _search(self, index: CorpusIndex, query: str, limit: int, filter_mask: pd.Series | None = None) -> list[dict]:
        if index.frame.empty:
            return []

        frame = index.frame
        columns = [column for column in frame.columns if not column.startswith("_")]
        candidate_mask = filter_mask if filter_mask is not None else pd.Series(True, index=frame.index)
        candidate_mask = candidate_mask.fillna(False)
        candidate_reports = frame[candidate_mask].copy()
        if candidate_reports.empty:
            return []

        if not query.strip() or index.vectorizer is None or index.matrix is None:
            return self._latest_rows(candidate_reports, columns, limit)

        candidate_report_ids = set(candidate_reports["_report_id"].tolist())
        candidate_chunk_mask = index.chunk_frame["_report_id"].isin(candidate_report_ids)
        candidate_chunks = index.chunk_frame[candidate_chunk_mask].copy()
        if candidate_chunks.empty:
            return self._latest_rows(candidate_reports, columns, limit)

        query_vector = index.vectorizer.transform([self._normalize_text(query)])
        base_scores = linear_kernel(query_vector, index.matrix).ravel()
        base_scores = np.where(candidate_chunk_mask.to_numpy(), base_scores, -1.0)
        query_terms = self._extract_query_keywords(query)

        report_dates = pd.to_datetime(candidate_reports.get("report_date"), errors="coerce") if "report_date" in candidate_reports else pd.Series(dtype="datetime64[ns]")
        min_ord = int(report_dates.min().toordinal()) if not report_dates.empty and pd.notna(report_dates.min()) else 0
        max_ord = int(report_dates.max().toordinal()) if not report_dates.empty and pd.notna(report_dates.max()) else 0

        ranked_chunks = []
        for chunk_idx in base_scores.argsort()[::-1]:
            base_score = float(base_scores[chunk_idx])
            if base_score <= 0:
                continue
            chunk_row = index.chunk_frame.iloc[int(chunk_idx)]
            keyword_boost, matched_terms = self._keyword_overlap(
                query_terms,
                str(chunk_row.get("_chunk_text") or ""),
                str(chunk_row.get("title") or ""),
            )
            date_boost = self._date_boost(str(chunk_row.get("report_date") or ""), min_ord, max_ord)
            sentiment_boost = self._sentiment_bias(query, chunk_row.get("sentiment"))
            company_boost = 0.05 if str(chunk_row.get("company_name") or "") and str(chunk_row.get("company_name")) in query else 0.0
            rerank_score = round(base_score * 0.72 + keyword_boost + date_boost + sentiment_boost + company_boost, 4)
            signals = [f"vector={base_score:.4f}"]
            if matched_terms:
                signals.append("keyword=" + "|".join(matched_terms[:3]))
            if date_boost > 0:
                signals.append(f"recency={date_boost:.3f}")
            if sentiment_boost != 0:
                signals.append(f"sentiment={sentiment_boost:.3f}")
            if company_boost > 0:
                signals.append("entity=company")
            ranked_chunks.append((rerank_score, base_score, chunk_row, signals))
            if len(ranked_chunks) >= max(limit * 12, 24):
                break

        selected_reports = []
        seen_report_ids: set[int] = set()
        for rerank_score, base_score, chunk_row, signals in sorted(ranked_chunks, key=lambda item: item[0], reverse=True):
            report_id = int(chunk_row["_report_id"])
            if report_id in seen_report_ids:
                continue
            seen_report_ids.add(report_id)
            report_row = frame.iloc[report_id].to_dict()
            report_row = {key: value for key, value in report_row.items() if not key.startswith("_")}
            report_row = self._normalize_result_row(report_row)
            report_row["matched_excerpt"] = self._build_excerpt(chunk_row)
            report_row["relevance_score"] = round(base_score, 4)
            report_row["rerank_score"] = rerank_score
            report_row["ranking_signals"] = signals
            selected_reports.append(report_row)
            if len(selected_reports) >= limit:
                break

        if selected_reports:
            return selected_reports
        return self._latest_rows(candidate_reports, columns, limit)

    def retrieve_company_evidence(self, company_code: str, query: str, limit: int = 4) -> dict:
        company_code = str(company_code)
        stock_mask = self.stock_index.frame["company_code"].astype(str) == company_code if not self.stock_index.frame.empty else None

        target = self.analytics_service.targets[self.analytics_service.targets["company_code"].astype(str) == company_code]
        keywords: list[str] = []
        if not target.empty:
            keywords = self.analytics_service._segment_to_industry_keywords(str(target.iloc[0]["segment"]))
        industry_mask = None
        if not self.industry_index.frame.empty and keywords:
            industry_mask = self.industry_index.frame["industry_name"].astype(str).apply(
                lambda name: any(keyword in name for keyword in keywords)
            )

        return {
            "query": query,
            "query_terms": self._extract_query_keywords(query),
            "stock_reports": self._search(self.stock_index, query, limit, stock_mask),
            "industry_reports": self._search(self.industry_index, query, limit, industry_mask),
        }

    def retrieve_industry_evidence(self, query: str, limit: int = 6) -> dict:
        return {
            "query": query,
            "query_terms": self._extract_query_keywords(query),
            "industry_reports": self._search(self.industry_index, query, limit),
        }
