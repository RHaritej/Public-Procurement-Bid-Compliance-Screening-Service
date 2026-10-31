"""bidscreen_contracts – shared Pydantic models and enums for the Bid Compliance Screening Service."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bidscreen_contracts")
except PackageNotFoundError:
    __version__ = "0.0.0"

from bidscreen_contracts.enums import (
    BidderCategory,
    CorpusScope,
    EscalationReason,
    FindingStatus,
    MandatoryCondition,
    Route,
    RunStatus,
)
from bidscreen_contracts.bid_summary import BidSummary, BidderInfo
from bidscreen_contracts.finding import Citation, ScreeningFinding
from bidscreen_contracts.run import RunSubmission, RunStatusModel, ScreeningResult
from bidscreen_contracts.tools import (
    CheckThresholdInput,
    CheckThresholdOutput,
    FindModifyingProvisionsInput,
    FindModifyingProvisionsOutput,
    GetBidFieldsInput,
    GetBidFieldsOutput,
    GetClauseInput,
    GetClauseOutput,
    SearchCorpusInput,
    SearchCorpusOutput,
)

__all__ = [
    "BidderCategory",
    "Route",
    "FindingStatus",
    "EscalationReason",
    "RunStatus",
    "CorpusScope",
    "MandatoryCondition",
    "BidSummary",
    "BidderInfo",
    "Citation",
    "ScreeningFinding",
    "RunSubmission",
    "RunStatusModel",
    "ScreeningResult",
    "SearchCorpusInput",
    "SearchCorpusOutput",
    "GetClauseInput",
    "GetClauseOutput",
    "GetBidFieldsInput",
    "GetBidFieldsOutput",
    "FindModifyingProvisionsInput",
    "FindModifyingProvisionsOutput",
    "CheckThresholdInput",
    "CheckThresholdOutput",
]
