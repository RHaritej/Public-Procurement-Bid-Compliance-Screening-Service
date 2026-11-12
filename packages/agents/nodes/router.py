"""Router Node (Requirement F7, Section 4.3).
Deterministic router table implementing strict priority rules (first match wins).
"""

from typing import Dict, Any, Tuple, Optional
from bidscreen_contracts.enums import Route, EscalationReason, FindingStatus, BidderCategory
from bidscreen_contracts.finding import Finding
from packages.agents.state import AgentState


def determine_route(state: AgentState) -> Tuple[Route, Optional[EscalationReason]]:
    """Evaluates the state against the deterministic router table in Section 4.3.

    Returns:
        Tuple of (Route, Optional[EscalationReason])
    """
    category_unclear = state.get("category_unclear", False)
    verification_passed = state.get("verification_passed", True)
    findings = state.get("findings", [])
    error = state.get("error")
    bid = state.get("bid")
    bidder_cat = bid.bidder.declared_category if bid else None

    # Rule 1a: Category unclear -> ESCALATE_TO_HUMAN (CATEGORY_UNCLEAR)
    if category_unclear:
        return Route.ESCALATE_TO_HUMAN, EscalationReason.CATEGORY_UNCLEAR

    # Rule 1b: Any finding CONFLICT -> ESCALATE_TO_HUMAN
    conflict_findings = [f for f in findings if f.status == FindingStatus.CONFLICT]
    if conflict_findings:
        # Check specific scenario S12: Consortium bidder with corpus silent
        if bidder_cat == BidderCategory.CONSORTIUM:
            return Route.ESCALATE_TO_HUMAN, EscalationReason.NO_EVIDENCE_IN_CORPUS
        return Route.ESCALATE_TO_HUMAN, EscalationReason.RULE_CONFLICT

    # Rule 2: Failures after retries, guardrails, budget, provider
    if not verification_passed:
        return Route.ESCALATE_TO_HUMAN, EscalationReason.VERIFICATION_FAILED

    if error:
        if "guardrail" in error.lower():
            return Route.ESCALATE_TO_HUMAN, EscalationReason.GUARDRAIL_BLOCK
        if "budget" in error.lower():
            return Route.ESCALATE_TO_HUMAN, EscalationReason.BUDGET_EXHAUSTED
        if "provider" in error.lower() or "unavailable" in error.lower():
            return Route.ESCALATE_TO_HUMAN, EscalationReason.PROVIDER_UNAVAILABLE
        return Route.ESCALATE_TO_HUMAN, EscalationReason.VERIFICATION_FAILED

    # Rule 3: Any UNMET finding with no applicable relaxation -> REJECT_WITH_CITED_CONDITION
    unmet_findings = [f for f in findings if f.status == FindingStatus.UNMET]
    if unmet_findings:
        return Route.REJECT_WITH_CITED_CONDITION, None

    # Rule 4: Any NOT_VERIFIABLE finding (evidence missing) -> SEEK_CLARIFICATION
    not_verifiable_findings = [f for f in findings if f.status == FindingStatus.NOT_VERIFIABLE]
    if not_verifiable_findings:
        return Route.SEEK_CLARIFICATION, None

    # Rule 5: Otherwise -> PASS_TO_TECHNICAL_EVALUATION
    return Route.PASS_TO_TECHNICAL_EVALUATION, None


def route_screening(state: AgentState) -> Dict[str, Any]:
    """Router node wrapper for LangGraph."""
    route, escalation_reason = determine_route(state)
    step_count = state.get("step_count", 0) + 1

    return {
        "step_count": step_count,
        "route": route,
        "escalation_reason": escalation_reason,
    }

