"""Unit tests for the rate limiter service."""

from __future__ import annotations

import asyncio
import pytest
from fastapi import HTTPException

try:
    from services.api.ratelimit import RateLimiter
except ImportError:
    from ratelimit import RateLimiter


def test_rate_limiter_within_limit():
    """Requests within limit must succeed without error."""
    async def _run():
        limiter = RateLimiter(redis_client=None, requests_per_minute=5)
        for _ in range(5):
            await limiter.check_rate_limit("client-ok")
    asyncio.run(_run())


def test_rate_limiter_exceeded():
    """Requests exceeding requests_per_minute must raise HTTPException 429."""
    async def _run():
        limiter = RateLimiter(redis_client=None, requests_per_minute=3)
        # 3 allowed
        for _ in range(3):
            await limiter.check_rate_limit("client-blocked")

        # 4th must trigger 429
        with pytest.raises(HTTPException) as exc_info:
            await limiter.check_rate_limit("client-blocked")

        assert exc_info.value.status_code == 429
        assert exc_info.value.headers.get("Retry-After") == "60"
    asyncio.run(_run())
