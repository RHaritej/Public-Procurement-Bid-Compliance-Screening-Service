"""Resilience components for LLM Gateway: Circuit Breaker, Retries, and Fallback Cache."""

import time
import hashlib
import json
import logging
from typing import Dict, Any, Optional, Callable
from bidscreen_contracts.enums import CircuitState

logger = logging.getLogger(__name__)


class ProviderUnavailableError(Exception):
    """Raised when the LLM provider is down or circuit is open and fallback fails."""
    pass


class GatewayTimeoutError(Exception):
    """Raised when an LLM call exceeds its allocated timeout."""
    pass


class CircuitBreaker:
    """Standard Circuit Breaker implementation with CLOSED, OPEN, and HALF_OPEN states."""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout_s: float = 30.0,
        half_open_max_trials: int = 1,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self.half_open_max_trials = half_open_max_trials

        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0
        self.last_failure_time: float = 0.0
        self.trial_count: int = 0

    def can_execute(self) -> bool:
        now = time.time()
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time >= self.recovery_timeout_s:
                logger.info("Circuit breaker transitioning from OPEN to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.trial_count = 0
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return self.trial_count < self.half_open_max_trials

        return False

    def record_success(self):
        if self.state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
            logger.info("Circuit breaker probe succeeded; transitioning to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.trial_count = 0

    def record_failure(self):
        self.last_failure_time = time.time()
        self.failure_count += 1

        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Trial failed in HALF_OPEN state; returning to OPEN")
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            logger.warning("Failure threshold (%d) reached; opening circuit", self.failure_threshold)
            self.state = CircuitState.OPEN


class ResponseCache:
    """In-memory cache for fallback when provider is temporarily unavailable."""

    def __init__(self, ttl_s: float = 3600.0):
        self.ttl_s = ttl_s
        self._cache: Dict[str, tuple[float, Any]] = {}

    def _hash_key(self, messages: Any, prompt_version: str) -> str:
        serialized = json.dumps({"messages": messages, "v": prompt_version}, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get(self, messages: Any, prompt_version: str) -> Optional[Any]:
        key = self._hash_key(messages, prompt_version)
        if key in self._cache:
            created_at, val = self._cache[key]
            if time.time() - created_at < self.ttl_s:
                return val
            del self._cache[key]
        return None

    def set(self, messages: Any, prompt_version: str, val: Any):
        key = self._hash_key(messages, prompt_version)
        self._cache[key] = (time.time(), val)

