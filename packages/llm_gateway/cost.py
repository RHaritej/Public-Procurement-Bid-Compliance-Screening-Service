"""Token and cost tracking for LLM Gateway (Requirement A5, L6).
Prices and models configured strictly via environment variables.
"""

import os
from typing import Dict, Any
from bidscreen_contracts.run import StepMetrics, TokenCostMetrics


class CostCalculator:
    """Calculates LLM cost based on configured per-million-token rates."""

    def __init__(self):
        # Default pricing: $0.15 / 1M prompt tokens, $0.60 / 1M completion tokens (e.g. gpt-4o-mini / gemini-flash)
        self.input_cost_per_m = float(os.getenv("LLM_INPUT_COST_PER_M", "0.15"))
        self.output_cost_per_m = float(os.getenv("LLM_OUTPUT_COST_PER_M", "0.60"))

    def compute_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        cost = (prompt_tokens * self.input_cost_per_m + completion_tokens * self.output_cost_per_m) / 1_000_000.0
        return round(cost, 6)


class RunCostTracker:
    """Tracks token usage and cost per step and overall for a screening run."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.calculator = CostCalculator()
        self.steps: Dict[str, StepMetrics] = {}
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost_usd = 0.0

    def record_step(
        self,
        step: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        model: str = "",
        prompt_version: str = "",
    ) -> StepMetrics:
        cost = self.calculator.compute_cost(prompt_tokens, completion_tokens)
        total_tokens = prompt_tokens + completion_tokens

        metrics = StepMetrics(
            step=step,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            model=model,
            prompt_version=prompt_version,
        )

        self.steps[step] = metrics
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_cost_usd += cost

        return metrics

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "by_step": {k: v.model_dump() for k, v in self.steps.items()},
        }

