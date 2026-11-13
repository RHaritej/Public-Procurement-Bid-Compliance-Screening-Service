"""Finding models for individual mandatory-condition screening results."""

from __future__ import annotations

from typing import Optional, Union
from pydantic import BaseModel, Field, model_validator

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
        default="",
        description="Exact quoted text from the corpus document supporting the finding.",
    )
    passage_id: Optional[str] = Field(
        default=None,
        description="Optional internal passage identifier.",
    )

    @model_validator(mode="before")
    @classmethod
    def _handle_quote_alias(cls, data: object) -> object:
        if isinstance(data, dict):
            if "quote" in data and ("quoted_text" not in data or not data["quoted_text"]):
                data["quoted_text"] = data["quote"]
            elif "quoted_text" in data and ("quote" not in data or not data["quote"]):
                data["quote"] = data["quoted_text"]
        return data

    @property
    def quote(self) -> str:
        return self.quoted_text


class ScreeningFinding(BaseModel):
    """Result of evaluating a single mandatory eligibility condition."""

    condition_id: Union[MandatoryCondition, str] = Field(
        ..., description="Identifier of the mandatory condition (e.g. MC-01)."
    )
    condition_name: str = Field(
        default="", description="Human-readable name of the condition."
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
    summary: Optional[str] = Field(
        default=None,
        description="Summary/advisory note alias.",
    )
    quote: Optional[str] = Field(
        default=None,
        description="Optional quote shortcut.",
    )

    @model_validator(mode="before")
    @classmethod
    def _sync_fields(cls, data: object) -> object:
        if isinstance(data, dict):
            if "summary" in data and not data.get("advisory_note"):
                data["advisory_note"] = data["summary"]
            elif "advisory_note" in data and not data.get("summary"):
                data["summary"] = data["advisory_note"]
            if not data.get("condition_name") and "condition_id" in data:
                cid = data["condition_id"]
                data["condition_name"] = str(cid.value if hasattr(cid, "value") else cid)
        return data


# Backwards compatibility alias for Member C agent code and tests
Finding = ScreeningFinding
