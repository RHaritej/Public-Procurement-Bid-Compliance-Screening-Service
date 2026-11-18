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
            "Identifier of the cited clause, e.g. 'GEM_BID_8034326::HDR.min_turnover', "
            "'DOE_OM_2016_09_20::P2'."
        ),
    )
    quote: Optional[str] = Field(
        default=None,
        description="Exact quoted text from the corpus document supporting the finding (under 40 words).",
    )
    quoted_text: Optional[str] = Field(
        default=None,
        description="Exact quoted text alias.",
    )
    passage_id: Optional[str] = Field(
        default=None,
        description="Unique passage ID where this citation was found.",
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

    @model_validator(mode="after")
    def _sync_quotes(self) -> "Citation":
        if self.quote is None and self.quoted_text is not None:
            self.quote = self.quoted_text
        elif self.quoted_text is None and self.quote is not None:
            self.quoted_text = self.quote
        elif self.quote is None and self.quoted_text is None:
            self.quote = ""
            self.quoted_text = ""
        return self


class Finding(BaseModel):
    """Result of evaluating a single mandatory eligibility condition."""

    condition_id: Union[MandatoryCondition, str] = Field(
        ..., description="Identifier of the mandatory condition (e.g. MC-01)."
    )
    status: FindingStatus = Field(
        ..., description="Evaluation outcome for this condition."
    )
    summary: str = Field(
        default="",
        description="Brief natural language summary of the finding.",
    )
    condition_name: Optional[str] = Field(
        default=None,
        description="Human-readable name of the condition.",
    )
    citations: list[Citation] = Field(
        default_factory=list,
        description="Corpus citations that support the finding.",
    )
    advisory_note: Optional[str] = Field(
        default=None,
        description="Optional clarifying note for the procuring officer.",
    )

    @model_validator(mode="after")
    def _sync_summary_name(self) -> "Finding":
        if not self.summary and self.condition_name:
            self.summary = self.condition_name
        elif not self.condition_name and self.summary:
            self.condition_name = self.summary
        return self


# Backward-compatible alias
ScreeningFinding = Finding
