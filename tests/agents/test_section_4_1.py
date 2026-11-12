"""Golden Test Case: Section 4.1 Request on Corpus.
Reference: Section 2 and Section 7 Exit Criteria.
"Done when: the section 4.1 request returns ESCALATE_TO_HUMAN with both citations and the verifier passes."
"""

from datetime import date
from bidscreen_contracts.enums import BidderCategory, Route, EscalationReason, FindingStatus, EmdMode, DocumentType
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


def build_section_4_1_request() -> BidSummary:
    """Constructs the exact Section 4.1 test request."""
    return BidSummary(
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
            years_of_similar_service=2,  # required 3
            similar_services=[
                SimilarService(client_type=ClientType.CENTRAL_GOVT, fy="2024-25", value_lakh=30.0)
            ],
        ),
        emd=EmdDetails(
            mode=EmdMode.PHYSICAL,
            amount_inr=117600,
        ),
        manpower=Manpower(
            payroll_share_pct_one_year=20.0,
        ),
        local_office_in_consignee_state=True,
        documents_uploaded=[
            DocumentType.EXPERIENCE_PROOF,
            DocumentType.TURNOVER_PROOF,
            DocumentType.DPIIT_CERTIFICATE,
            DocumentType.PAYROLL_PROOF,
        ],
        notes="Standard bid response submission.",
    )


def test_section_4_1_reference_case():
    """Validates the section 4.1 exit criteria."""
    bid = build_section_4_1_request()
    result = run_screening(
        run_id="run-test-sec41",
        bid=bid,
        correlation_id="corr-sec41-001",
        prompt_version="analyst@v2",
    )

    # 1. Expected Route and Escalation Reason
    assert result.route == Route.ESCALATE_TO_HUMAN, f"Expected ESCALATE_TO_HUMAN, got {result.route}"
    assert result.escalation_reason == EscalationReason.RULE_CONFLICT, f"Expected RULE_CONFLICT, got {result.escalation_reason}"

    # 2. MC-02 (turnover) must be CONFLICT with citations to threshold, tender relaxation, and policy OM
    mc02 = next((f for f in result.findings if f.condition_id == "MC-02"), None)
    assert mc02 is not None, "MC-02 finding missing"
    assert mc02.status == FindingStatus.CONFLICT, f"Expected MC-02 CONFLICT, got {mc02.status}"
    mc02_clauses = [c.clause_id for c in mc02.citations]
    assert "GEM_BID_8034326::HDR.min_turnover" in mc02_clauses, "MC-02 missing tender threshold citation"
    assert any("MII.4" in c or "DOE_OM" in c for c in mc02_clauses), "MC-02 missing relaxation citation"

    # 3. MC-03 (experience) must be CONFLICT
    mc03 = next((f for f in result.findings if f.condition_id == "MC-03"), None)
    assert mc03 is not None, "MC-03 finding missing"
    assert mc03.status == FindingStatus.CONFLICT, f"Expected MC-03 CONFLICT, got {mc03.status}"
    mc03_clauses = [c.clause_id for c in mc03.citations]
    assert "GEM_BID_8034326::HDR.exp_years" in mc03_clauses, "MC-03 missing experience threshold citation"

    # 4. Advisory flag for QCBS cut-offs present
    assert any("QCBS" in flag for flag in result.advisory_flags), "Missing QCBS cut-offs advisory flag"

    # 5. Verification passes
    assert result.route != Route.REJECT_WITH_CITED_CONDITION, "Bid should not be rejected"
    print("Section 4.1 reference test passed successfully!")


if __name__ == "__main__":
    test_section_4_1_reference_case()

