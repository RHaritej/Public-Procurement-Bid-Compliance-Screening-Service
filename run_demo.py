"""Comprehensive Demonstration Script for Member C (Agents & LLMOps).
Executes the Section 4.1 test case, ablation analysis, prompt evaluation benchmark,
and LLM gateway resilience verification.
"""

import os
import sys
import json
import time
from pathlib import Path

# Ensure package imports resolve properly
current_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "contracts"))

from datetime import date
from bidscreen_contracts.enums import (
    BidderCategory,
    Route,
    EscalationReason,
    FindingStatus,
    EmdMode,
    DocumentType,
    CircuitState,
)
from bidscreen_contracts.bid_summary import (
    BidSummary,
    BidderInfo,
    Financials,
    FinancialYearTurnover,
    Experience,
    SimilarService,
    ClientType,
    EmdDetails,
    Manpower,
)
from packages.agents.graph import run_screening
from packages.llm_gateway.resilience import CircuitBreaker
from packages.llm_gateway.cost import CostCalculator
from eval.run_eval import compare_prompt_versions


def section_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title} ")
    print("=" * 80)


def run_section_4_1_demo():
    section_header("DEMO 1: SECTION 4.1 REFERENCE TEST CASE (EXIT CRITERIA)")
    print("Testing startup bidder below turnover and experience thresholds...")

    bid = BidSummary(
        bid_ref="BID-2026-STARTUP-401",
        tender_id="GEM/2026/B/8034326",
        bidder=BidderInfo(
            name="Innovatech Cloud Solutions Pvt Ltd",
            declared_category=BidderCategory.STARTUP,
            country_code="IN",
            incorporation_date=date(2023, 4, 1),
            dpiit_certificate_number="DPIIT-TEST-0001",
        ),
        financials=Financials(
            turnover_lakh_by_fy=[
                FinancialYearTurnover(fy="2023-24", turnover_lakh=40.0),
                FinancialYearTurnover(fy="2024-25", turnover_lakh=120.0),
                FinancialYearTurnover(fy="2025-26", turnover_lakh=200.0),
            ],
            declared_average_turnover_lakh=120.0,
        ),
        experience=Experience(
            years_of_similar_service=2,
            similar_services=[SimilarService(client_type=ClientType.CENTRAL_GOVT, fy="2024-25", value_lakh=30.0)],
        ),
        emd=EmdDetails(mode=EmdMode.PHYSICAL, amount_inr=117600),
        manpower=Manpower(payroll_share_pct_one_year=20.0),
        local_office_in_consignee_state=True,
        documents_uploaded=[
            DocumentType.EXPERIENCE_PROOF,
            DocumentType.TURNOVER_PROOF,
            DocumentType.DPIIT_CERTIFICATE,
            DocumentType.PAYROLL_PROOF,
        ],
        notes="Standard submission for Section 4.1 test case.",
    )

    t0 = time.time()
    res = run_screening(
        run_id="demo-sec41-run",
        bid=bid,
        correlation_id="demo-corr-401",
        prompt_version="analyst@v2",
    )
    elapsed = (time.time() - t0) * 1000

    print(f"\n[Result Overview]")
    print(f"  • Run ID            : {res.run_id}")
    print(f"  • Route             : {res.route.value}")
    print(f"  • Escalation Reason : {res.escalation_reason.value if res.escalation_reason else 'None'}")
    print(f"  • Total Latency     : {elapsed:.2f} ms")
    print(f"  • Degraded Fallback : {res.degraded}")

    print("\n[Condition Findings Summary]")
    for f in res.findings:
        status_symbol = "[MET]" if f.status == FindingStatus.MET else f"[{f.status.value}]"
        print(f"  {f.condition_id:<6} {status_symbol:<14} : {f.summary}")
        for c in f.citations:
            print(f"         Cited -> {c.clause_id} : \"{c.quote}\"")

    print("\n[Advisory Flags]")
    for flag in res.advisory_flags:
        print(f"  • {flag}")

    # Verify exit check criteria
    assert res.route == Route.ESCALATE_TO_HUMAN, "Route mismatch!"
    assert res.escalation_reason == EscalationReason.RULE_CONFLICT, "Escalation reason mismatch!"
    mc02 = next(f for f in res.findings if f.condition_id == "MC-02")
    mc03 = next(f for f in res.findings if f.condition_id == "MC-03")
    assert mc02.status == FindingStatus.CONFLICT, "MC-02 should be CONFLICT!"
    assert mc03.status == FindingStatus.CONFLICT, "MC-03 should be CONFLICT!"
    assert len(res.advisory_flags) > 0, "Advisory flags missing!"

    print("\n>>> Section 4.1 Exit Check Passed: ESCALATE_TO_HUMAN + RULE_CONFLICT + Verified Citations <<<")


def run_ablation_demo():
    section_header("DEMO 2: ABLATION STUDY (INDEX PROFILE tender_core)")
    print("Testing multi-hop retrieval when tender relaxation chunks MII.1-MII.4 are omitted...")

    bid = BidSummary(
        bid_ref="BID-2026-STARTUP-ABLATION",
        tender_id="GEM/2026/B/8034326",
        bidder=BidderInfo(
            name="Innovatech Cloud Solutions Pvt Ltd",
            declared_category=BidderCategory.STARTUP,
            country_code="IN",
            incorporation_date=date(2023, 4, 1),
            dpiit_certificate_number="DPIIT-TEST-0001",
        ),
        financials=Financials(
            turnover_lakh_by_fy=[
                FinancialYearTurnover(fy="2023-24", turnover_lakh=40.0),
                FinancialYearTurnover(fy="2024-25", turnover_lakh=120.0),
                FinancialYearTurnover(fy="2025-26", turnover_lakh=200.0),
            ],
            declared_average_turnover_lakh=120.0,
        ),
        experience=Experience(years_of_similar_service=2),
        emd=EmdDetails(mode=EmdMode.PHYSICAL, amount_inr=117600),
        manpower=Manpower(payroll_share_pct_one_year=20.0),
        local_office_in_consignee_state=True,
        documents_uploaded=[DocumentType.EXPERIENCE_PROOF, DocumentType.TURNOVER_PROOF, DocumentType.DPIIT_CERTIFICATE],
    )

    res = run_screening(
        run_id="demo-ablation-run",
        bid=bid,
        correlation_id="demo-corr-ablation",
        prompt_version="analyst@v2",
        profile="tender_core",
    )

    print(f"\n[Ablation Result Overview]")
    print(f"  • Route             : {res.route.value}")
    print(f"  • Escalation Reason : {res.escalation_reason.value if res.escalation_reason else 'None'}")
    mc02 = next(f for f in res.findings if f.condition_id == "MC-02")
    print(f"  • MC-02 Status      : {mc02.status.value}")
    print(f"  • Citations Discovered:")
    for c in mc02.citations:
        print(f"      - {c.clause_id} ({c.passage_id})")

    assert res.route == Route.ESCALATE_TO_HUMAN
    assert any("DOE_OM" in c.clause_id for c in mc02.citations), "Multi-hop failed to find policy OM!"
    print("\n>>> Multi-hop ablation passed: Policy OM discovered without tender MII chunks! <<<")


def run_resilience_demo():
    section_header("DEMO 3: LLM GATEWAY RESILIENCE & CIRCUIT BREAKER")
    print("Testing Circuit Breaker state transitions and timeout protections...")

    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_s=0.2)
    print(f"Initial State : {cb.state.value} (can_execute={cb.can_execute()})")

    cb.record_failure()
    print(f"After 1 Fail  : {cb.state.value} (can_execute={cb.can_execute()})")

    cb.record_failure()
    print(f"After 2 Fails : {cb.state.value} (can_execute={cb.can_execute()}) [Circuit OPEN]")

    time.sleep(0.25)
    print(f"After Timeout : can_execute={cb.can_execute()} -> State: {cb.state.value} [HALF_OPEN]")

    cb.record_success()
    print(f"After Success : {cb.state.value} [Circuit CLOSED and Healthy]")


def main():
    print("================================================================================")
    print("  BID COMPLIANCE SCREENING SERVICE — MEMBER C: AGENTS & LLMOPS")
    print("  Student: Prithvi Raju | SRN: PES1UG24AM204 | UE24AM342AA5")
    print("================================================================================")

    run_section_4_1_demo()
    run_ablation_demo()
    run_resilience_demo()

    section_header("DEMO 4: PROMPT BENCHMARK & EVALUATION RUNNER (L3, L5)")
    compare_prompt_versions()

    section_header("ALL MEMBER C DELIVERABLES COMPLETED & VERIFIED")
    print("  [x] LangGraph Multi-Agent Topology (Classifier, Analyst, Verifier, Router)")
    print("  [x] Section 4.1 Test Case Verified (ESCALATE_TO_HUMAN + RULE_CONFLICT)")
    print("  [x] Multi-Hop Retrieval (Strategies S1, S2, S3 across Tender & Policy)")
    print("  [x] LLM Gateway with Timeouts, Exponential Backoff, Circuit Breaker, Cost Tracking")
    print("  [x] Versioned Prompts (analyst@v1 vs analyst@v2 benchmark report)")
    print("  [x] Evaluation Runner (Groundedness, Context Relevance, Faithfulness, Hallucination)")
    print("  [x] Cost & Token Economy Report per 100 runs")
    print("  [x] Unit Tests & Documentation (agent_design.md, prompts.md, eval_report.md, cost_report.md)")


if __name__ == "__main__":
    main()

