"""Tool: find_modifying_provisions (Section 6.4).
Finds POLICY passages that may modify or relax a given tender clause for a given bidder category.
"""

from typing import List
from bidscreen_contracts.enums import BidderCategory
from bidscreen_contracts.tools import Passage
from packages.agents.tools.corpus_store import CORPUS_PASSAGES


def find_modifying_provisions(clause_id: str, bidder_category: BidderCategory) -> List[Passage]:
    """Finds policy passages modifying the specified clause for the category."""
    modifying: List[Passage] = []

    # Map clause keys to topics
    is_turnover = "turnover" in clause_id.lower()
    is_experience = "exp" in clause_id.lower() or "experience" in clause_id.lower()

    for p_id, passage in CORPUS_PASSAGES.items():
        if passage.metadata.get("corpus") != "POLICY":
            continue

        applies_to = passage.metadata.get("applies_to", [])
        if applies_to and bidder_category.value not in applies_to:
            continue

        # Check explicit modifies metadata
        modifies_meta = passage.metadata.get("modifies", "")
        if clause_id in modifies_meta:
            modifying.append(passage)
            continue

        # Check topic overlap
        topics = passage.metadata.get("topics", [])
        if is_turnover and "turnover" in topics and "relaxation" in topics:
            modifying.append(passage)
        elif is_experience and "experience" in topics and "relaxation" in topics:
            modifying.append(passage)

    return modifying

