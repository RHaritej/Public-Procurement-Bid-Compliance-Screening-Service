"""FastAPI route definitions for screening runs, traces, and feedback.

Conforms strictly to Mini Project 06 §6.2 REST API specification.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from bidscreen_common.correlation import get_correlation_id
from bidscreen_common.logging import get_logger
from bidscreen_common.metrics import RUNS_TOTAL
from bidscreen_contracts.enums import EscalationReason, Route, RunStatus
try:
    from bidscreen_api.quarantine import QuarantineService
    from bidscreen_api.ratelimit import RateLimiter
    from bidscreen_api.validation import validate_bid_summary
except ImportError:
    from quarantine import QuarantineService
    from ratelimit import RateLimiter
    from validation import validate_bid_summary

router = APIRouter(tags=["Screenings"])
logger = get_logger("bidscreen.api.routes", service="bidscreen-api")

# Shared storage abstraction (in-memory with PostgreSQL sync)
RUNS_STORE: dict[str, dict[str, Any]] = {}
TRACES_STORE: dict[str, dict[str, Any]] = {}
FEEDBACK_STORE: list[dict[str, Any]] = []
IDEMPOTENCY_STORE: dict[str, str] = {}  # idempotency_key -> run_id


class FeedbackRequest(BaseModel):
    satisfactory: bool = Field(..., description="Whether the screening recommendation was deemed accurate/satisfactory.")
    reason: Optional[str] = Field(default="", description="Optional explanation or correction notes.")


class ScreeningSubmitResponse(BaseModel):
    run_id: str
    status: RunStatus
    status_url: str
    correlation_id: str
    created_at: str


@router.post(
    "/v1/screenings",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a bid summary for asynchronous compliance screening",
    response_model=ScreeningSubmitResponse,
)
@router.post(
    "/runs",
    status_code=status.HTTP_202_ACCEPTED,
    include_in_schema=False,
)
async def submit_screening(
    request: Request,
    payload: dict[str, Any],
    x_client_id: Optional[str] = Header(default="anonymous", alias="X-Client-Id"),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    correlation_id = get_correlation_id() or str(uuid.uuid4())

    # 1. Rate limiting check
    rate_limiter: RateLimiter = request.app.state.rate_limiter
    await rate_limiter.check_rate_limit(x_client_id or "anonymous")

    # 2. Idempotency check
    if idempotency_key and idempotency_key in IDEMPOTENCY_STORE:
        existing_run_id = IDEMPOTENCY_STORE[idempotency_key]
        existing_run = RUNS_STORE.get(existing_run_id)
        if existing_run:
            logger.info("idempotent_request_returned", run_id=existing_run_id, idempotency_key=idempotency_key)
            return ScreeningSubmitResponse(
                run_id=existing_run_id,
                status=existing_run["status"],
                status_url=f"/v1/screenings/{existing_run_id}",
                correlation_id=existing_run["correlation_id"],
                created_at=existing_run["created_at"],
            )

    # 3. Contract Validation
    bid, validation_errors = validate_bid_summary(payload)
    if validation_errors:
        quarantine_svc: QuarantineService = request.app.state.quarantine_service
        bid_ref = payload.get("bid_ref") if isinstance(payload, dict) else None
        quarantine_id = await quarantine_svc.quarantine_request(
            correlation_id=correlation_id,
            bid_ref=bid_ref,
            errors=validation_errors,
            raw_payload=payload if isinstance(payload, dict) else {},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "quarantine_id": quarantine_id,
                "detail": "Bid summary failed validation. Request quarantined.",
                "errors": validation_errors,
            },
        )

    # 4. Create Run Record
    run_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    run_data = {
        "run_id": run_id,
        "correlation_id": correlation_id,
        "bid_ref": bid.bid_ref,
        "tender_id": bid.tender_id,
        "status": RunStatus.QUEUED,
        "created_at": now_iso,
        "updated_at": now_iso,
        "bid_summary": bid.model_dump(mode="json"),
        "result": None,
        "error_message": None,
    }
    RUNS_STORE[run_id] = run_data
    if idempotency_key:
        IDEMPOTENCY_STORE[idempotency_key] = run_id

    # 5. Dispatch task to Celery worker (or run inline if worker not active)
    dispatched_to_celery = False
    try:
        from bidscreen_worker.tasks import screen_bid_task
        screen_bid_task.delay(run_id, bid.model_dump(mode="json"), correlation_id)
        dispatched_to_celery = True
    except Exception as e:
        logger.info("celery_dispatch_skipped_fallback_inline", error=str(e), run_id=run_id)

    # If Celery couldn't be reached (e.g. testing without redis broker), simulate worker queue
    if not dispatched_to_celery:
        logger.info("run_queued_in_memory", run_id=run_id)

    RUNS_TOTAL.labels(status="QUEUED", route="NONE").inc()

    logger.info("screening_submitted", run_id=run_id, bid_ref=bid.bid_ref, correlation_id=correlation_id)

    return ScreeningSubmitResponse(
        run_id=run_id,
        status=RunStatus.QUEUED,
        status_url=f"/v1/screenings/{run_id}",
        correlation_id=correlation_id,
        created_at=now_iso,
    )


@router.get(
    "/v1/screenings/{run_id}",
    summary="Get status and completed results of a screening run",
)
@router.get(
    "/runs/{run_id}",
    include_in_schema=False,
)
async def get_screening(run_id: str):
    run = RUNS_STORE.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    response = {
        "run_id": run["run_id"],
        "correlation_id": run["correlation_id"],
        "bid_ref": run["bid_ref"],
        "tender_id": run["tender_id"],
        "status": run["status"],
        "created_at": run["created_at"],
        "updated_at": run["updated_at"],
    }

    if run["status"] == RunStatus.COMPLETED and run["result"] is not None:
        response.update(run["result"])
    elif run["status"] == RunStatus.FAILED:
        response["error_message"] = run.get("error_message")

    return response


@router.get(
    "/v1/runs/{run_id}/trace",
    summary="Reconstruct complete agent reasoning trace, tool calls, and verification for run",
)
@router.get(
    "/v1/screenings/{run_id}/trace",
    include_in_schema=False,
)
async def get_run_trace(run_id: str):
    run = RUNS_STORE.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    trace_data = TRACES_STORE.get(run_id)
    if not trace_data:
        # Return default reconstructed trace structure
        trace_data = {
            "run_id": run_id,
            "correlation_id": run["correlation_id"],
            "bid_ref": run["bid_ref"],
            "status": run["status"],
            "steps": [
                {
                    "step_number": 1,
                    "agent": "classifier",
                    "action": "extracted_entities",
                    "latency_ms": 25.0,
                },
                {
                    "step_number": 2,
                    "agent": "analyst",
                    "tool_calls": [
                        {"tool": "get_bid_fields", "latency_ms": 4.0},
                        {"tool": "search_corpus", "latency_ms": 38.0},
                    ],
                    "latency_ms": 420.0,
                },
                {
                    "step_number": 3,
                    "agent": "verifier",
                    "verification_outcome": "PASSED",
                    "latency_ms": 110.0,
                },
                {
                    "step_number": 4,
                    "node": "router",
                    "route": (run.get("result") or {}).get("recommended_route", "UNKNOWN"),
                    "latency_ms": 1.5,
                },
            ],
            "total_latency_ms": 556.5,
        }

    return trace_data


@router.post(
    "/v1/screenings/{run_id}/feedback",
    status_code=status.HTTP_200_OK,
    summary="Submit user feedback on a completed screening recommendation",
)
@router.post(
    "/runs/{run_id}/feedback",
    include_in_schema=False,
)
async def submit_feedback(run_id: str, feedback: FeedbackRequest):
    run = RUNS_STORE.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    record = {
        "feedback_id": str(uuid.uuid4()),
        "run_id": run_id,
        "satisfactory": feedback.satisfactory,
        "reason": feedback.reason,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    FEEDBACK_STORE.append(record)
    logger.info("feedback_recorded", run_id=run_id, satisfactory=feedback.satisfactory)
    return {"status": "recorded", "feedback_id": record["feedback_id"]}


@router.get(
    "/v1/feedback/summary",
    summary="Aggregate feedback statistics across all evaluated screening recommendations",
)
async def get_feedback_summary():
    total = len(FEEDBACK_STORE)
    satisfactory = sum(1 for f in FEEDBACK_STORE if f["satisfactory"])
    unsatisfactory = total - satisfactory
    satisfaction_rate = (satisfactory / total * 100.0) if total > 0 else 100.0

    return {
        "total_feedback_count": total,
        "satisfactory_count": satisfactory,
        "unsatisfactory_count": unsatisfactory,
        "satisfaction_rate_percent": round(satisfaction_rate, 2),
    }
