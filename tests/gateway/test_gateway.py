"""Unit tests for LLM Gateway resilience, circuit breaker, and cost tracking."""

import pytest
from bidscreen_contracts.enums import CircuitState
from packages.llm_gateway.resilience import CircuitBreaker, ResponseCache, ProviderUnavailableError
from packages.llm_gateway.cost import CostCalculator, RunCostTracker
from packages.llm_gateway.gateway import LLMGateway


def test_circuit_breaker_transitions():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_s=0.1)
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True

    # 1 failure
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED

    # 2 failures -> OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False

    # Wait for recovery timeout
    import time
    time.sleep(0.15)
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN

    # Success in half open -> CLOSED
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_cost_calculation():
    calc = CostCalculator()
    # 1000 prompt tokens, 500 completion tokens
    cost = calc.compute_cost(1000, 500)
    assert cost > 0.0
    assert isinstance(cost, float)


def test_gateway_stub_mode():
    gw = LLMGateway()
    res = gw.chat(
        messages=[{"role": "user", "content": "Please verify findings"}],
        step="verifier.verify",
        run_id="test-run-gw",
        prompt_version="verifier@v1",
    )
    assert res.text is not None
    assert res.prompt_tokens > 0
    assert res.cost >= 0.0
    assert res.degraded is False

