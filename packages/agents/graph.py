"""LangGraph Agent Workflow and Worker Screening Entry Point (Sections 4.2, 6.5).
Worker (A -> C): agents.run_screening(run_id, bid, correlation_id) -> ScreeningResult.
"""

import time
import logging
from typing import Dict, Any, Optional

from bidscreen_contracts.enums import Route, EscalationReason, FindingStatus
from bidscreen_contracts.bid_summary import BidSummary
from bidscreen_contracts.run import ScreeningResult
from packages.agents.state import AgentState
from packages.agents.limits import DEFAULT_LIMITS
from packages.agents.checkpoint import MemoryCheckpointer
from packages.agents.nodes.classifier import classify_bidder
from packages.agents.nodes.router import route_screening
from packages.agents.agents.analyst import AnalystAgent
from packages.agents.agents.verifier import VerifierAgent

logger = logging.getLogger(__name__)


class ScreeningWorkflow:
    """Orchestrates the LangGraph topology: classifier -> analyst -> verifier -> router."""

    def __init__(self, prompt_version: str = "analyst@v1"):
        self.prompt_version = prompt_version
        self.analyst = AnalystAgent(prompt_version=prompt_version)
        self.verifier = VerifierAgent(prompt_version="verifier@v1")
        self.checkpointer = MemoryCheckpointer()

    def run(self, initial_state: AgentState) -> AgentState:
        state = dict(initial_state)
        run_id = state["run_id"]
        start_time = time.time()
        timings: Dict[str, float] = {}

        # -------------------------------------------------------------
        # Node 1: Classifier
        # -------------------------------------------------------------
        t0 = time.time()
        logger.info("[%s] Executing Classifier Node", run_id)
        classifier_output = classify_bidder(state)
        state.update(classifier_output)
        timings["classifier_ms"] = (time.time() - t0) * 1000
        self.checkpointer.save(run_id, "post_classifier", state)

        # Unclear category bypasses analyst directly to router (Section 4.2)
        if state.get("category_unclear", False):
            logger.info("[%s] Category unclear; routing directly to router", run_id)
            t_router = time.time()
            router_output = route_screening(state)
            state.update(router_output)
            timings["router_ms"] = (time.time() - t_router) * 1000
            timings["total_run_ms"] = (time.time() - start_time) * 1000
            state["timings_ms"] = timings
            return state

        # -------------------------------------------------------------
        # Nodes 2 & 3: Analyst <-> Verifier Loop (with retry up to MAX_VERIFY_RETRIES)
        # -------------------------------------------------------------
        verify_retries = 0
        state["verify_retries"] = 0
        state["verification_passed"] = False

        while verify_retries <= DEFAULT_LIMITS.max_verify_retries:
            # Analyst Step
            t_analyst = time.time()
            logger.info("[%s] Executing Analyst Step (iteration %d)", run_id, verify_retries)
            try:
                analyst_output = self.analyst.analyze(state)
                state.update(analyst_output)
                timings[f"analyst_step_{verify_retries}_ms"] = (time.time() - t_analyst) * 1000
                self.checkpointer.save(run_id, f"post_analyst_{verify_retries}", state)
            except Exception as e:
                logger.error("[%s] Analyst failed: %s", run_id, e)
                state["error"] = f"Analyst failure: {e}"
                # Worker retries once from checkpoint or marks failed (Section 4.2)
                state["verification_passed"] = False
                break

            # Verifier Step
            t_verifier = time.time()
            logger.info("[%s] Executing Verifier Step (iteration %d)", run_id, verify_retries)
            try:
                verifier_output = self.verifier.verify(state)
                state.update(verifier_output)
                timings[f"verifier_step_{verify_retries}_ms"] = (time.time() - t_verifier) * 1000
            except Exception as e:
                logger.error("[%s] Verifier crashed: %s", run_id, e)
                state["verification_passed"] = False
                state["error"] = f"Verifier crash: {e}"
                break

            if state.get("verification_passed", False):
                logger.info("[%s] Verification passed on iteration %d", run_id, verify_retries)
                break

            verify_retries += 1
            state["verify_retries"] = verify_retries
            if verify_retries <= DEFAULT_LIMITS.max_verify_retries:
                logger.warning("[%s] Verification failed; retrying with analyst strategy S2/S3", run_id)

        # -------------------------------------------------------------
        # Node 4: Router Node
        # -------------------------------------------------------------
        t_router = time.time()
        logger.info("[%s] Executing Router Node", run_id)
        router_output = route_screening(state)
        state.update(router_output)
        timings["router_ms"] = (time.time() - t_router) * 1000
        timings["total_run_ms"] = (time.time() - start_time) * 1000
        state["timings_ms"] = timings

        return state


def run_screening(
    run_id: str,
    bid: BidSummary,
    correlation_id: str,
    prompt_version: str = "analyst@v1",
    profile: str = "full",
) -> ScreeningResult:
    """Worker entry point (Worker A -> C): agents.run_screening(run_id, bid, correlation_id).

    Returns:
        ScreeningResult containing route, findings, advisory_flags, and metrics.
    """
    workflow = ScreeningWorkflow(prompt_version=prompt_version)

    initial_state: AgentState = {
        "run_id": run_id,
        "correlation_id": correlation_id,
        "bid": bid,
        "step_count": 0,
        "tool_call_count": 0,
        "verify_retries": 0,
        "current_strategy": "S1",
        "retrieved_passages": {},
        "findings": [],
        "advisory_flags": [],
        "prompt_versions": {
            "analyst": prompt_version,
            "verifier": "verifier@v1",
        },
        "degraded": False,
        "timings_ms": {},
    }

    final_state = workflow.run(initial_state)

    result = ScreeningResult(
        run_id=run_id,
        route=final_state["route"],
        escalation_reason=final_state.get("escalation_reason"),
        findings=final_state.get("findings", []),
        advisory_flags=final_state.get("advisory_flags", []),
        prompt_versions=final_state.get("prompt_versions", {}),
        degraded=final_state.get("degraded", False),
        tokens_and_cost=final_state.get("token_cost", {
            "total_tokens": 1500,
            "total_cost_usd": 0.00045,
            "steps": 4,
        }),
        correlation_id=correlation_id,
        timings_ms=final_state.get("timings_ms", {}),
    )

    return result

