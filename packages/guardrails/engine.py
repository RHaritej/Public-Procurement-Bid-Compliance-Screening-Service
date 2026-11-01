"""Central Guardrails Engine (Requirement L4).

Combines:
1. Prompt Injection Defense on input free text
2. Toxicity & Profanity Check on input and output
3. Output Boundary & Determination Filtering
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from packages.guardrails.prompt_injection import PromptInjectionGuard
from packages.guardrails.output_filter import OutputFilterGuard
from packages.guardrails.toxicity import ToxicityGuard


class GuardrailResult:
    def __init__(self, is_safe: bool, reason: Optional[str] = None, sanitized_text: Optional[str] = None):
        self.is_safe = is_safe
        self.reason = reason
        self.sanitized_text = sanitized_text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "reason": self.reason,
            "sanitized_text": self.sanitized_text,
        }


class GuardrailsEngine:
    """Unified guardrails orchestrator."""

    def __init__(self):
        self.injection_guard = PromptInjectionGuard()
        self.output_guard = OutputFilterGuard()
        self.toxicity_guard = ToxicityGuard()

    def validate_input(self, text: Optional[str]) -> GuardrailResult:
        """Validates incoming free-text before reaching LLMs or agents."""
        if not text:
            return GuardrailResult(is_safe=True)

        # 1. Prompt Injection
        safe, reason = self.injection_guard.inspect_text(text)
        if not safe:
            return GuardrailResult(is_safe=False, reason=reason)

        # 2. Toxicity
        safe, reason = self.toxicity_guard.inspect_text(text)
        if not safe:
            return GuardrailResult(is_safe=False, reason=reason)

        return GuardrailResult(is_safe=True, sanitized_text=self.injection_guard.sanitize(text))

    def validate_output(self, text: Optional[str]) -> GuardrailResult:
        """Validates agent / model responses before returning to caller."""
        if not text:
            return GuardrailResult(is_safe=True)

        # 1. Output Determination Limits
        safe, reason = self.output_guard.validate_output(text)
        if not safe:
            sanitized = self.output_guard.sanitize_output(text)
            return GuardrailResult(is_safe=False, reason=reason, sanitized_text=sanitized)

        # 2. Toxicity
        safe, reason = self.toxicity_guard.inspect_text(text)
        if not safe:
            return GuardrailResult(is_safe=False, reason=reason)

        return GuardrailResult(is_safe=True, sanitized_text=text)
