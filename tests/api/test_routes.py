"""Integration tests for FastAPI screening, polling, and feedback endpoints."""

from __future__ import annotations

import copy
from fastapi.testclient import TestClient

from bidscreen_contracts.enums import Route, RunStatus
try:
    from services.api.routes.runs import RUNS_STORE
except ImportError:
    from routes.runs import RUNS_STORE


def test_health_check(client: TestClient):
    """GET /health must return healthy status with tender_id."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["tender_id"] == "GEM/2026/B/8034326"


def test_submit_valid_screening(client: TestClient, valid_bid_payload):
    """POST /v1/screenings with valid bid returns 202 Accepted and QUEUED status."""
    resp = client.post(
        "/v1/screenings",
        json=valid_bid_payload,
        headers={"X-Client-Id": "test-client", "X-Correlation-ID": "test-corr-123"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "run_id" in data
    assert data["status"] == RunStatus.QUEUED
    assert data["correlation_id"] == "test-corr-123"
    assert resp.headers.get("X-Correlation-ID") == "test-corr-123"


def test_submit_invalid_payload_quarantines(client: TestClient, valid_bid_payload):
    """POST /v1/screenings with invalid bid returns 422 and assigns a quarantine_id."""
    invalid_payload = copy.deepcopy(valid_bid_payload)
    invalid_payload["tender_id"] = "WRONG_TENDER"

    resp = client.post("/v1/screenings", json=invalid_payload)
    assert resp.status_code == 422
    data = resp.json()
    assert "quarantine_id" in data
    assert data["quarantine_id"].startswith("Q-")
    assert len(data["errors"]) > 0


def test_get_screening_run(client: TestClient, valid_bid_payload):
    """GET /v1/screenings/{run_id} returns run status."""
    # Submit first
    post_resp = client.post("/v1/screenings", json=valid_bid_payload)
    run_id = post_resp.json()["run_id"]

    # Poll status
    get_resp = client.get(f"/v1/screenings/{run_id}")
    assert get_resp.status_code == 200
    run_data = get_resp.json()
    assert run_data["run_id"] == run_id
    assert run_data["status"] == RunStatus.QUEUED


def test_get_nonexistent_run(client: TestClient):
    """GET /v1/screenings/{nonexistent} returns 404."""
    resp = client.get("/v1/screenings/nonexistent-uuid")
    assert resp.status_code == 404


def test_submit_feedback_and_summary(client: TestClient, valid_bid_payload):
    """POST /v1/screenings/{run_id}/feedback records human validation feedback."""
    post_resp = client.post("/v1/screenings", json=valid_bid_payload)
    run_id = post_resp.json()["run_id"]

    # Submit feedback
    fb_resp = client.post(
        f"/v1/screenings/{run_id}/feedback",
        json={"satisfactory": True, "reason": "Accurate finding"},
    )
    assert fb_resp.status_code == 200
    assert fb_resp.json()["status"] == "recorded"

    # Verify summary
    sum_resp = client.get("/v1/feedback/summary")
    assert sum_resp.status_code == 200
    summary = sum_resp.json()
    assert summary["total_feedback_count"] == 1
    assert summary["satisfactory_count"] == 1
    assert summary["satisfaction_rate_percent"] == 100.0


def test_run_trace_endpoint(client: TestClient, valid_bid_payload):
    """GET /v1/runs/{run_id}/trace reconstructs multi-agent execution steps."""
    post_resp = client.post("/v1/screenings", json=valid_bid_payload)
    run_id = post_resp.json()["run_id"]

    trace_resp = client.get(f"/v1/runs/{run_id}/trace")
    assert trace_resp.status_code == 200
    trace = trace_resp.json()
    assert trace["run_id"] == run_id
    assert "steps" in trace
    assert len(trace["steps"]) > 0
