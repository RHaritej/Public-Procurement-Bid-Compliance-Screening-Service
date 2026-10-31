"""Run-lifecycle models: submission, status, and screening result."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from bidscreen_contracts.bid_summary import BidSummary
from bidscreen_contracts.enums import EscalationReason, Route
from bidscreen_contracts.enums import RunStatus as RunStatusEnum
from bidscreen_contracts.finding import ScreeningFinding


class RunSubmission(BaseModel):
    """Payload accepted by POST /runs."""

    bid_summary: BidSummary = Field(..., description="The bid to be screened.")
    correlation_id: Optional[str] = Field(
        default=None,
        description=(
            "Caller-supplied correlation ID (X-Correlation-ID). "
            "A UUID will be generated if not provided."
        ),
    )


class RunStatusModel(BaseModel):
    """Current lifecycle state of a screening run."""

    run_id: str = Field(..., description="Unique run identifier (UUID).")
    correlation_id: str = Field(..., description="Correlation ID for distributed tracing.")
    bid_ref: str = Field(..., description="Bid reference from the submitted BidSummary.")
    status: RunStatusEnum = Field(..., description="Current run lifecycle status.")
    created_at: datetime = Field(..., description="Timestamp when the run was created.")
    updated_at: datetime = Field(..., description="Timestamp of the last status update.")
    error_message: Optional[str] = Field(
        default=None, description="Error detail if status is FAILED."
    )


class ScreeningResult(BaseModel):
    """Complete screening result returned when a run reaches COMPLETED status.

    IMPORTANT: The system recommends a route only. It NEVER rejects or qualifies
    a bid. Final authority rests with the procuring entity.
    """

    run_id: str = Field(..., description="Unique run identifier (UUID).")
    correlation_id: str = Field(..., description="Correlation ID for distributed tracing.")
    bid_ref: str = Field(..., description="Bid reference from the submitted BidSummary.")
    tender_id: str = Field(..., description="Tender ID from the submitted BidSummary.")
    status: RunStatusEnum = Field(default=RunStatusEnum.COMPLETED)
    recommended_route: Route = Field(
        ..., description="Recommended disposition route for the procuring entity."
    )
    findings: list[ScreeningFinding] = Field(
        default_factory=list,
        description="Individual findings for each evaluated mandatory condition.",
    )
    escalation_reason: Optional[EscalationReason] = Field(
        default=None,
        description="Reason code when recommended_route is ESCALATE_TO_HUMAN.",
    )
    summary_advisory: Optional[str] = Field(
        default=None,
        description=(
            "High-level advisory note for the procuring officer. "
            "Advisory only — the system makes no binding determination."
        ),
    )
    agent_steps: int = Field(
        default=0, description="Number of agent reasoning steps consumed."
    )
    tool_calls: int = Field(
        default=0, description="Number of tool invocations made during screening."
    )
    llm_cost_usd: Optional[float] = Field(
        default=None, description="Estimated LLM cost in USD for this run."
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the run completed."
    )
