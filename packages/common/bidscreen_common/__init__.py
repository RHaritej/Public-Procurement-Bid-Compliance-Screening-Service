"""bidscreen_common ?" shared utilities for logging, tracing, metrics, correlation, and config."""

from bidscreen_common.config import Settings, get_settings
from bidscreen_common.correlation import (
    CorrelationIDMiddleware,
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
)
from bidscreen_common.logging import configure_logging, get_logger
from bidscreen_common.metrics import (
    CIRCUIT_STATE,
    INDEX_BUILT_TIMESTAMP,
    INDEX_CHUNKS,
    LLM_COST_USD_TOTAL,
    QUARANTINE_TOTAL,
    RATE_LIMIT_TOTAL,
    RUN_DURATION_SECONDS,
    RUNS_TOTAL,
    TOOL_CALLS_TOTAL,
)
from bidscreen_common.tracing import get_tracer, init_tracer, traced

__all__ = [
    "Settings",
    "get_settings",
    "CorrelationIDMiddleware",
    "generate_correlation_id",
    "get_correlation_id",
    "set_correlation_id",
    "configure_logging",
    "get_logger",
    "init_tracer",
    "get_tracer",
    "traced",
    "RUN_DURATION_SECONDS",
    "RUNS_TOTAL",
    "TOOL_CALLS_TOTAL",
    "LLM_COST_USD_TOTAL",
    "CIRCUIT_STATE",
    "INDEX_CHUNKS",
    "INDEX_BUILT_TIMESTAMP",
    "QUARANTINE_TOTAL",
    "RATE_LIMIT_TOTAL",
]
