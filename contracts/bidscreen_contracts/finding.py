"""Finding models for individual mandatory-condition screening results."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from bidscreen_contracts.enums import FindingStatus, MandatoryCondition


class Citation(BaseModel):
    """A reference to a specific clause in the tender or policy corpus."""

    clause_id: str = Field(
        ...,
        description=(
            "Identifier of the cited clause, e.g. 'GFR-2017-149', "
            "'GeM-Bidding-Conditions-Section-3.2', or 'MC-01'."
        ),
    )
    quoted_text: str = Field(
        ...,
        min_length=1,
        description="Exact quoted text from the corpus document supporting the finding.",
    )


class ScreeningFinding(BaseModel):
    """Result of evaluating a single mandatory eligibility condition."""

    condition_id: MandatoryCondition = Field(
        ..., description="Identifier of the mandatory condition (e.g. MC-01)."
    )
    condition_name: str = Field(
        ..., description="Human-readable name of the condition."
    )
    status: FindingStatus = Field(
        ..., description="Evaluation outcome for this condition."
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="Corpus citations that support the finding.",
    )
    advisory_note: Optional[str] = Field(
        default=None,
        description=(
            "Optional clarifying note for the procuring officer. "
            "The system never makes a final determination — this is advisory only."
        ),
    )
