"""Structured JSON logging using structlog.

Mandatory fields on every log line:
  ts, level, service, correlation_id, run_id, agent, step, event, latency_ms

All fields that are not yet known at the call-site are emitted as None
(never omitted) so that log aggregators can rely on a consistent schema.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Optional

import structlog
from structlog.types import EventDict, WrappedLogger


def _add_mandatory_fields(
    logger: WrappedLogger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Ensure every log record carries the mandatory schema fields."""
    # Lazy import to avoid circular dependency
    try:
        from bidscreen_common.correlation import get_correlation_id
        event_dict.setdefault("correlation_id", get_correlation_id())
    except Exception:
        event_dict.setdefault("correlation_id", None)

    event_dict.setdefault("run_id", None)
    event_dict.setdefault("agent", None)
    event_dict.setdefault("step", None)
    event_dict.setdefault("latency_ms", None)
    event_dict.setdefault("service", "bidscreen")
    return event_dict


def configure_logging(service_name: str = "bidscreen", log_level: str = "INFO") -> None:
    """Configure structlog for JSON-structured output.

    Call once at application startup before any logging occurs.
    """
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_mandatory_fields,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.WARNING)


def get_logger(
    name: str,
    *,
    service: Optional[str] = None,
    run_id: Optional[str] = None,
    agent: Optional[str] = None,
) -> structlog.stdlib.BoundLogger:
    """Factory returning a structlog logger pre-bound with service context.

    Args:
        name: Logger name (usually ``__name__`` of the calling module).
        service: Service name override (defaults to ``bidscreen``).
        run_id: Optional run ID to bind immediately.
        agent: Optional agent name to bind immediately.

    Returns:
        A structlog BoundLogger instance.
    """
    try:
        from bidscreen_common.correlation import get_correlation_id
        corr_id = get_correlation_id()
    except Exception:
        corr_id = None

    logger = structlog.get_logger(name)
    bound = logger.bind(
        service=service or "bidscreen",
        correlation_id=corr_id,
    )
    if run_id is not None:
        bound = bound.bind(run_id=run_id)
    if agent is not None:
        bound = bound.bind(agent=agent)
    return bound
