from app.services.analytics import AnalyticsService
from app.services.retrieval import RetrievalService



def test_company_retrieval_returns_ranked_evidence_snippets() -> None:
    retrieval = RetrievalService(AnalyticsService())

    evidence = retrieval.retrieve_company_evidence("300760", "结合海外增长和风险看迈瑞医疗", limit=3)

    assert evidence["query_terms"]
    assert evidence["query_profile"]["query_variants"]
    assert evidence["query_profile"]["expansion_terms"]
    assert evidence["stock_reports"]
    first = evidence["stock_reports"][0]
    assert first["company_code"] == "300760"
    assert first["matched_excerpt"]
    assert first["rerank_score"] >= first["relevance_score"]
    assert first["ranking_breakdown"]["hybrid_score"] >= 0
    assert first["ranking_breakdown"]["rerank_score"] == first["rerank_score"]
    assert isinstance(first["matched_terms"], list)
    assert any(signal.startswith("char=") for signal in first["ranking_signals"])
    assert any(signal.startswith("word=") for signal in first["ranking_signals"])



def test_industry_retrieval_returns_reranked_reports() -> None:
    retrieval = RetrievalService(AnalyticsService())

    evidence = retrieval.retrieve_industry_evidence("AI医疗和创新药机会", limit=4)

    assert evidence["industry_reports"]
    assert evidence["query_profile"]["query_variants"]
    first = evidence["industry_reports"][0]
    assert first["matched_excerpt"]
    assert first["ranking_signals"]
    assert first["ranking_breakdown"]["query_variant_count"] >= 1
    assert any(signal.startswith("hybrid=") for signal in first["ranking_signals"])
    assert "rerank_score" in first
