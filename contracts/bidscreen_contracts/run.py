"""Run-lifecycle models: submission, status, step metrics, and screening result."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator

from bidscreen_contracts.bid_summary import BidSummary
from bidscreen_contracts.enums import EscalationReason, Route
from bidscreen_contracts.enums import RunStatus as RunStatusEnum
from bidscreen_contracts.finding import Finding, ScreeningFinding


class StepMetrics(BaseModel):
    """Metrics recorded for a single reasoning or tool invocation step."""

    step: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    model: str = ""
    prompt_version: str = ""


class TokenCostMetrics(BaseModel):
    """Aggregate token and cost metrics."""

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    steps: Dict[str, StepMetrics] = Field(default_factory=dict)


class RunSubmission(BaseModel):
    """Payload accepted by POST /runs."""

    bid_summary: BidSummary = Field(..., description="The bid to be screened.")
    correlation_id: Optional[str] = Field(default=None)


class RunStatusModel(BaseModel):
    """Current lifecycle state of a screening run."""

    run_id: str
    correlation_id: str
    bid_ref: str
    status: RunStatusEnum
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None


class ScreeningResult(BaseModel):
    """Complete screening result returned when a run reaches COMPLETED status."""

    run_id: str
    correlation_id: str
    bid_ref: str = "UNKNOWN"
    tender_id: str = "GEM/2026/B/8034326"
    status: RunStatusEnum = Field(default=RunStatusEnum.COMPLETED)
    route: Optional[Route] = None
    recommended_route: Optional[Route] = None
    findings: List[Finding] = Field(default_factory=list)
    escalation_reason: Optional[EscalationReason] = None
    advisory_flags: List[str] = Field(default_factory=list)
    summary_advisory: Optional[str] = None
    prompt_versions: Dict[str, str] = Field(default_factory=dict)
    degraded: bool = False
    tokens_and_cost: Optional[Dict[str, Any]] = None
    timings_ms: Optional[Dict[str, float]] = None
    agent_steps: int = 0
    tool_calls: int = 0
    llm_cost_usd: Optional[float] = None
    completed_at: Optional[datetime] = None

    @model_validator(mode="after")
    def _sync_routes(self) -> "ScreeningResult":
        if self.route is None and self.recommended_route is not None:
            self.route = self.recommended_route
        elif self.recommended_route is None and self.route is not None:
            self.recommended_route = self.route
        return self
