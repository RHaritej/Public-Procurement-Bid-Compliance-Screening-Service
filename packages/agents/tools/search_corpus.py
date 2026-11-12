"""Tool: search_corpus (Section 6.4).
Supports filtering by corpus_scope, applies_to, and topics.
"""

from typing import List, Optional
from bidscreen_contracts.enums import CorpusScope, BidderCategory
from bidscreen_contracts.tools import Passage
from packages.agents.tools.corpus_store import CORPUS_PASSAGES


def search_corpus(
    query: str,
    corpus_scope: CorpusScope = CorpusScope.ALL,
    applies_to: Optional[str] = None,
    topics: Optional[List[str]] = None,
    top_k: int = 5,
    profile: str = "full",
) -> List[Passage]:
    """Searches the corpus passages according to scope and filters."""
    query_lower = query.lower()
    results: List[tuple[float, Passage]] = []

    for clause_id, passage in CORPUS_PASSAGES.items():
        # Handle tender_core ablation profile (leaving out MII.1 - MII.4)
        if profile == "tender_core" and clause_id.startswith("GEM_BID_8034326::MII."):
            mii_num = clause_id.split("::MII.")[-1]
            if mii_num in ["1", "2", "3", "4"]:
                continue

        p_corpus = passage.metadata.get("corpus", "")
        # Scope filter
        if corpus_scope != CorpusScope.ALL:
            if corpus_scope.value != p_corpus:
                continue

        # Applies_to category filter
        if applies_to:
            p_applies = passage.metadata.get("applies_to", [])
            if p_applies and applies_to not in p_applies:
                continue

        # Topics filter
        if topics:
            p_topics = passage.metadata.get("topics", [])
            if not any(t.lower() in [pt.lower() for pt in p_topics] for t in topics):
                continue

        # Scoring relevance
        score = 0.0
        text_lower = passage.text.lower()
        clause_lower = passage.clause_id.lower()

        # Keyword matching
        for term in query_lower.split():
            if term in text_lower:
                score += 2.0
            if term in clause_lower:
                score += 3.0

        if score > 0 or not query.strip():
            results.append((score, passage))

    # Sort descending by score
    results.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in results[:top_k]]

