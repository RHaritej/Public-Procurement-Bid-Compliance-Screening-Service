"""Tool: check_threshold (Section 6.4).
Deterministic comparison of numerical values without LLM involvement.
"""

from typing import Dict, Any


def check_threshold(name: str, bidder_value: float, threshold: float) -> Dict[str, Any]:
    """Deterministically compares a bidder's metric against a required threshold."""
    meets = bidder_value >= threshold
    margin = bidder_value - threshold
    return {
        "name": name,
        "bidder_value": bidder_value,
        "threshold": threshold,
        "meets_threshold": meets,
        "margin": round(margin, 2),
    }

