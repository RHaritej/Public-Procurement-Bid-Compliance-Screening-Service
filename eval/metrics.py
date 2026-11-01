"""Evaluation metrics for Screening System (Requirement L3, L5).
Computes Groundedness, Context Relevance, Faithfulness, Hallucination Rate, and Route Accuracy.
"""

from typing import List, Dict, Any
from bidscreen_contracts.run import ScreeningResult
from bidscreen_contracts.tools import Passage


def compute_groundedness(result: ScreeningResult, passage_store: Dict[str, Passage]) -> float:
    """Computes Groundedness: ratio of citations whose quotes match retrieved passage text."""
    total_citations = 0
    grounded_citations = 0

    for finding in result.findings:
        for cit in finding.citations:
            total_citations += 1
            passage = passage_store.get(cit.clause_id) or passage_store.get(cit.passage_id)
            if passage:
                quote_lead = " ".join(cit.quote.lower().split()[:4])
                if quote_lead in passage.text.lower():
                    grounded_citations += 1

    if total_citations == 0:
        return 1.0
    return round(grounded_citations / total_citations, 4)


def compute_context_relevance(result: ScreeningResult, passage_store: Dict[str, Passage]) -> float:
    """Computes Context Relevance: fraction of retrieved passages that are cited in findings."""
    total_retrieved = len(passage_store)
    if total_retrieved == 0:
        return 1.0

    cited_passage_ids = set()
    for finding in result.findings:
        for cit in finding.citations:
            cited_passage_ids.add(cit.clause_id)
            cited_passage_ids.add(cit.passage_id)

    relevant_count = sum(1 for p_id in passage_store if p_id in cited_passage_ids)
    return round(min(1.0, relevant_count / max(1, total_retrieved)), 4)


def compute_faithfulness(result: ScreeningResult, passage_store: Dict[str, Passage]) -> float:
    """Computes Faithfulness: checks that summary claims align with cited passages."""
    groundedness = compute_groundedness(result, passage_store)
    # Penalize if unsupported findings exist
    unsupported_count = 0
    total_conditions = len(result.findings)

    for f in result.findings:
        if f.status.value in ("MET", "UNMET", "CONFLICT") and not f.citations:
            unsupported_count += 1

    penalty = unsupported_count / max(1, total_conditions)
    faithfulness = max(0.0, groundedness * (1.0 - 0.5 * penalty))
    return round(faithfulness, 4)


def compute_hallucination_rate(result: ScreeningResult, passage_store: Dict[str, Passage]) -> float:
    """Computes Hallucination Rate: proportion of ungrounded or fabricated citations."""
    groundedness = compute_groundedness(result, passage_store)
    return round(max(0.0, 1.0 - groundedness), 4)


def evaluate_run(
    result: ScreeningResult,
    expected_route: str,
    passage_store: Dict[str, Passage],
) -> Dict[str, float]:
    """Evaluates a screening run across all five core metrics."""
    route_match = 1.0 if result.route.value == expected_route else 0.0
    groundedness = compute_groundedness(result, passage_store)
    context_relevance = compute_context_relevance(result, passage_store)
    faithfulness = compute_faithfulness(result, passage_store)
    hallucination_rate = compute_hallucination_rate(result, passage_store)

    return {
        "route_accuracy": route_match,
        "groundedness": groundedness,
        "context_relevance": context_relevance,
        "faithfulness": faithfulness,
        "hallucination_rate": hallucination_rate,
    }

