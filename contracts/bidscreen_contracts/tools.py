"""Tool input/output shapes for the screening agent's tool calls (§6.4).

These models define the contract between the agent and each tool implementation.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from bidscreen_contracts.enums import CorpusScope, FindingStatus, MandatoryCondition


# ---------------------------------------------------------------------------
# SearchCorpus
# ---------------------------------------------------------------------------


class SearchCorpusInput(BaseModel):
    """Input for the search_corpus tool — semantic/keyword search over the corpus."""

    query: str = Field(..., min_length=1, description="Natural-language search query.")
    scope: CorpusScope = Field(
        default=CorpusScope.BOTH,
        description="Which corpus partition(s) to search.",
    )
    top_k: int = Field(
        default=5, ge=1, le=20, description="Maximum number of chunks to return."
    )
    condition_id: Optional[MandatoryCondition] = Field(
        default=None,
        description="Optional filter to restrict results relevant to a specific MC.",
    )


class SearchCorpusOutput(BaseModel):
    """Output from the search_corpus tool."""

    chunks: list[dict] = Field(
        default_factory=list,
        description=(
            "List of retrieved chunks. Each dict has keys: "
            "'chunk_id', 'source', 'clause_id', 'text', 'score'."
        ),
    )
    query_echo: str = Field(..., description="Echo of the original query.")


# ---------------------------------------------------------------------------
# GetClause
# ---------------------------------------------------------------------------


class GetClauseInput(BaseModel):
    """Input for the get_clause tool — fetch a specific clause by ID."""

    clause_id: str = Field(
        ..., description="Clause identifier, e.g. 'GFR-2017-149' or 'MC-01'."
    )
    scope: CorpusScope = Field(
        default=CorpusScope.BOTH,
        description="Corpus partition to look in.",
    )


class GetClauseOutput(BaseModel):
    """Output from the get_clause tool."""

    clause_id: str = Field(..., description="The requested clause identifier.")
    text: Optional[str] = Field(
        default=None,
        description="Full text of the clause, or None if not found.",
    )
    source: Optional[str] = Field(
        default=None, description="Source document filename or URI."
    )
    found: bool = Field(..., description="Whether the clause was found in the corpus.")


# ---------------------------------------------------------------------------
# GetBidFields
# ---------------------------------------------------------------------------


class GetBidFieldsInput(BaseModel):
    """Input for the get_bid_fields tool — extract specific fields from BidSummary."""

    field_paths: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "List of dot-notation field paths to extract from the BidSummary, "
            "e.g. ['bidder.annual_turnover_lakh', 'bidder.emd_submitted']."
        ),
    )


class GetBidFieldsOutput(BaseModel):
    """Output from the get_bid_fields tool."""

    fields: dict = Field(
        default_factory=dict,
        description="Mapping of requested field paths to their values.",
    )
    missing: list[str] = Field(
        default_factory=list,
        description="Field paths that were not found in the BidSummary.",
    )


# ---------------------------------------------------------------------------
# FindModifyingProvisions
# ---------------------------------------------------------------------------


class FindModifyingProvisionsInput(BaseModel):
    """Input for find_modifying_provisions — locate clauses that override a condition."""

    condition_id: MandatoryCondition = Field(
        ...,
        description="The mandatory condition for which modifying provisions are sought.",
    )
    bidder_category: Optional[str] = Field(
        default=None,
        description="Bidder category to narrow the search (e.g. 'MSE', 'STARTUP').",
    )


class FindModifyingProvisionsOutput(BaseModel):
    """Output from find_modifying_provisions."""

    provisions: list[dict] = Field(
        default_factory=list,
        description=(
            "List of modifying provisions found. Each dict has keys: "
            "'clause_id', 'source', 'summary', 'effect' ('RELAXES' | 'TIGHTENS' | 'EXEMPTS')."
        ),
    )
    conflict_detected: bool = Field(
        default=False,
        description="True if provisions with contradictory effects were found.",
    )


# ---------------------------------------------------------------------------
# CheckThreshold
# ---------------------------------------------------------------------------


class CheckThresholdInput(BaseModel):
    """Input for check_threshold — compare a bid value against a condition threshold."""

    condition_id: MandatoryCondition = Field(
        ..., description="The mandatory condition whose threshold to check."
    )
    actual_value: float = Field(..., description="The actual value from the bid.")
    unit: str = Field(
        default="INR",
        description="Unit of the value (e.g. 'INR', 'lakh', 'percent', 'years').",
    )


class CheckThresholdOutput(BaseModel):
    """Output from check_threshold."""

    condition_id: MandatoryCondition = Field(...)
    threshold_value: float = Field(..., description="The required threshold value.")
    actual_value: float = Field(..., description="The actual value provided.")
    unit: str = Field(...)
    status: FindingStatus = Field(
        ..., description="MET or UNMET based on threshold comparison."
    )
    delta: float = Field(
        ...,
        description=(
            "actual_value - threshold_value "
            "(positive means surplus, negative means deficit)."
        ),
    )
