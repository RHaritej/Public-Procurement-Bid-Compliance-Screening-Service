"""Unit tests for Multi-Hop Retrieval Engine (Member B)."""

import pytest
from services.retrieval.retriever import MultiHopRetriever


@pytest.fixture
def retriever():
    return MultiHopRetriever()


def test_get_clause_exact(retriever):
    chunk = retriever.get_clause("GEM_BID_8034326::HDR.min_turnover")
    assert chunk is not None
    assert "235 Lakh" in chunk.text
    assert chunk.metadata.get("threshold_lakh") == 235.0


def test_search_tender_scope(retriever):
    results = retriever.search(
        query="Minimum Average Annual Turnover",
        corpus_scope="TENDER",
        top_k=3,
    )
    assert len(results) > 0
    assert any("235" in r["text"] for r in results)


def test_search_policy_relaxation(retriever):
    results = retriever.search(
        query="relaxation prior turnover experience startup",
        corpus_scope="POLICY",
        applies_to="STARTUP",
        top_k=3,
    )
    assert len(results) > 0
    assert any("DOE_OM_2016_09_20" in r["clause_id"] for r in results)


def test_find_modifying_provisions_turnover_startup(retriever):
    modifying = retriever.find_modifying_provisions(
        condition_id="MC-02",
        bidder_category="STARTUP",
    )
    assert len(modifying) > 0
    clause_ids = [m["clause_id"] for m in modifying]
    assert any("DOE_OM_2016_09_20" in c or "MII.4" in c for c in clause_ids)
