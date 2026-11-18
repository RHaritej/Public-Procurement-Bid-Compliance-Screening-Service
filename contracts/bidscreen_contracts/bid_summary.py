"""BidSummary Pydantic model - the primary input contract for bid screening.

Conforms strictly to Section 6.1 Data Contract of Mini Project 06.
Tender ID: GEM/2026/B/8034326
Supports both Member A's canonical flat schema and Member C's agent-oriented schema.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Any, List, Optional, Union

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

from bidscreen_contracts.enums import (
    BidderCategory,
    ClientType,
    DocumentType,
    EmdMode,
    MseClass,
)

_LAND_BORDER_COUNTRIES: frozenset[str] = frozenset(
    {"CN", "PK", "BD", "NP", "BT", "MM", "AF"}
)

_TENDER_ID = "GEM/2026/B/8034326"
_ISO2_RE = re.compile(r"^[A-Z]{2}$")


class FinancialYearTurnover(BaseModel):
    """Annual turnover for one financial year."""

    fy: str = Field(..., description="Financial year, e.g. '2024-25'")
    turnover_lakh: float = Field(..., ge=0.0, description="Annual turnover in INR Lakh.")


class Financials(BaseModel):
    """Financial parameters of the bidding entity."""

    turnover_lakh_by_fy: List[FinancialYearTurnover] = Field(
        default_factory=list,
        description="Up to 3 financial years of turnover data.",
    )
    declared_average_turnover_lakh: Optional[float] = Field(
        default=None,
        description="Declared 3-year average turnover in INR Lakh.",
    )

    @property
    def computed_average(self) -> float:
        if not self.turnover_lakh_by_fy:
            return 0.0
        return sum(f.turnover_lakh for f in self.turnover_lakh_by_fy) / len(self.turnover_lakh_by_fy)


class SimilarService(BaseModel):
    """Prior similar contract record."""

    client_type: Union[ClientType, str] = Field(
        default=ClientType.CENTRAL_GOVT,
        description="Client category (CENTRAL_GOVT, STATE_GOVT, PSU, OTHER).",
    )
    fy: Optional[str] = Field(default=None, description="Financial year completed.")
    contract_value_lakh: float = Field(
        default=0.0,
        ge=0.0,
        description="Contract value in INR Lakh.",
    )
    value_lakh: Optional[float] = Field(
        default=None,
        description="Alias for contract_value_lakh.",
    )

    @model_validator(mode="after")
    def _sync_value(self) -> "SimilarService":
        if self.value_lakh is not None and self.contract_value_lakh == 0.0:
            self.contract_value_lakh = self.value_lakh
        elif self.value_lakh is None:
            self.value_lakh = self.contract_value_lakh
        return self


class Experience(BaseModel):
    """Experience credentials."""

    years_of_similar_service: float = Field(
        default=0.0,
        ge=0.0,
        description="Years of past experience in similar services.",
    )
    similar_services: List[SimilarService] = Field(
        default_factory=list,
        description="Executed contracts.",
    )


class EmdDetails(BaseModel):
    """Earnest Money Deposit submission details."""

    mode: EmdMode = Field(
        default=EmdMode.PHYSICAL,
        description="Submission mode (PHYSICAL, SURETY_BOND, EXEMPTION_CLAIMED, NOT_SUBMITTED).",
    )
    amount_inr: float = Field(
        default=0.0,
        ge=0.0,
        description="EMD amount in INR (required threshold: 117,600).",
    )
    exemption_basis: Optional[str] = Field(
        default=None,
        description="Basis for exemption: 'MSE' or 'STARTUP'.",
    )


class Manpower(BaseModel):
    """Manpower compliance."""

    payroll_share_pct_one_year: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of technical staff on payroll for at least 1 year (MC-05).",
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
    """Bidder organization details and credentials."""

    name: Annotated[str, StringConstraints(min_length=2, max_length=200)] = Field(
        ..., description="Legal name of the bidding entity."
    )
    declared_category: BidderCategory = Field(
        ..., description="Declared bidder category (LARGE, MSE, STARTUP, CONSORTIUM, FOREIGN)."
    )
    country_code: Annotated[str, StringConstraints(min_length=2, max_length=2)] = Field(
        ..., description="ISO-3166-1 alpha-2 country code."
    )
    land_border_registered: Optional[bool] = Field(
        default=None,
        description="Registration with competent authority for land-border countries (MC-07).",
    )
    incorporation_date: date = Field(
        ..., description="Date of entity incorporation."
    )
    udyam_number: Optional[str] = Field(default=None)
    mse_class: Optional[MseClass] = Field(default=None)
    dpiit_certificate_number: Optional[str] = Field(default=None)
    startup_certificate_number: Optional[str] = Field(default=None)
    consortium_members: List[str] = Field(default_factory=list)

    # Optional flat fields for backward compatibility
    annual_turnover_lakh: Optional[List[float]] = Field(default=None)
    years_experience: Optional[float] = Field(default=None)
    similar_services: List[SimilarService] = Field(default_factory=list)
    manpower_payroll_percent: Optional[float] = Field(default=None)
    emd_submitted: Optional[bool] = Field(default=None)
    emd_amount_inr: Optional[float] = Field(default=None)
    emd_exemption_claimed: Optional[bool] = Field(default=None)
    office_in_consignee_state: Optional[bool] = Field(default=None)
    documents_submitted: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _sync_startup_cert(cls, data: Any) -> Any:
        if isinstance(data, dict):
            cert = data.get("dpiit_certificate_number") or data.get("startup_certificate_number") or data.get("dpiit_number")
            if cert:
                data["dpiit_certificate_number"] = cert
                data["startup_certificate_number"] = cert
                data["dpiit_number"] = cert
        return data

    @field_validator("country_code")
    @classmethod
    def _validate_country_code(cls, v: str) -> str:
        if not _ISO2_RE.match(v):
            raise ValueError(f"country_code must be two-letter uppercase ISO-2, got '{v}'.")
        return v

    @field_validator("incorporation_date")
    @classmethod
    def _validate_incorporation_date(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("incorporation_date must not be in the future.")
        return v

    @field_validator("annual_turnover_lakh")
    @classmethod
    def _validate_turnover(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None:
            for val in v:
                if val < 0:
                    raise ValueError("annual_turnover_lakh values must be non-negative turnover numbers.")
        return v

    @model_validator(mode="after")
    def _validate_bidder(self) -> "BidderInfo":
        if self.declared_category == BidderCategory.FOREIGN and self.country_code == "IN":
            raise ValueError("A bidder declared as FOREIGN cannot have country_code 'IN'.")
        if self.country_code in _LAND_BORDER_COUNTRIES and self.land_border_registered is None:
            raise ValueError(
                f"country_code '{self.country_code}' shares a land border with India. "
                "'land_border_registered' must be explicitly provided."
            )
        if self.startup_certificate_number and not self.dpiit_certificate_number:
            self.dpiit_certificate_number = self.startup_certificate_number
        elif self.dpiit_certificate_number and not self.startup_certificate_number:
            self.startup_certificate_number = self.dpiit_certificate_number
        return self


class BidSummary(BaseModel):
    """The complete structured Bid Summary document (Section 6.1)."""

    bid_ref: Annotated[str, StringConstraints(min_length=6, max_length=40)] = Field(
        ..., description="Unique submission reference identifier."
    )
    tender_id: str = Field(..., description="Must equal 'GEM/2026/B/8034326'.")
    bidder: BidderInfo = Field(..., description="Bidder profile.")

    # Structured sections per Section 6.1
    financials: Optional[Financials] = Field(default=None)
    experience: Optional[Experience] = Field(default=None)
    emd: Optional[EmdDetails] = Field(default=None)
    manpower: Optional[Manpower] = Field(default=None)
    local_office_in_consignee_state: Optional[bool] = Field(default=None)
    documents_uploaded: List[Union[DocumentType, str]] = Field(default_factory=list)
    notes: Optional[str] = Field(
        default=None,
        description="Free text notes (scanned for prompt injection).",
    )

    @field_validator("tender_id")
    @classmethod
    def _validate_tender_id(cls, v: str) -> str:
        if v != _TENDER_ID:
            raise ValueError(f"tender_id must equal '{_TENDER_ID}', got '{v}'.")
        return v

    @model_validator(mode="after")
    def _cross_populate_fields(self) -> "BidSummary":
        # 1. Sync Financials <-> bidder.annual_turnover_lakh
        if self.financials and self.financials.turnover_lakh_by_fy:
            if self.bidder.annual_turnover_lakh is None:
                self.bidder.annual_turnover_lakh = [
                    f.turnover_lakh for f in self.financials.turnover_lakh_by_fy
                ]
        elif self.bidder.annual_turnover_lakh:
            fy_list = [
                FinancialYearTurnover(fy=f"FY-{3-i}", turnover_lakh=to)
                for i, to in enumerate(self.bidder.annual_turnover_lakh)
            ]
            self.financials = Financials(
                turnover_lakh_by_fy=fy_list,
                declared_average_turnover_lakh=sum(self.bidder.annual_turnover_lakh)
                / len(self.bidder.annual_turnover_lakh),
            )

        # 2. Sync Experience <-> bidder.years_experience
        if self.experience:
            if self.bidder.years_experience is None:
                self.bidder.years_experience = self.experience.years_of_similar_service
            if not self.bidder.similar_services and self.experience.similar_services:
                self.bidder.similar_services = self.experience.similar_services
        elif self.bidder.years_experience is not None:
            self.experience = Experience(
                years_of_similar_service=self.bidder.years_experience,
                similar_services=self.bidder.similar_services,
            )

        # 3. Sync EMD <-> bidder.emd_*
        if self.emd:
            if self.bidder.emd_submitted is None:
                self.bidder.emd_submitted = self.emd.mode != EmdMode.NOT_SUBMITTED
            if self.bidder.emd_amount_inr is None:
                self.bidder.emd_amount_inr = self.emd.amount_inr
            if self.bidder.emd_exemption_claimed is None:
                self.bidder.emd_exemption_claimed = self.emd.mode == EmdMode.EXEMPTION_CLAIMED
        elif self.bidder.emd_submitted is not None:
            mode = EmdMode.PHYSICAL if self.bidder.emd_submitted else EmdMode.NOT_SUBMITTED
            if self.bidder.emd_exemption_claimed:
                mode = EmdMode.EXEMPTION_CLAIMED
            self.emd = EmdDetails(
                mode=mode,
                amount_inr=self.bidder.emd_amount_inr or 0.0,
            )

        # 4. Sync Manpower <-> bidder.manpower_payroll_percent
        if self.manpower:
            if self.bidder.manpower_payroll_percent is None:
                self.bidder.manpower_payroll_percent = self.manpower.payroll_share_pct_one_year
        elif self.bidder.manpower_payroll_percent is not None:
            self.manpower = Manpower(
                payroll_share_pct_one_year=self.bidder.manpower_payroll_percent
            )

        # 5. Sync Office in consignee state
        if self.local_office_in_consignee_state is not None:
            if self.bidder.office_in_consignee_state is None:
                self.bidder.office_in_consignee_state = self.local_office_in_consignee_state
        elif self.bidder.office_in_consignee_state is not None:
            self.local_office_in_consignee_state = self.bidder.office_in_consignee_state

        # 6. Sync Documents
        if self.documents_uploaded:
            if not self.bidder.documents_submitted:
                self.bidder.documents_submitted = [
                    d.value if hasattr(d, "value") else str(d) for d in self.documents_uploaded
                ]
        elif self.bidder.documents_submitted:
            self.documents_uploaded = self.bidder.documents_submitted

        return self
