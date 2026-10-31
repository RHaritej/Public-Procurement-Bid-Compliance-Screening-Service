"""Pytest configuration and shared fixtures for API tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project roots to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "contracts"))
sys.path.insert(0, str(BASE_DIR / "packages" / "common"))
sys.path.insert(0, str(BASE_DIR / "services" / "api"))
sys.path.insert(0, str(BASE_DIR))

import pytest
from fastapi.testclient import TestClient

try:
    from services.api.main import app
    from services.api.routes.runs import RUNS_STORE, IDEMPOTENCY_STORE, FEEDBACK_STORE
    from services.api.quarantine import _IN_MEMORY_QUARANTINE
except ImportError:
    from main import app
    from routes.runs import RUNS_STORE, IDEMPOTENCY_STORE, FEEDBACK_STORE
    from quarantine import _IN_MEMORY_QUARANTINE


@pytest.fixture(autouse=True)
def clean_stores():
    """Clear in-memory databases between tests."""
    RUNS_STORE.clear()
    IDEMPOTENCY_STORE.clear()
    FEEDBACK_STORE.clear()
    _IN_MEMORY_QUARANTINE.clear()
    yield


@pytest.fixture
def client() -> TestClient:
    """Synchronous test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def valid_bid_payload() -> dict:
    """Section 4.1 compliant test case payload."""
    return {
        "bid_ref": "TEST-BID-001",
        "tender_id": "GEM/2026/B/8034326",
        "bidder": {
            "name": "Sandes Tech Labs Pvt Ltd",
            "declared_category": "STARTUP",
            "country_code": "IN",
            "incorporation_date": "2023-04-01",
            "startup_certificate_number": "DPIIT-TEST-0001",
            "annual_turnover_lakh": [40.0, 120.0, 200.0],
            "years_experience": 2.0,
            "manpower_payroll_percent": 20.0,
            "emd_submitted": True,
            "emd_amount_inr": 117600.0,
            "emd_exemption_claimed": False,
            "office_in_consignee_state": True,
            "documents_submitted": [
                "EXPERIENCE_PROOF",
                "TURNOVER_PROOF",
                "DPIIT_CERTIFICATE",
                "PAYROLL_PROOF",
            ],
            "similar_services": [
                {"contract_value_lakh": 120.0, "client_type": "CENTRAL"}
            ],
        },
        "notes": None,
    }
