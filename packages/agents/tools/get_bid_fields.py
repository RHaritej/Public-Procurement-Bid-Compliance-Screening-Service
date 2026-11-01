"""Tool: get_bid_fields (Section 6.4).
Extracts requested dot-notation field values from a validated BidSummary.
"""

from typing import List, Dict, Any
from bidscreen_contracts.bid_summary import BidSummary


def get_bid_fields(bid: BidSummary, field_paths: List[str]) -> Dict[str, Any]:
    """Retrieves dot-notation field paths from the bid summary."""
    bid_dict = bid.model_dump()
    result = {}

    for path in field_paths:
        parts = path.split(".")
        val: Any = bid_dict
        found = True
        for part in parts:
            if isinstance(val, dict) and part in val:
                val = val[part]
            else:
                found = False
                break
        if found:
            result[path] = val
        else:
            result[path] = None

    return result

