"""Tool input/output shapes for the screening agent's tool calls (Section 6.4)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from bidscreen_contracts.enums import CorpusScope, FindingStatus, MandatoryCondition


class Passage(BaseModel):
    """One retrieved chunk or passage from the knowledge corpus."""

    passage_id: str = Field(..., description="Unique passage ID.")
    doc_id: str = Field(..., description="Document ID.")
    clause_id: str = Field(..., description="Clause ID (doc_id::key).")
    text: str = Field(..., description="Text content of the passage.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata associated with chunk.")


# ---------------------------------------------------------------------------
# SearchCorpus
# ---------------------------------------------------------------------------

class SearchCorpusInput(BaseModel):
    query: str = Field(..., min_length=1, description="Natural-language search query.")
    scope: CorpusScope = Field(
        default=CorpusScope.BOTH,
        description="Which corpus partition(s) to search.",
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of chunks to return.")
    condition_id: Optional[MandatoryCondition] = Field(default=None)


class SearchCorpusOutput(BaseModel):
    chunks: list[dict] = Field(default_factory=list)
    query_echo: str = Field(...)


# ---------------------------------------------------------------------------
# GetClause
# ---------------------------------------------------------------------------

class GetClauseInput(BaseModel):
    clause_id: str = Field(...)
    scope: CorpusScope = Field(default=CorpusScope.BOTH)


class GetClauseOutput(BaseModel):
    clause_id: str = Field(...)
    text: Optional[str] = Field(default=None)
    source: Optional[str] = Field(default=None)
    found: bool = Field(...)


# ---------------------------------------------------------------------------
# GetBidFields
# ---------------------------------------------------------------------------

class GetBidFieldsInput(BaseModel):
    field_paths: list[str] = Field(..., min_length=1)


class GetBidFieldsOutput(BaseModel):
    fields: dict = Field(default_factory=dict)
    missing: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# FindModifyingProvisions
# ---------------------------------------------------------------------------

class FindModifyingProvisionsInput(BaseModel):
    condition_id: MandatoryCondition = Field(...)
    bidder_category: Optional[str] = Field(default=None)


class FindModifyingProvisionsOutput(BaseModel):
    provisions: list[dict] = Field(default_factory=list)
    conflict_detected: bool = Field(default=False)


# ---------------------------------------------------------------------------
# CheckThreshold
# ---------------------------------------------------------------------------

class CheckThresholdInput(BaseModel):
    condition_id: MandatoryCondition = Field(...)
    actual_value: float = Field(...)
    unit: str = Field(default="INR")


class CheckThresholdOutput(BaseModel):
    condition_id: MandatoryCondition = Field(...)
    threshold_value: float = Field(...)
    actual_value: float = Field(...)
    unit: str = Field(...)
    status: FindingStatus = Field(...)
    delta: float = Field(...)
