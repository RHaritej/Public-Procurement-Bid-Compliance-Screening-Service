"""Unit tests for Deterministic Router Table (Section 4.3)."""

from bidscreen_contracts.enums import Route, EscalationReason, FindingStatus
from bidscreen_contracts.finding import Finding
from packages.agents.nodes.router import determine_route
from packages.agents.state import AgentState


def test_router_conflict_escalates():
    state: AgentState = {
        "findings": [Finding(condition_id="MC-02", status=FindingStatus.CONFLICT, summary="Conflict found")],
        "verification_passed": True,
    }
    route, reason = determine_route(state)
    assert route == Route.ESCALATE_TO_HUMAN
    assert reason == EscalationReason.RULE_CONFLICT


def test_router_category_unclear_escalates():
    state: AgentState = {
        "category_unclear": True,
        "verification_passed": True,
        "findings": [],
    }
    route, reason = determine_route(state)
    assert route == Route.ESCALATE_TO_HUMAN
    assert reason == EscalationReason.CATEGORY_UNCLEAR


def test_router_unmet_rejects():
    state: AgentState = {
        "findings": [Finding(condition_id="MC-01", status=FindingStatus.UNMET, summary="EMD missing")],
        "verification_passed": True,
    }
    route, reason = determine_route(state)
    assert route == Route.REJECT_WITH_CITED_CONDITION
    assert reason is None


def test_router_not_verifiable_seeks_clarification():
    state: AgentState = {
        "findings": [Finding(condition_id="MC-06", status=FindingStatus.NOT_VERIFIABLE, summary="Missing doc")],
        "verification_passed": True,
    }
    route, reason = determine_route(state)
    assert route == Route.SEEK_CLARIFICATION
    assert reason is None


def test_router_all_met_passes():
    state: AgentState = {
        "findings": [Finding(condition_id="MC-01", status=FindingStatus.MET, summary="All good")],
        "verification_passed": True,
    }
    route, reason = determine_route(state)
    assert route == Route.PASS_TO_TECHNICAL_EVALUATION
    assert reason is None

