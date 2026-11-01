"""LLM Gateway: Centralised access, resilience, and metrics tracking for all model calls.
Reference: Sections 4.1, 6.5, 6.7, and 7.
"""

import os
import time
import json
import random
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from bidscreen_contracts.enums import CircuitState
from packages.llm_gateway.cost import CostCalculator
from packages.llm_gateway.resilience import (
    CircuitBreaker,
    ResponseCache,
    ProviderUnavailableError,
    GatewayTimeoutError,
)

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    cost: float
    latency_ms: float
    degraded: bool = False


class LLMGateway:
    """Gateway through which all agent LLM calls must pass."""

    def __init__(self):
        # Configuration strictly from environment variables (Rule 4)
        self.provider = os.getenv("LLM_PROVIDER", "stub").lower()
        self.base_url = os.getenv("LLM_BASE_URL", "")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model_name = os.getenv("LLM_MODEL", "gemini-2.0-flash")
        self.default_timeout_s = float(os.getenv("LLM_TIMEOUT_S", "20.0"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))

        self.cost_calculator = CostCalculator()
        self.circuit_breaker = CircuitBreaker()
        self.cache = ResponseCache()

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (approx 4 chars per token)."""
        return max(1, len(text) // 4)

    def _log_event(
        self,
        event: str,
        level: str,
        run_id: str,
        step: str,
        correlation_id: str = "",
        latency_ms: float = 0.0,
        extra: Optional[Dict[str, Any]] = None,
    ):
        """Standard JSON log format (Section 6.7)."""
        log_data = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": level,
            "service": "llm_gateway",
            "correlation_id": correlation_id,
            "run_id": run_id,
            "agent": step.split(".")[0] if "." in step else step,
            "step": step,
            "event": event,
            "latency_ms": latency_ms,
        }
        if extra:
            log_data.update(extra)
        log_line = json.dumps(log_data)
        if level == "ERROR":
            logger.error(log_line)
        elif level == "WARNING":
            logger.warning(log_line)
        else:
            logger.info(log_line)

    def chat(
        self,
        messages: List[Dict[str, str]],
        step: str,
        run_id: str,
        prompt_version: str,
        timeout_s: Optional[float] = None,
        correlation_id: str = "",
    ) -> LLMResponse:
        """Executes a chat call with timeouts, exponential backoff retries, and circuit breaker."""
        timeout = timeout_s or self.default_timeout_s
        start_time = time.time()

        # 1. Check Circuit Breaker
        if not self.circuit_breaker.can_execute():
            self._log_event(
                event="circuit_breaker_open",
                level="WARNING",
                run_id=run_id,
                step=step,
                correlation_id=correlation_id,
            )
            # Try cache fallback
            cached_val = self.cache.get(messages, prompt_version)
            if cached_val:
                latency_ms = (time.time() - start_time) * 1000
                self._log_event(
                    event="cache_fallback_hit",
                    level="INFO",
                    run_id=run_id,
                    step=step,
                    correlation_id=correlation_id,
                    latency_ms=latency_ms,
                )
                return LLMResponse(
                    text=cached_val["text"],
                    prompt_tokens=cached_val["prompt_tokens"],
                    completion_tokens=cached_val["completion_tokens"],
                    cost=0.0,
                    latency_ms=latency_ms,
                    degraded=True,
                )
            raise ProviderUnavailableError("LLM provider circuit is OPEN and cache missed.")

        # 2. Execution with retries and exponential backoff
        attempts = 0
        last_exception = None

        while attempts < self.max_retries:
            attempts += 1
            call_start = time.time()
            try:
                raw_text, p_tokens, c_tokens = self._dispatch_call(messages, timeout)
                latency_ms = (time.time() - call_start) * 1000

                self.circuit_breaker.record_success()

                cost = self.cost_calculator.compute_cost(p_tokens, c_tokens)
                self.cache.set(
                    messages,
                    prompt_version,
                    {"text": raw_text, "prompt_tokens": p_tokens, "completion_tokens": c_tokens},
                )

                self._log_event(
                    event="llm_call_success",
                    level="INFO",
                    run_id=run_id,
                    step=step,
                    correlation_id=correlation_id,
                    latency_ms=latency_ms,
                    extra={"prompt_tokens": p_tokens, "completion_tokens": c_tokens, "cost_usd": cost},
                )

                return LLMResponse(
                    text=raw_text,
                    prompt_tokens=p_tokens,
                    completion_tokens=c_tokens,
                    cost=cost,
                    latency_ms=latency_ms,
                    degraded=False,
                )

            except Exception as e:
                last_exception = e
                latency_ms = (time.time() - call_start) * 1000
                self.circuit_breaker.record_failure()

                self._log_event(
                    event="llm_call_failed",
                    level="WARNING",
                    run_id=run_id,
                    step=step,
                    correlation_id=correlation_id,
                    latency_ms=latency_ms,
                    extra={"attempt": attempts, "error": str(e)},
                )

                if attempts < self.max_retries:
                    backoff = (2 ** (attempts - 1)) + random.uniform(0.1, 0.5)
                    time.sleep(backoff)

        # 3. All retries failed: Attempt Fallback Cache
        cached_val = self.cache.get(messages, prompt_version)
        if cached_val:
            latency_ms = (time.time() - start_time) * 1000
            self._log_event(
                event="fallback_cache_used_after_retries",
                level="INFO",
                run_id=run_id,
                step=step,
                correlation_id=correlation_id,
                latency_ms=latency_ms,
            )
            return LLMResponse(
                text=cached_val["text"],
                prompt_tokens=cached_val["prompt_tokens"],
                completion_tokens=cached_val["completion_tokens"],
                cost=0.0,
                latency_ms=latency_ms,
                degraded=True,
            )

        raise ProviderUnavailableError(f"All {self.max_retries} attempts failed: {last_exception}")

    def _dispatch_call(self, messages: List[Dict[str, str]], timeout_s: float) -> tuple[str, int, int]:
        """Dispatches call based on configured provider."""
        # Calculate prompt tokens
        prompt_content = " ".join([m.get("content", "") for m in messages])
        p_tokens = self._estimate_tokens(prompt_content)

        if self.provider == "openai" and self.api_key:
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url or None)
            res = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                timeout=timeout_s,
            )
            text = res.choices[0].message.content or ""
            c_tokens = res.usage.completion_tokens if res.usage else self._estimate_tokens(text)
            p_tokens = res.usage.prompt_tokens if res.usage else p_tokens
            return text, p_tokens, c_tokens

        # Deterministic Stub/Mock Provider for reliable testing and local verification
        return self._generate_stub_response(messages, p_tokens)

    def _generate_stub_response(self, messages: List[Dict[str, str]], p_tokens: int) -> tuple[str, int, int]:
        """Generates realistic responses conforming to agent contracts when in stub mode."""
        last_msg = messages[-1]["content"] if messages else ""

        # Verifier Agent response
        if "verifier" in last_msg.lower() or "verify" in last_msg.lower() or "verification" in last_msg.lower():
            resp = json.dumps({
                "verdict": "PASS",
                "reasoning": "All mandatory findings cite valid passages retrieved in the session. Citations resolve exactly.",
                "unsupported_findings": [],
                "invalid_citations": []
            })
            return resp, p_tokens, self._estimate_tokens(resp)

        # Analyst Agent default structured finding response
        resp = json.dumps({
            "analysis": "Analyzed conditions against tender and policy provisions.",
            "findings": []
        })
        return resp, p_tokens, self._estimate_tokens(resp)

