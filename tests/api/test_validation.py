"""Unit tests for BidSummary schema validation and quarantine mappings."""

from __future__ import annotations

import copy
from datetime import date, timedelta
import pytest

try:
    from services.api.validation import validate_bid_summary
except ImportError:
    from validation import validate_bid_summary
from bidscreen_contracts.bid_summary import BidSummary


def test_valid_bid_summary(valid_bid_payload):
    """Ensure a compliant Section 4.1 payload passes validation with 0 errors."""
    bid, errors = validate_bid_summary(valid_bid_payload)
    assert errors == []
    assert bid is not None
    assert bid.bid_ref == "TEST-BID-001"
    assert bid.tender_id == "GEM/2026/B/8034326"


def test_invalid_tender_id(valid_bid_payload):
    """Tender ID lock must reject non-matching tender IDs."""
    payload = copy.deepcopy(valid_bid_payload)
    payload["tender_id"] = "GEM/2025/B/9999999"

    bid, errors = validate_bid_summary(payload)
    assert bid is None
    assert len(errors) == 1
    assert "tender_id" in errors[0]["field"]


def test_future_incorporation_date(valid_bid_payload):
    """Future incorporation dates must be rejected."""
    payload = copy.deepcopy(valid_bid_payload)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    payload["bidder"]["incorporation_date"] = tomorrow

    bid, errors = validate_bid_summary(payload)
    assert bid is None
    assert any("incorporation_date" in err["field"] for err in errors)


def test_foreign_category_with_indian_country_code(valid_bid_payload):
    """FOREIGN category cannot declare country_code 'IN'."""
    payload = copy.deepcopy(valid_bid_payload)
    payload["bidder"]["declared_category"] = "FOREIGN"
    payload["bidder"]["country_code"] = "IN"

    bid, errors = validate_bid_summary(payload)
    assert bid is None
    assert any("FOREIGN" in err["message"] for err in errors)


def test_land_border_missing_registration(valid_bid_payload):
    """Bidders from land-border countries (e.g. CN) must declare land_border_registered."""
    payload = copy.deepcopy(valid_bid_payload)
    payload["bidder"]["country_code"] = "CN"
    payload["bidder"]["declared_category"] = "FOREIGN"
    payload["bidder"]["land_border_registered"] = None

    bid, errors = validate_bid_summary(payload)
    assert bid is None
    assert any("land border" in err["message"] for err in errors)


def test_negative_turnover(valid_bid_payload):
    """Negative financial turnover entries must be rejected."""
    payload = copy.deepcopy(valid_bid_payload)
    payload["bidder"]["annual_turnover_lakh"] = [-10.0, 100.0, 200.0]

    bid, errors = validate_bid_summary(payload)
    assert bid is None
    assert any("turnover" in err["message"] for err in errors)
