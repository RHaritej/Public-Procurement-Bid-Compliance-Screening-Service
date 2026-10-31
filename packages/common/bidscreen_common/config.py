"""Pydantic Settings — all environment variable bindings for the screening service.

No credentials, endpoints, or model names are hard-coded here.
All values are read exclusively from environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised configuration for the Bid Compliance Screening Service.

    All settings are read from environment variables (case-insensitive).
    See .env.example for documentation of every variable.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -----------------------------------------------------------------------
    # Infrastructure URLs
    # -----------------------------------------------------------------------
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL (used by Celery and rate limiter).",
    )
    database_url: str = Field(
        default="postgresql://bidscreen:bidscreen@localhost:5432/bidscreen",
        description="Async PostgreSQL DSN (asyncpg format).",
    )
    retrieval_url: str = Field(
        default="http://localhost:8002",
        description="Base URL of the retrieval / vector-search service.",
    )
    llm_stub_url: str = Field(
        default="http://localhost:8003",
        description="Base URL of the LLM stub service (OpenAI-compatible).",
    )

    # -----------------------------------------------------------------------
    # Celery
    # -----------------------------------------------------------------------
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL (Redis).",
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/1",
        description="Celery result backend URL (Redis).",
    )

    # -----------------------------------------------------------------------
    # LLM Provider
    # -----------------------------------------------------------------------
    llm_provider_url: str = Field(
        default="http://localhost:8003/v1",
        description="Base URL of the live LLM provider (OpenAI-compatible).",
    )
    llm_api_key: str = Field(
        default="stub-key",
        description="API key for the LLM provider. Never log this value.",
    )
    llm_model_name: str = Field(
        default="stub-model",
        description="Model identifier to pass to the LLM provider.",
    )
    llm_embedding_model: str = Field(
        default="stub-embedding-model",
        description="Model identifier for embedding generation.",
    )
    llm_timeout_s: float = Field(
        default=20.0,
        description="Per-request timeout in seconds for LLM calls.",
    )

    # -----------------------------------------------------------------------
    # Agent / Tool limits
    # -----------------------------------------------------------------------
    tool_timeout_s: float = Field(
        default=5.0,
        description="Per-call timeout in seconds for tool invocations.",
    )
    max_steps: int = Field(
        default=12,
        description="Maximum agent reasoning steps per run.",
    )
    max_tool_calls: int = Field(
        default=15,
        description="Maximum total tool invocations per run.",
    )
    run_timeout_s: float = Field(
        default=60.0,
        description="Wall-clock timeout in seconds for a complete screening run.",
    )
    max_verify_retries: int = Field(
        default=2,
        description="Maximum retries for tool verification failures.",
    )

    # -----------------------------------------------------------------------
    # Rate limiting
    # -----------------------------------------------------------------------
    rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum API requests per client IP per minute.",
    )

    # -----------------------------------------------------------------------
    # Business constants
    # -----------------------------------------------------------------------
    tender_id: str = Field(
        default="GEM/2026/B/8034326",
        description="Tender ID this deployment is configured to screen.",
    )

    # -----------------------------------------------------------------------
    # Observability
    # -----------------------------------------------------------------------
    otel_exporter_otlp_endpoint: Optional[str] = Field(
        default=None,
        description=(
            "OTLP gRPC endpoint for OpenTelemetry export "
            "(e.g. http://otel-collector:4317)."
        ),
    )
    service_name: str = Field(
        default="bidscreen-api",
        description="Service name reported in traces and logs.",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings singleton.

    Call ``get_settings.cache_clear()`` in tests to force re-initialisation.
    """
    return Settings()
