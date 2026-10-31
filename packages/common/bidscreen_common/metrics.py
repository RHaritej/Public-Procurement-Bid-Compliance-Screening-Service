"""Prometheus metrics with mandatory prefix `bidscreen_`.

Specified in Mini Project 06 implementation plan §6.7.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# ---------------------------------------------------------------------------
# Screening Run Metrics
# ---------------------------------------------------------------------------

RUN_DURATION_SECONDS = Histogram(
    "bidscreen_run_duration_seconds",
    "Time taken to complete a full screening run in seconds.",
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0, 45.0, 60.0, 90.0, 120.0],
)

RUNS_TOTAL = Counter(
    "bidscreen_runs_total",
    "Total screening runs processed.",
    labelnames=["status", "route"],
)

TOOL_CALLS_TOTAL = Counter(
    "bidscreen_tool_calls_total",
    "Total agent tool calls invoked during screening runs.",
    labelnames=["tool"],
)

LLM_COST_USD_TOTAL = Counter(
    "bidscreen_llm_cost_usd_total",
    "Cumulative estimated LLM cost in USD across runs.",
    labelnames=["step"],
)

# ---------------------------------------------------------------------------
# System / Circuit & Index State
# ---------------------------------------------------------------------------

CIRCUIT_STATE = Gauge(
    "bidscreen_circuit_state",
    "Circuit breaker state: 0=CLOSED (healthy), 1=HALF-OPEN, 2=OPEN (broken).",
)

INDEX_CHUNKS = Gauge(
    "bidscreen_index_chunks",
    "Total number of chunks currently indexed in the vector store.",
)

INDEX_BUILT_TIMESTAMP = Gauge(
    "bidscreen_index_built_timestamp",
    "Epoch timestamp when the vector index was last rebuilt.",
)

QUARANTINE_TOTAL = Counter(
    "bidscreen_quarantine_total",
    "Total malformed requests diverted to quarantine without creating a run.",
)

RATE_LIMIT_TOTAL = Counter(
    "bidscreen_rate_limit_total",
    "Total requests rejected by rate limiter (HTTP 429).",
)
