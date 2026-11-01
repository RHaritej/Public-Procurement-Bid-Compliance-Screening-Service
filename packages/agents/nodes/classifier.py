"""Classifier Node (Requirement F3, Section 4.2).
Confirms bidder category using rules first, extracts qualification entities.
Unclear category transitions directly to router with CATEGORY_UNCLEAR.
"""

from datetime import date
from typing import Dict, Any
from bidscreen_contracts.enums import BidderCategory
from packages.agents.state import AgentState


def classify_bidder(state: AgentState) -> Dict[str, Any]:
    """Classifier node: validates category requirements and extracts qualification metrics."""
    bid = state["bid"]
    bidder = bid.bidder
    category = bidder.declared_category

    category_unclear = False
    unclear_reasons = []

    # Rule 1: STARTUP verification against corpus limits
    if category == BidderCategory.STARTUP:
        if not bidder.dpiit_certificate_number:
            category_unclear = True
            unclear_reasons.append("Missing DPIIT certificate number")

        # Action Plan Annexure 1.A limit is 5 years from incorporation
        # Scenario S13: Startup incorporated 8 years ago -> CATEGORY_UNCLEAR
        today = date.today()
        years_since_inc = (today - bidder.incorporation_date).days / 365.25
        if years_since_inc > 5.0:
            category_unclear = True
            unclear_reasons.append(
                f"Startup incorporation age ({years_since_inc:.1f} years) exceeds corpus definition limit of 5 years (Annexure 1.A)"
            )

    # Rule 2: MSE verification
    elif category == BidderCategory.MSE:
        if not bidder.udyam_number or not bidder.mse_class:
            category_unclear = True
            unclear_reasons.append("MSE missing Udyam registration or classification")

    # Rule 3: CONSORTIUM verification
    elif category == BidderCategory.CONSORTIUM:
        if not bidder.consortium_members or len(bidder.consortium_members) < 2:
            category_unclear = True
            unclear_reasons.append("Consortium has fewer than 2 declared members")

    # Extract qualification entities
    avg_turnover = bid.financials.computed_average
    years_exp = bid.experience.years_of_similar_service
    payroll_pct = bid.manpower.payroll_share_pct_one_year

    qualification_entities = {
        "bid_ref": bid.bid_ref,
        "category": category.value,
        "average_turnover_lakh": avg_turnover,
        "years_of_similar_service": years_exp,
        "payroll_share_pct": payroll_pct,
        "emd_mode": bid.emd.mode.value,
        "emd_amount_inr": bid.emd.amount_inr,
        "emd_exemption_basis": bid.emd.exemption_basis,
        "has_local_office": bid.local_office_in_consignee_state,
        "land_border_registered": bidder.land_border_registered,
        "country_code": bidder.country_code,
        "documents": [d.value for d in bid.documents_uploaded],
        "unclear_reasons": unclear_reasons,
    }

    step_count = state.get("step_count", 0) + 1

    return {
        "step_count": step_count,
        "confirmed_category": None if category_unclear else category,
        "category_unclear": category_unclear,
        "qualification_entities": qualification_entities,
    }

