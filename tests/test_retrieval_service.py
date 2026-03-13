from app.services.analytics import AnalyticsService
from app.services.retrieval import RetrievalService



def test_company_retrieval_returns_ranked_evidence_snippets() -> None:
    retrieval = RetrievalService(AnalyticsService())

    evidence = retrieval.retrieve_company_evidence("300760", "结合海外增长和风险看迈瑞医疗", limit=3)

    assert evidence["query_terms"]
    assert evidence["query_profile"]["query_variants"]
    assert evidence["query_profile"]["expansion_terms"]
    assert evidence["query_profile"]["semantic_ranker_ready"] is True
    assert evidence["stock_reports"]
    first = evidence["stock_reports"][0]
    assert first["company_code"] == "300760"
    assert first["matched_excerpt"]
    assert first["rerank_score"] >= first["relevance_score"]
    assert first["ranking_breakdown"]["hybrid_score"] >= 0
    assert first["ranking_breakdown"]["rerank_score"] == first["rerank_score"]
    assert first["ranking_breakdown"]["semantic_score"] >= 0
    assert isinstance(first["matched_terms"], list)
    assert any(signal.startswith("char=") for signal in first["ranking_signals"])
    assert any(signal.startswith("word=") for signal in first["ranking_signals"])
    assert any(signal.startswith("semantic=") for signal in first["ranking_signals"])



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


def test_retrieval_supports_multiple_modes() -> None:
    retrieval = RetrievalService(AnalyticsService())

    lexical = retrieval.retrieve_company_evidence("300760", "迈瑞医疗海外增长", limit=3, retrieval_mode="lexical_tfidf")
    semantic = retrieval.retrieve_company_evidence("300760", "迈瑞医疗海外增长", limit=3, retrieval_mode="hybrid_semantic_rerank")
    diversified = retrieval.retrieve_company_evidence("300760", "迈瑞医疗海外增长", limit=3, retrieval_mode="hybrid_diversified")

    assert lexical["query_profile"]["retrieval_mode"] == "lexical_tfidf"
    assert "word_tfidf" in lexical["query_profile"]["strategy_labels"]
    assert lexical["stock_reports"][0]["ranking_breakdown"]["retrieval_mode"] == "lexical_tfidf"
    assert semantic["query_profile"]["retrieval_mode"] == "hybrid_semantic_rerank"
    assert "latent_semantic" in semantic["query_profile"]["strategy_labels"]
    assert semantic["stock_reports"][0]["ranking_breakdown"]["semantic_score"] >= 0
    assert diversified["query_profile"]["retrieval_mode"] == "hybrid_diversified"
    assert "institution_diversity" in diversified["query_profile"]["strategy_labels"]
    assert diversified["stock_reports"][0]["ranking_breakdown"]["diversity_boost"] >= 0
