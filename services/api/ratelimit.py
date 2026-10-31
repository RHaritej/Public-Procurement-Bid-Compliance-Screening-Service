"""Rate limiting middleware and service using Redis sliding-window algorithm.

Enforces per-client rate limits using the `X-Client-Id` header (fallback to client host IP).
Rejection returns HTTP 429 Too Many Requests with a `Retry-After` header.
"""

from __future__ import annotations

import time
from typing import Optional

from fastapi import HTTPException
from bidscreen_common.logging import get_logger
from bidscreen_common.metrics import RATE_LIMIT_TOTAL

logger = get_logger("bidscreen.ratelimit", service="bidscreen-api")

# Fallback local in-memory sliding window store: key -> list of float timestamps
_MEMORY_WINDOWS: dict[str, list[float]] = {}


class RateLimiter:
    """Sliding-window rate limiter powered by Redis with in-memory fallback."""

    def __init__(self, redis_client: Optional[any] = None, requests_per_minute: int = 60) -> None:
        self.redis = redis_client
        self.limit = requests_per_minute
        self.window_seconds = 60

    async def check_rate_limit(self, client_id: str) -> None:
        """Check if client exceeds requests_per_minute limit.

        Raises HTTPException(429) if rate limit is exceeded.
        """
        now = time.time()
        key = f"ratelimit:{client_id}"

        # Try Redis if connected
        if self.redis is not None:
            try:
                pipe = self.redis.pipeline()
                # Remove timestamps older than window
                pipe.zremrangebyscore(key, 0, now - self.window_seconds)
                # Add current timestamp
                pipe.zadd(key, {str(now): now})
                # Count items in window
                pipe.zcard(key)
                # Set TTL on window
                pipe.expire(key, self.window_seconds)
                results = await pipe.execute()
                current_count = results[2]

                if current_count > self.limit:
                    RATE_LIMIT_TOTAL.inc()
                    logger.warning("rate_limit_exceeded", client_id=client_id, count=current_count)
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded. Try again later.",
                        headers={"Retry-After": "60"},
                    )
                return
            except HTTPException:
                raise
            except Exception as e:
                logger.warning("redis_ratelimit_fallback_to_memory", error=str(e))

        # Fallback to in-memory sliding window
        window = _MEMORY_WINDOWS.setdefault(client_id, [])
        cutoff = now - self.window_seconds
        # Clean older
        _MEMORY_WINDOWS[client_id] = [ts for ts in window if ts > cutoff]
        _MEMORY_WINDOWS[client_id].append(now)

        if len(_MEMORY_WINDOWS[client_id]) > self.limit:
            RATE_LIMIT_TOTAL.inc()
            logger.warning("rate_limit_exceeded", client_id=client_id, count=len(_MEMORY_WINDOWS[client_id]))
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again later.",
                headers={"Retry-After": "60"},
            )
