"""Unit tests for Classifier Node."""

from datetime import date
from bidscreen_contracts.enums import BidderCategory
from bidscreen_contracts.bid_summary import (
    BidSummary,
    BidderInfo,
    Financials,
    FinancialYearTurnover,
    Experience,
    EmdDetails,
    EmdMode,
    Manpower,
)
from packages.agents.nodes.classifier import classify_bidder
from packages.agents.state import AgentState


def test_startup_classification_valid():
    bid = BidSummary(
        bid_ref="BID-TEST-STARTUP",
        tender_id="GEM/2026/B/8034326",
        bidder=BidderInfo(
            name="Valid Startup Inc",
            declared_category=BidderCategory.STARTUP,
            country_code="IN",
            incorporation_date=date(2023, 1, 1),
            dpiit_certificate_number="DPIIT-12345",
        ),
        financials=Financials(turnover_lakh_by_fy=[FinancialYearTurnover(fy="2024-25", turnover_lakh=100.0)]),
        experience=Experience(years_of_similar_service=2),
        emd=EmdDetails(mode=EmdMode.PHYSICAL, amount_inr=117600),
        manpower=Manpower(payroll_share_pct_one_year=20.0),
        local_office_in_consignee_state=True,
    )
    state: AgentState = {"run_id": "test", "correlation_id": "c1", "bid": bid}
    res = classify_bidder(state)
    assert res["category_unclear"] is False
    assert res["confirmed_category"] == BidderCategory.STARTUP


def test_startup_classification_dated_fails():
    # More than 5 years old (Scenario S13)
    bid = BidSummary(
        bid_ref="BID-TEST-OLD-STARTUP",
        tender_id="GEM/2026/B/8034326",
        bidder=BidderInfo(
            name="Old Startup Inc",
            declared_category=BidderCategory.STARTUP,
            country_code="IN",
            incorporation_date=date(2017, 1, 1),
            dpiit_certificate_number="DPIIT-OLD",
        ),
        financials=Financials(turnover_lakh_by_fy=[FinancialYearTurnover(fy="2024-25", turnover_lakh=100.0)]),
        experience=Experience(years_of_similar_service=2),
        emd=EmdDetails(mode=EmdMode.PHYSICAL, amount_inr=117600),
        manpower=Manpower(payroll_share_pct_one_year=20.0),
        local_office_in_consignee_state=True,
    )
    state: AgentState = {"run_id": "test", "correlation_id": "c1", "bid": bid}
    res = classify_bidder(state)
    assert res["category_unclear"] is True
    assert res["confirmed_category"] is None

