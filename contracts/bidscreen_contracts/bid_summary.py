"""BidSummary Pydantic model — the primary input contract for bid screening.

Tender ID: GEM/2026/B/8034326
"""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

from bidscreen_contracts.enums import BidderCategory

# Land-border countries with India (ISO-3166-1 alpha-2)
_LAND_BORDER_COUNTRIES: frozenset[str] = frozenset(
    {"CN", "PK", "BD", "NP", "BT", "MM", "AF"}
)

_TENDER_ID = "GEM/2026/B/8034326"
_ISO2_RE = re.compile(r"^[A-Z]{2}$")


class SimilarService(BaseModel):
    """A record of a prior similar service contract used for MC-03 / MC-04."""

    contract_value_lakh: float = Field(
        ...,
        gt=0,
        description="Contract value in Indian Rupees lakh.",
    )
    client_type: Literal["CENTRAL", "STATE", "PSU"] = Field(
        ...,
        description="Type of client organisation.",
    )


class BidderInfo(BaseModel):
    """All bidder-specific fields extracted from the bid submission."""

    name: Annotated[str, StringConstraints(min_length=2, max_length=200)] = Field(
        ..., description="Legal name of the bidding entity."
    )
    declared_category: BidderCategory = Field(
        ..., description="Category declared by the bidder."
    )
    country_code: Annotated[str, StringConstraints(min_length=2, max_length=2)] = Field(
        ..., description="ISO-3166-1 alpha-2 country code of the bidder."
    )
    land_border_registered: Optional[bool] = Field(
        default=None,
        description=(
            "Whether the bidder is registered with the competent authority "
            "as required for land-border countries (MC-07). "
            "Must be provided when country_code shares a land border with India."
        ),
    )
    incorporation_date: date = Field(
        ..., description="Date of incorporation / registration of the entity."
    )
    udyam_number: Optional[str] = Field(
        default=None,
        description="MSME Udyam Registration Number (required for MSE category).",
    )
    startup_certificate_number: Optional[str] = Field(
        default=None,
        description=(
            "DPIIT Startup Recognition Certificate number. "
            "The system does NOT decide whether the entity qualifies as a startup; "
            "it only records the certificate number as submitted."
        ),
    )
    annual_turnover_lakh: list[float] = Field(
        ...,
        min_length=3,
        max_length=3,
        description=(
            "Annual turnover in INR lakh for the last three financial years, "
            "ordered oldest-first (FY-3, FY-2, FY-1)."
        ),
    )
    years_experience: float = Field(
        ..., ge=0, description="Total years of relevant service experience."
    )
    similar_services: list[SimilarService] = Field(
        default_factory=list,
        description="List of prior similar service contracts (for MC-03 / MC-04).",
    )
    manpower_payroll_percent: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of total manpower on payroll for at least one year (MC-05).",
    )
    emd_submitted: bool = Field(
        ..., description="Whether Earnest Money Deposit has been submitted."
    )
    emd_amount_inr: Optional[float] = Field(
        default=None,
        ge=0,
        description="EMD amount in INR as submitted (MC-01 threshold: 117,600).",
    )
    emd_exemption_claimed: bool = Field(
        default=False,
        description="Whether the bidder has claimed EMD exemption.",
    )
    office_in_consignee_state: bool = Field(
        ...,
        description="Whether the bidder has a service office in the consignee's state (MC-08).",
    )
    documents_submitted: list[str] = Field(
        default_factory=list,
        description="List of document identifiers / names submitted with the bid (MC-06).",
    )

    @field_validator("country_code")
    @classmethod
    def _validate_country_code(cls, v: str) -> str:
        if not _ISO2_RE.match(v):
            raise ValueError(
                f"country_code must be a two-letter ISO-3166-1 alpha-2 code, got '{v}'."
            )
        return v

    @field_validator("incorporation_date")
    @classmethod
    def _validate_incorporation_date(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("incorporation_date must not be in the future.")
        return v

    @field_validator("annual_turnover_lakh")
    @classmethod
    def _validate_turnover(cls, v: list[float]) -> list[float]:
        for val in v:
            if val < 0:
                raise ValueError("annual_turnover_lakh values must be non-negative.")
        return v

    @model_validator(mode="after")
    def _cross_field_validation(self) -> "BidderInfo":
        # FOREIGN category must not use "IN"
        if self.declared_category == BidderCategory.FOREIGN and self.country_code == "IN":
            raise ValueError(
                "A bidder declared as FOREIGN must have a country_code other than 'IN'."
            )
        # Land-border countries require land_border_registered
        if (
            self.country_code in _LAND_BORDER_COUNTRIES
            and self.land_border_registered is None
        ):
            raise ValueError(
                f"country_code '{self.country_code}' shares a land border with India. "
                "'land_border_registered' must be explicitly set (True or False)."
            )
        return self


class BidSummary(BaseModel):
    """Top-level bid submission document submitted to the screening service.

    Tender: GEM/2026/B/8034326
    """

    bid_ref: Annotated[str, StringConstraints(min_length=6, max_length=40)] = Field(
        ...,
        description="Unique bid reference identifier assigned by the procuring entity.",
    )
    tender_id: str = Field(..., description=f"Must equal '{_TENDER_ID}'.")
    bidder: BidderInfo = Field(..., description="Bidder details and declared credentials.")
    notes: Optional[str] = Field(
        default=None,
        description=(
            "Free-text notes from the procuring entity. "
            "GUARDRAIL SCANNING REQUIRED before processing: "
            "this field is checked for prompt-injection attempts via the guardrail endpoint."
        ),
    )

    @field_validator("tender_id")
    @classmethod
    def _validate_tender_id(cls, v: str) -> str:
        if v != _TENDER_ID:
            raise ValueError(f"tender_id must equal '{_TENDER_ID}', got '{v}'.")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "bid_ref": "BID-2026-001",
                    "tender_id": "GEM/2026/B/8034326",
                    "bidder": {
                        "name": "Acme Solutions Pvt Ltd",
                        "declared_category": "LARGE",
                        "country_code": "IN",
                        "incorporation_date": "2010-04-01",
                        "annual_turnover_lakh": [280.0, 310.0, 340.0],
                        "years_experience": 8.0,
                        "similar_services": [
                            {"contract_value_lakh": 100.0, "client_type": "CENTRAL"}
                        ],
                        "manpower_payroll_percent": 35.0,
                        "emd_submitted": True,
                        "emd_amount_inr": 117600.0,
                        "emd_exemption_claimed": False,
                        "office_in_consignee_state": True,
                        "documents_submitted": [
                            "TechBid.pdf",
                            "FinancialBid.pdf",
                            "EMD_Receipt.pdf",
                        ],
                    },
                    "notes": None,
                }
            ]
        }
    }
