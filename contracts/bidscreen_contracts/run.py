"""Run-lifecycle models: submission, status, and screening result."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field, model_validator

from bidscreen_contracts.bid_summary import BidSummary
from bidscreen_contracts.enums import EscalationReason, Route
from bidscreen_contracts.enums import RunStatus as RunStatusEnum
from bidscreen_contracts.finding import ScreeningFinding


class StepMetrics(BaseModel):
    """Metrics recorded for a single LLM invocation step."""

    step: str = Field(..., description="Name of the step (e.g. 'analyst', 'verifier').")
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0.0)
    latency_ms: float = Field(default=0.0, ge=0.0)
    model: str = Field(default="", description="LLM model identifier used.")
    prompt_version: str = Field(default="", description="Prompt template version used.")


class TokenCostMetrics(BaseModel):
    """Aggregated token and cost metrics for a screening run."""

    total_prompt_tokens: int = Field(default=0, ge=0)
    total_completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    total_cost_usd: float = Field(default=0.0, ge=0.0)
    by_step: dict[str, StepMetrics] = Field(default_factory=dict)


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
    bid_ref: str = Field(default="", description="Bid reference from the submitted BidSummary.")
    tender_id: str = Field(default="GEM/2026/B/8034326", description="Tender ID from the submitted BidSummary.")
    status: RunStatusEnum = Field(default=RunStatusEnum.COMPLETED)
    recommended_route: Route = Field(
        default=Route.PASS_TO_TECHNICAL_EVALUATION,
        description="Recommended disposition route for the procuring entity.",
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
    advisory_flags: list[str] = Field(
        default_factory=list,
        description="Advisory flags produced during screening.",
    )
    prompt_versions: dict[str, str] = Field(
        default_factory=dict,
        description="Prompt versions used by agents.",
    )
    degraded: bool = Field(
        default=False,
        description="Whether screening executed in degraded mode.",
    )
    tokens_and_cost: dict[str, Any] = Field(
        default_factory=dict,
        description="Token counts and estimated costs.",
    )
    timings_ms: dict[str, float] = Field(
        default_factory=dict,
        description="Step timings in milliseconds.",
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

    @model_validator(mode="before")
    @classmethod
    def _handle_route_alias(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "route" in data and "recommended_route" not in data:
                data["recommended_route"] = data["route"]
            elif "recommended_route" in data and "route" not in data:
                data["route"] = data["recommended_route"]
            if "tokens_and_cost" in data and not data.get("llm_cost_usd"):
                cost = data["tokens_and_cost"].get("total_cost_usd")
                if cost is not None:
                    data["llm_cost_usd"] = float(cost)
        return data

    @property
    def route(self) -> Route:
        return self.recommended_route

