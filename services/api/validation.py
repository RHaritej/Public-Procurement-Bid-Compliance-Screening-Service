"""Validation helpers for incoming bid screening requests.

Conforms to Mini Project 06 §6.1 data contract and §6.2 REST API behavior.
On validation failure, errors are mapped into structured field-level error records.
"""

from __future__ import annotations

from typing import Any, Tuple

from pydantic import ValidationError

from bidscreen_contracts.bid_summary import BidSummary


def validate_bid_summary(payload: dict[str, Any]) -> Tuple[BidSummary | None, list[dict[str, str]]]:
    """Validate raw request dictionary against the BidSummary contract.

    Returns:
        (bid_summary, []) on success
        (None, [ {"field": "...", "code": "...", "message": "..."} ]) on failure
    """
    try:
        bid = BidSummary.model_validate(payload)
        return bid, []
    except ValidationError as exc:
        errors: list[dict[str, str]] = []
        for err in exc.errors():
            loc = ".".join(str(part) for part in err["loc"])
            errors.append(
                {
                    "field": loc,
                    "code": err["type"],
                    "message": err["msg"],
                }
            )
        return None, errors
