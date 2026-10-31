"""Correlation ID management using contextvars and FastAPI middleware.

Header: X-Correlation-ID
Every log line, span, and database record carries this ID.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_CORRELATION_ID_CTX: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)

HEADER_NAME = "X-Correlation-ID"


def get_correlation_id() -> Optional[str]:
    """Retrieve the current correlation ID from contextvars, or None."""
    return _CORRELATION_ID_CTX.get()


def set_correlation_id(correlation_id: str) -> None:
    """Explicitly set the correlation ID for the current async task / context."""
    _CORRELATION_ID_CTX.set(correlation_id)


def generate_correlation_id() -> str:
    """Generate a fresh UUID4 correlation ID string."""
    return str(uuid.uuid4())


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """FastAPI / Starlette middleware that extracts or generates X-Correlation-ID.

    1. Checks the incoming request for X-Correlation-ID header.
    2. Uses it if present, otherwise generates a fresh UUID4.
    3. Sets it in contextvars for logging / tracing.
    4. Attaches X-Correlation-ID to the outgoing response headers.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        corr_id = request.headers.get(HEADER_NAME)
        if not corr_id:
            corr_id = generate_correlation_id()

        token = _CORRELATION_ID_CTX.set(corr_id)
        try:
            response: Response = await call_next(request)
            response.headers[HEADER_NAME] = corr_id
            return response
        finally:
            _CORRELATION_ID_CTX.reset(token)
