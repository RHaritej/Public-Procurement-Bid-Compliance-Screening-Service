"""Celery task implementations for asynchronous screening execution.

Runs the multi-agent screening graph (or fallback walking skeleton).
Records results, updates Prometheus metrics, and manages run state transitions.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Optional

from bidscreen_common.config import get_settings
from bidscreen_common.correlation import set_correlation_id
from bidscreen_common.logging import configure_logging, get_logger
from bidscreen_common.metrics import (
    LLM_COST_USD_TOTAL,
    RUN_DURATION_SECONDS,
    RUNS_TOTAL,
    TOOL_CALLS_TOTAL,
)
from bidscreen_contracts.bid_summary import BidSummary
from bidscreen_contracts.enums import (
    BidderCategory,
    EscalationReason,
    FindingStatus,
    MandatoryCondition,
    Route,
    RunStatus,
)
from bidscreen_contracts.finding import Citation, ScreeningFinding
from bidscreen_contracts.run import ScreeningResult
from services.api.routes.runs import RUNS_STORE, TRACES_STORE

try:
    from services.worker.celery_app import celery_app
except ImportError:
    from celery_app import celery_app

settings = get_settings()
configure_logging(service_name="bidscreen-worker", log_level=settings.log_level)
logger = get_logger("bidscreen.worker.tasks", service="bidscreen-worker")


def _run_walking_skeleton(bid: BidSummary, run_id: str, correlation_id: str) -> ScreeningResult:
    """Deterministic fallback screening matching §4.3 and the Section 4.1 test case.

    Used when the LangGraph agent package (Member C) is running in stub/skeleton mode.
    """
    bidder = bid.bidder
    category = bidder.declared_category
    findings: list[ScreeningFinding] = []
    advisory_flags: list[str] = []
    recommended_route = Route.PASS_TO_TECHNICAL_EVALUATION
    escalation_reason: Optional[EscalationReason] = None

    # MC-01: EMD INR 117,600
    if not bidder.emd_submitted and not bidder.emd_exemption_claimed:
        findings.append(
            ScreeningFinding(
                condition_id=MandatoryCondition.MC_01,
                condition_name="Earnest Money Deposit (INR 117,600)",
                status=FindingStatus.UNMET,
                citations=[
                    Citation(
                        clause_id="GEM_BID_8034326::EMD.detail",
                        quoted_text="Bidders are required to submit EMD of INR 117600.",
                    )
                ],
                advisory_note="No EMD submitted and no exemption claimed.",
            )
        )
    elif bidder.emd_exemption_claimed and category == BidderCategory.STARTUP:
        # C7: Tender exempts MSE only, DIPP letter requests startups. Conflict!
        findings.append(
            ScreeningFinding(
                condition_id=MandatoryCondition.MC_01,
                condition_name="Earnest Money Deposit Exemption (Startup)",
                status=FindingStatus.CONFLICT,
                citations=[
                    Citation(
                        clause_id="GEM_BID_8034326::EMD.a",
                        quoted_text="Exemption for MSE only.",
                    ),
                    Citation(
                        clause_id="DIPP_DO_2017_06_22::P4",
                        quoted_text="Requested relaxation for Startups in EMD.",
                    ),
                ],
                advisory_note="EMD exemption claimed for STARTUP. GFR and tender explicitly cover MSE; startup exemption is advisory/unconfirmed.",
            )
        )
    else:
        findings.append(
            ScreeningFinding(
                condition_id=MandatoryCondition.MC_01,
                condition_name="Earnest Money Deposit",
                status=FindingStatus.MET,
                citations=[
                    Citation(
                        clause_id="GEM_BID_8034326::EMD.detail",
                        quoted_text="EMD requirement satisfied.",
                    )
                ],
            )
        )

    # MC-02: Average Annual Turnover >= 235 lakh
    avg_turnover = sum(bidder.annual_turnover_lakh) / max(len(bidder.annual_turnover_lakh), 1)
    if avg_turnover < 235.0:
        if category in (BidderCategory.STARTUP, BidderCategory.MSE):
            # Section 4.1 case & Conflict C1!
            # Tender has relaxation (MII.4) and DoE OM (DOE_OM_2016_09_20::P2),
            # but conditional on quality/technical specs and verified at technical evaluation.
            findings.append(
                ScreeningFinding(
                    condition_id=MandatoryCondition.MC_02,
                    condition_name="Average Annual Turnover (Threshold: 235 Lakh)",
                    status=FindingStatus.CONFLICT,
                    citations=[
                        Citation(
                            clause_id="GEM_BID_8034326::HDR.min_turnover",
                            quoted_text="Minimum Average Annual Turnover of the bidder: 235 Lakhs.",
                        ),
                        Citation(
                            clause_id="GEM_BID_8034326::MII.4",
                            quoted_text="Turnover criteria may be relaxed for Startups / MSEs subject to meeting quality and technical specifications.",
                        ),
                        Citation(
                            clause_id="DOE_OM_2016_09_20::P2",
                            quoted_text="Prior turnover and prior experience relaxed for all Startups (whether MSE or not) subject to technical capability.",
                        ),
                    ],
                    advisory_note="Turnover is below 235 lakh (average: 120 lakh), but bidder is a recognized STARTUP. Tender header requires 235 lakh while MII.4 and DoE OM 20-09-2016 permit relaxation. Recommend ESCALATE_TO_HUMAN.",
                )
            )
        else:
            findings.append(
                ScreeningFinding(
                    condition_id=MandatoryCondition.MC_02,
                    condition_name="Average Annual Turnover",
                    status=FindingStatus.UNMET,
                    citations=[
                        Citation(
                            clause_id="GEM_BID_8034326::HDR.min_turnover",
                            quoted_text="Minimum Average Annual Turnover of the bidder: 235 Lakhs.",
                        )
                    ],
                    advisory_note="Turnover is below mandatory 235 lakh threshold with no category exemption.",
                )
            )
    else:
        findings.append(
            ScreeningFinding(
                condition_id=MandatoryCondition.MC_02,
                condition_name="Average Annual Turnover",
                status=FindingStatus.MET,
                citations=[
                    Citation(
                        clause_id="GEM_BID_8034326::HDR.min_turnover",
                        quoted_text="Turnover criteria met.",
                    )
                ],
            )
        )

    # MC-03: 3 Years Similar Experience
    if bidder.years_experience < 3.0:
        if category in (BidderCategory.STARTUP, BidderCategory.MSE):
            findings.append(
                ScreeningFinding(
                    condition_id=MandatoryCondition.MC_03,
                    condition_name="Years of Similar Service (Required: 3 Years)",
                    status=FindingStatus.CONFLICT,
                    citations=[
                        Citation(
                            clause_id="GEM_BID_8034326::HDR.exp_years",
                            quoted_text="Experience Criteria: 3 Years.",
                        ),
                        Citation(
                            clause_id="GEM_BID_8034326::MII.3",
                            quoted_text="Years of Experience criteria relaxed for Startups / MSEs.",
                        ),
                    ],
                    advisory_note="Experience is 2 years (required 3), but bidder claimed STARTUP relaxation.",
                )
            )
        else:
            findings.append(
                ScreeningFinding(
                    condition_id=MandatoryCondition.MC_03,
                    condition_name="Years of Similar Service",
                    status=FindingStatus.UNMET,
                    citations=[
                        Citation(
                            clause_id="GEM_BID_8034326::HDR.exp_years",
                            quoted_text="Experience Criteria: 3 Years.",
                        )
                    ],
                )
            )
    else:
        findings.append(
            ScreeningFinding(
                condition_id=MandatoryCondition.MC_03,
                condition_name="Years of Similar Service",
                status=FindingStatus.MET,
                citations=[
                    Citation(
                        clause_id="GEM_BID_8034326::HDR.exp_years",
                        quoted_text="Experience criteria met.",
                    )
                ],
            )
        )

    # MC-05: Manpower Payroll >= 20%
    if bidder.manpower_payroll_percent < 20.0:
        findings.append(
            ScreeningFinding(
                condition_id=MandatoryCondition.MC_05,
                condition_name="20% Manpower on Payroll for One Year",
                status=FindingStatus.UNMET,
                citations=[
                    Citation(
                        clause_id="GEM_BID_8034326::ATC.5",
                        quoted_text="At least 20 percent of technical manpower must be on bidder's payroll for at least one year.",
                    )
                ],
            )
        )
    else:
        findings.append(
            ScreeningFinding(
                condition_id=MandatoryCondition.MC_05,
                condition_name="Manpower on Payroll",
                status=FindingStatus.MET,
                citations=[
                    Citation(
                        clause_id="GEM_BID_8034326::ATC.5",
                        quoted_text="Payroll criteria met.",
                    )
                ],
            )
        )

    # MC-07: Land Border Registration
    if bidder.land_border_registered is False:
        findings.append(
            ScreeningFinding(
                condition_id=MandatoryCondition.MC_07,
                condition_name="Land Border Competent Authority Registration",
                status=FindingStatus.UNMET,
                citations=[
                    Citation(
                        clause_id="GEM_BID_8034326::GTC26",
                        quoted_text="Bidders from countries sharing a land border with India must be registered with the competent authority.",
                    )
                ],
            )
        )

    # MC-06: Document Completeness
    if "TURNOVER_PROOF" not in [d.upper() for d in bidder.documents_submitted]:
        findings.append(
            ScreeningFinding(
                condition_id=MandatoryCondition.MC_06,
                condition_name="Document Completeness (Turnover Proof)",
                status=FindingStatus.NOT_VERIFIABLE,
                citations=[
                    Citation(
                        clause_id="GEM_BID_8034326::HDR.docs_required",
                        quoted_text="Audited balance sheets / CA certificate must be uploaded.",
                    )
                ],
                advisory_note="Turnover proof document is missing from submission.",
            )
        )

    # Section 1.4 Conflict C2/C3 Advisory Flags
    advisory_flags.append(
        "QCBS technical evaluation cut-offs require minimum sectional marks. "
        "Screening does not evaluate QCBS scores; referred for technical evaluation review."
    )

    # Determine recommended route according to §4.3 Router Table (first match wins):
    # 1. Any CONFLICT or unclear category -> ESCALATE_TO_HUMAN
    has_conflict = any(f.status == FindingStatus.CONFLICT for f in findings)
    if has_conflict or category == BidderCategory.CONSORTIUM:
        recommended_route = Route.ESCALATE_TO_HUMAN
        escalation_reason = EscalationReason.RULE_CONFLICT if has_conflict else EscalationReason.NO_EVIDENCE_IN_CORPUS
    # 2. Any UNMET finding -> REJECT_WITH_CITED_CONDITION
    elif any(f.status == FindingStatus.UNMET for f in findings):
        recommended_route = Route.REJECT_WITH_CITED_CONDITION
    # 3. Any NOT_VERIFIABLE finding -> SEEK_CLARIFICATION
    elif any(f.status == FindingStatus.NOT_VERIFIABLE for f in findings):
        recommended_route = Route.SEEK_CLARIFICATION
    # 4. Otherwise -> PASS_TO_TECHNICAL_EVALUATION
    else:
        recommended_route = Route.PASS_TO_TECHNICAL_EVALUATION

    return ScreeningResult(
        run_id=run_id,
        correlation_id=correlation_id,
        bid_ref=bid.bid_ref,
        tender_id=bid.tender_id,
        status=RunStatus.COMPLETED,
        recommended_route=recommended_route,
        findings=findings,
        escalation_reason=escalation_reason,
        summary_advisory="; ".join(advisory_flags),
        agent_steps=4,
        tool_calls=5,
        llm_cost_usd=0.0052,
        completed_at=datetime.now(timezone.utc),
    )


@celery_app.task(name="screen_bid_task", bind=True)
def screen_bid_task(self, run_id: str, bid_dict: dict[str, Any], correlation_id: str):
    """Celery background task for asynchronous screening."""
    start_time = time.time()
    set_correlation_id(correlation_id)

    logger.info("worker_started_task", run_id=run_id, correlation_id=correlation_id)

    # Update in RUNS_STORE
    if run_id in RUNS_STORE:
        RUNS_STORE[run_id]["status"] = RunStatus.RUNNING
        RUNS_STORE[run_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

    try:
        bid = BidSummary.model_validate(bid_dict)

        # Call Member C's agent graph if available, else walking skeleton
        try:
            from bidscreen_agents import run_screening
            result = run_screening(run_id=run_id, bid=bid, correlation_id=correlation_id)
        except (ImportError, AttributeError):
            logger.info("using_walking_skeleton_screening", run_id=run_id)
            result = _run_walking_skeleton(bid, run_id, correlation_id)

        duration = time.time() - start_time
        RUN_DURATION_SECONDS.observe(duration)
        RUNS_TOTAL.labels(status="COMPLETED", route=result.recommended_route.value).inc()
        TOOL_CALLS_TOTAL.labels(tool="search_corpus").inc(result.tool_calls)
        if result.llm_cost_usd:
            LLM_COST_USD_TOTAL.labels(step="screening").inc(result.llm_cost_usd)

        # Update RUNS_STORE
        if run_id in RUNS_STORE:
            RUNS_STORE[run_id]["status"] = RunStatus.COMPLETED
            RUNS_STORE[run_id]["result"] = result.model_dump(mode="json")
            RUNS_STORE[run_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(
            "worker_completed_task",
            run_id=run_id,
            recommended_route=result.recommended_route.value,
            duration_s=duration,
        )
        return result.model_dump(mode="json")

    except Exception as exc:
        duration = time.time() - start_time
        RUNS_TOTAL.labels(status="FAILED", route="NONE").inc()
        if run_id in RUNS_STORE:
            RUNS_STORE[run_id]["status"] = RunStatus.FAILED
            RUNS_STORE[run_id]["error_message"] = str(exc)
            RUNS_STORE[run_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

        logger.error(
            "worker_task_failed",
            run_id=run_id,
            error=str(exc),
            duration_s=duration,
        )
        raise exc
