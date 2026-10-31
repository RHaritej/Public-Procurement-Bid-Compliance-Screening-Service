"""FastAPI Application Entry Point for the Bid Compliance Screening API.

Service: api (Member A ownership)
Includes Correlation ID middleware, Prometheus metrics, OTel tracing, rate limiting, and quarantine.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from bidscreen_common.config import get_settings
from bidscreen_common.correlation import CorrelationIDMiddleware
from bidscreen_common.logging import configure_logging, get_logger
from bidscreen_common.tracing import init_tracer
try:
    from bidscreen_api.quarantine import QuarantineService
    from bidscreen_api.ratelimit import RateLimiter
    from bidscreen_api.routes.runs import router as runs_router
except ImportError:
    from quarantine import QuarantineService
    from ratelimit import RateLimiter
    from routes.runs import router as runs_router

settings = get_settings()
configure_logging(service_name="bidscreen-api", log_level=settings.log_level)
logger = get_logger("bidscreen.api.main", service="bidscreen-api")
init_tracer(service_name="bidscreen-api", endpoint=settings.otel_exporter_otlp_endpoint)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "service_starting",
        service="bidscreen-api",
        tender_id=settings.tender_id,
        env=os.getenv("ENV", "development"),
    )

    # Setup Redis for rate limiter if available
    redis_client = None
    try:
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await redis_client.ping()
        logger.info("redis_connected_for_ratelimit", redis_url=settings.redis_url)
    except Exception as e:
        logger.warning("redis_unavailable_using_inmemory_ratelimit", error=str(e))
        redis_client = None

    # Setup PostgreSQL if available
    db_pool = None
    try:
        import asyncpg
        db_pool = await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=5)
        # Create schema if not exists
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id VARCHAR(64) PRIMARY KEY,
                    correlation_id VARCHAR(64) NOT NULL,
                    bid_ref VARCHAR(64) NOT NULL,
                    tender_id VARCHAR(64) NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    result_json JSONB,
                    error_message TEXT,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                );
                CREATE TABLE IF NOT EXISTS quarantine (
                    quarantine_id VARCHAR(64) PRIMARY KEY,
                    correlation_id VARCHAR(64) NOT NULL,
                    bid_ref VARCHAR(64),
                    errors_json JSONB NOT NULL,
                    raw_payload_json JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                );
                CREATE TABLE IF NOT EXISTS feedback (
                    id SERIAL PRIMARY KEY,
                    feedback_id VARCHAR(64) NOT NULL,
                    run_id VARCHAR(64) NOT NULL,
                    satisfactory BOOLEAN NOT NULL,
                    reason TEXT,
                    created_at TIMESTAMPTZ NOT NULL
                );
                """
            )
        logger.info("postgres_connected_and_schema_verified", db_url=settings.database_url)
    except Exception as e:
        logger.warning("postgres_unavailable_using_inmemory_store", error=str(e))
        db_pool = None

    app.state.rate_limiter = RateLimiter(
        redis_client=redis_client,
        requests_per_minute=settings.rate_limit_per_minute,
    )
    app.state.quarantine_service = QuarantineService(db_pool=db_pool)
    app.state.db_pool = db_pool
    app.state.redis = redis_client

    yield

    if redis_client:
        await redis_client.aclose()
    if db_pool:
        await db_pool.close()
    logger.info("service_shutdown_complete")


app = FastAPI(
    title="Public Procurement Bid Compliance Screening API",
    description="Automated pre-qualification & mandatory compliance screening for GeM tenders (Tender GEM/2026/B/8034326)",
    version="1.0.0",
    lifespan=lifespan,
)

# Default in-memory state fallbacks for testing and bootstrapping
app.state.rate_limiter = RateLimiter(requests_per_minute=settings.rate_limit_per_minute)
app.state.quarantine_service = QuarantineService()
app.state.db_pool = None
app.state.redis = None

# Middleware
app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
@app.get("/healthz", tags=["Health"])
@app.get("/readyz", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "bidscreen-api",
        "tender_id": settings.tender_id,
    }


@app.get("/metrics", tags=["Observability"])
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(runs_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
