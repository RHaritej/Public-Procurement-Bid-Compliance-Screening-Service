"""Enumeration types for the Bid Compliance Screening Service.

All enums are string-valued to ensure JSON serialisation compatibility.
"""

from enum import Enum


class BidderCategory(str, Enum):
    """Classification of the bidding entity as declared in the bid."""

    LARGE = "LARGE"
    MSE = "MSE"
    STARTUP = "STARTUP"
    CONSORTIUM = "CONSORTIUM"
    FOREIGN = "FOREIGN"


class Route(str, Enum):
    """Recommended disposition route produced by the screening agent.

    The system NEVER rejects or qualifies a bid; it only recommends a route.
    Final decision authority rests with the procuring entity.
    """

    PASS_TO_TECHNICAL_EVALUATION = "PASS_TO_TECHNICAL_EVALUATION"
    SEEK_CLARIFICATION = "SEEK_CLARIFICATION"
    REJECT_WITH_CITED_CONDITION = "REJECT_WITH_CITED_CONDITION"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"


class FindingStatus(str, Enum):
    """Status of a single mandatory-condition finding."""

    MET = "MET"
    UNMET = "UNMET"
    CONFLICT = "CONFLICT"
    NOT_VERIFIABLE = "NOT_VERIFIABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class EscalationReason(str, Enum):
    """Reason codes for ESCALATE_TO_HUMAN route recommendations."""

    RULE_CONFLICT = "RULE_CONFLICT"
    CATEGORY_UNCLEAR = "CATEGORY_UNCLEAR"
    NO_EVIDENCE_IN_CORPUS = "NO_EVIDENCE_IN_CORPUS"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    GUARDRAIL_BLOCK = "GUARDRAIL_BLOCK"


class RunStatus(str, Enum):
    """Lifecycle state of a screening run."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CorpusScope(str, Enum):
    """Which corpus partition to search."""

    TENDER = "TENDER"
    POLICY = "POLICY"
    BOTH = "BOTH"


class MandatoryCondition(str, Enum):
    """Identifiers for the mandatory eligibility conditions (MC-01 to MC-09)."""

    MC_01 = "MC-01"  # EMD INR 117,600
    MC_02 = "MC-02"  # Annual turnover >= 235 lakh (last 3 FY)
    MC_03 = "MC-03"  # 3 years similar service to Central/State/PSU
    MC_04 = "MC-04"  # Similar services: 3@40%, 2@50%, or 1@80% of estimated cost
    MC_05 = "MC-05"  # >= 20% manpower on payroll for 1 year
    MC_06 = "MC-06"  # Document completeness
    MC_07 = "MC-07"  # Land-border country bidders registered with competent authority
    MC_08 = "MC-08"  # Service provider office in consignee's state
    MC_09 = "MC-09"  # Preference category claimed with supporting docs
