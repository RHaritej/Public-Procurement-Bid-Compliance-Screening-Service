"""BidSummary Pydantic model — the primary input contract for bid screening.

Tender ID: GEM/2026/B/8034326
Supports both Member A's canonical flat schema and Member C's agent-oriented schema.
"""

from __future__ import annotations

import re
from datetime import date
from enum import Enum
from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

from bidscreen_contracts.enums import BidderCategory, DocumentType, EmdMode

# Land-border countries with India (ISO-3166-1 alpha-2)
_LAND_BORDER_COUNTRIES: frozenset[str] = frozenset(
    {"CN", "PK", "BD", "NP", "BT", "MM", "AF"}
)

_TENDER_ID = "GEM/2026/B/8034326"
_ISO2_RE = re.compile(r"^[A-Z]{2}$")


class ClientType(str, Enum):
    """Client type classification for similar services."""

    CENTRAL = "CENTRAL"
    CENTRAL_GOVT = "CENTRAL"
    STATE = "STATE"
    STATE_GOVT = "STATE"
    PSU = "PSU"


class SimilarService(BaseModel):
    """A record of a prior similar service contract used for MC-03 / MC-04."""

    contract_value_lakh: Optional[float] = Field(
        default=None,
        gt=0,
        description="Contract value in Indian Rupees lakh.",
    )
    value_lakh: Optional[float] = Field(
        default=None,
        gt=0,
        description="Contract value alias in Indian Rupees lakh.",
    )
    client_type: Union[ClientType, str] = Field(
        ...,
        description="Type of client organisation.",
    )
    fy: Optional[str] = Field(default=None, description="Financial year.")

    @model_validator(mode="before")
    @classmethod
    def _sync_values(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "value_lakh" in data and ("contract_value_lakh" not in data or data["contract_value_lakh"] is None):
                data["contract_value_lakh"] = data["value_lakh"]
            elif "contract_value_lakh" in data and ("value_lakh" not in data or data["value_lakh"] is None):
                data["value_lakh"] = data["contract_value_lakh"]
        return data


class FinancialYearTurnover(BaseModel):
    """Turnover for a single financial year."""

    fy: str = Field(..., description="Financial year (e.g. '2023-24').")
    turnover_lakh: float = Field(..., ge=0, description="Turnover in lakh INR.")


class Financials(BaseModel):
    """Financials container used by agent nodes."""

    turnover_lakh_by_fy: list[FinancialYearTurnover] = Field(default_factory=list)
    declared_average_turnover_lakh: Optional[float] = Field(default=None)

    @property
    def computed_average(self) -> float:
        if not self.turnover_lakh_by_fy:
            return self.declared_average_turnover_lakh or 0.0
        return sum(f.turnover_lakh for f in self.turnover_lakh_by_fy) / max(len(self.turnover_lakh_by_fy), 1)


class Experience(BaseModel):
    """Experience metrics used by agent nodes."""

    years_of_similar_service: float = Field(default=0.0, ge=0)
    similar_services: list[SimilarService] = Field(default_factory=list)


class EmdDetails(BaseModel):
    """EMD details container used by agent nodes."""

    mode: EmdMode = Field(default=EmdMode.PHYSICAL)
    amount_inr: Optional[float] = Field(default=117600.0)
    exemption_basis: Optional[str] = Field(default=None)


class Manpower(BaseModel):
    """Manpower container used by agent nodes."""

    payroll_share_pct_one_year: float = Field(default=0.0, ge=0, le=100)


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
            "as required for land-border countries (MC-07)."
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
        description="DPIIT Startup Recognition Certificate number.",
    )
    dpiit_certificate_number: Optional[str] = Field(
        default=None,
        description="Alias for startup_certificate_number.",
    )
    mse_class: Optional[str] = Field(
        default=None,
        description="MSE subclassification (e.g. Micro, Small).",
    )
    consortium_members: list[str] = Field(
        default_factory=list,
        description="List of consortium members if category is CONSORTIUM.",
    )
    annual_turnover_lakh: list[float] = Field(
        default_factory=lambda: [0.0, 0.0, 0.0],
        description="Annual turnover in INR lakh for the last three financial years.",
    )
    years_experience: float = Field(
        default=0.0, ge=0, description="Total years of relevant service experience."
    )
    similar_services: list[SimilarService] = Field(
        default_factory=list,
        description="List of prior similar service contracts (for MC-03 / MC-04).",
    )
    manpower_payroll_percent: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Percentage of total manpower on payroll for at least one year (MC-05).",
    )
    emd_submitted: bool = Field(
        default=True, description="Whether Earnest Money Deposit has been submitted."
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
        default=True,
        description="Whether the bidder has a service office in the consignee's state (MC-08).",
    )
    documents_submitted: list[str] = Field(
        default_factory=list,
        description="List of document identifiers / names submitted with the bid (MC-06).",
    )

    @model_validator(mode="before")
    @classmethod
    def _sync_startup_cert(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "dpiit_certificate_number" in data and ("startup_certificate_number" not in data or not data["startup_certificate_number"]):
                data["startup_certificate_number"] = data["dpiit_certificate_number"]
            elif "startup_certificate_number" in data and ("dpiit_certificate_number" not in data or not data["dpiit_certificate_number"]):
                data["dpiit_certificate_number"] = data["startup_certificate_number"]
        return data

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
        if self.dpiit_certificate_number and not self.startup_certificate_number:
            self.startup_certificate_number = self.dpiit_certificate_number
        elif self.startup_certificate_number and not self.dpiit_certificate_number:
            self.dpiit_certificate_number = self.startup_certificate_number

        if self.declared_category == BidderCategory.FOREIGN and self.country_code == "IN":
            raise ValueError(
                "A bidder declared as FOREIGN must have a country_code other than 'IN'."
            )
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
        description="Free-text notes from the procuring entity.",
    )
    financials_data: Optional[Financials] = Field(default=None, alias="financials")
    experience_data: Optional[Experience] = Field(default=None, alias="experience")
    emd_data: Optional[EmdDetails] = Field(default=None, alias="emd")
    manpower_data: Optional[Manpower] = Field(default=None, alias="manpower")
    local_office_in_consignee_state_data: Optional[bool] = Field(
        default=None, alias="local_office_in_consignee_state"
    )
    documents_uploaded_data: Optional[list[Any]] = Field(
        default=None, alias="documents_uploaded"
    )

    @field_validator("tender_id")
    @classmethod
    def _validate_tender_id(cls, v: str) -> str:
        if v != _TENDER_ID:
            raise ValueError(f"tender_id must equal '{_TENDER_ID}', got '{v}'.")
        return v

    @model_validator(mode="after")
    def _sync_nested_to_bidder(self) -> "BidSummary":
        if self.financials_data is not None and self.financials_data.turnover_lakh_by_fy:
            self.bidder.annual_turnover_lakh = [
                f.turnover_lakh for f in self.financials_data.turnover_lakh_by_fy
            ]
        if self.experience_data is not None:
            self.bidder.years_experience = self.experience_data.years_of_similar_service
            if self.experience_data.similar_services:
                self.bidder.similar_services = self.experience_data.similar_services
        if self.emd_data is not None:
            self.bidder.emd_amount_inr = self.emd_data.amount_inr
            self.bidder.emd_submitted = self.emd_data.mode in (
                EmdMode.PHYSICAL,
                EmdMode.ONLINE,
            )
            self.bidder.emd_exemption_claimed = self.emd_data.mode in (
                EmdMode.EXEMPTED,
                EmdMode.EXEMPTION_CLAIMED,
            )
        if self.manpower_data is not None:
            self.bidder.manpower_payroll_percent = (
                self.manpower_data.payroll_share_pct_one_year
            )
        if self.local_office_in_consignee_state_data is not None:
            self.bidder.office_in_consignee_state = (
                self.local_office_in_consignee_state_data
            )
        if self.documents_uploaded_data is not None:
            self.bidder.documents_submitted = [
                d.value if hasattr(d, "value") else str(d)
                for d in self.documents_uploaded_data
            ]
        return self

    @property
    def financials(self) -> Financials:
        if self.financials_data is not None:
            return self.financials_data
        fy_list = [
            FinancialYearTurnover(fy=f"FY-{3 - i}", turnover_lakh=val)
            for i, val in enumerate(self.bidder.annual_turnover_lakh)
        ]
        return Financials(turnover_lakh_by_fy=fy_list)

    @property
    def experience(self) -> Experience:
        if self.experience_data is not None:
            return self.experience_data
        return Experience(
            years_of_similar_service=self.bidder.years_experience,
            similar_services=self.bidder.similar_services,
        )

    @property
    def emd(self) -> EmdDetails:
        if self.emd_data is not None:
            return self.emd_data
        if self.bidder.emd_submitted:
            mode = EmdMode.PHYSICAL
        elif self.bidder.emd_exemption_claimed:
            mode = EmdMode.EXEMPTION_CLAIMED
        else:
            mode = EmdMode.NOT_SUBMITTED
        return EmdDetails(mode=mode, amount_inr=self.bidder.emd_amount_inr)

    @property
    def manpower(self) -> Manpower:
        if self.manpower_data is not None:
            return self.manpower_data
        return Manpower(
            payroll_share_pct_one_year=self.bidder.manpower_payroll_percent
        )

    @property
    def local_office_in_consignee_state(self) -> bool:
        if self.local_office_in_consignee_state_data is not None:
            return self.local_office_in_consignee_state_data
        return self.bidder.office_in_consignee_state

    @property
    def documents_uploaded(self) -> list[Any]:
        if self.documents_uploaded_data is not None:
            return self.documents_uploaded_data
        res = []
        for d in self.bidder.documents_submitted:
            try:
                res.append(DocumentType(d))
            except (ValueError, TypeError):
                res.append(d)
        return res
