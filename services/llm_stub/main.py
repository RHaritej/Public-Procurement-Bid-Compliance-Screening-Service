"""LLM Stub service ?" OpenAI-compatible mock server with configurable delay and failure injection.

Used for testing, benchmarking, and load tests without burning LLM tokens.
Allows testing deterministic routing, verification, retries, and circuit breaker.
"""

from __future__ import annotations

import asyncio
import os
import random
import time
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="LLM Stub Service", version="0.1.0")

# Mode state
CURRENT_MODE = os.getenv("STUB_MODE", "normal").lower()
STUB_DELAY_S = float(os.getenv("STUB_DELAY_S", "2.0"))
STUB_FAILURE_RATE = float(os.getenv("STUB_FAILURE_RATE", "0.0"))

REQUESTS_TOTAL = Counter("bidscreen_llm_stub_requests_total", "Total requests to LLM stub", ["mode", "status"])
REQUEST_DURATION = Histogram("bidscreen_llm_stub_duration_seconds", "Latency of LLM stub calls")


class AdminModeRequest(BaseModel):
    mode: str = Field(..., description="One of: 'normal', 'slow', 'fail'")
    delay_s: Optional[float] = Field(default=None, description="Optional delay override in seconds")
    failure_rate: Optional[float] = Field(default=None, description="Optional failure rate between 0.0 and 1.0")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "stub-model"
    messages: list[ChatMessage]
    temperature: Optional[float] = 0.0
    max_tokens: Optional[int] = 1000


@app.get("/health")
@app.get("/healthz")
@app.get("/readyz")
async def health_check():
    return {"status": "ok", "mode": CURRENT_MODE, "delay_s": STUB_DELAY_S}


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/admin/mode")
async def set_mode(payload: AdminModeRequest):
    """Dynamically change stub behavior (normal, slow, fail) during chaos/load testing."""
    global CURRENT_MODE, STUB_DELAY_S, STUB_FAILURE_RATE
    valid_modes = {"normal", "slow", "fail"}
    if payload.mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Must be one of {valid_modes}")
    CURRENT_MODE = payload.mode
    if payload.delay_s is not None:
        STUB_DELAY_S = payload.delay_s
    elif CURRENT_MODE == "slow":
        STUB_DELAY_S = 10.0
    elif CURRENT_MODE == "normal":
        STUB_DELAY_S = float(os.getenv("STUB_DELAY_S", "2.0"))

    if payload.failure_rate is not None:
        STUB_FAILURE_RATE = payload.failure_rate
    elif CURRENT_MODE == "fail":
        STUB_FAILURE_RATE = 1.0
    else:
        STUB_FAILURE_RATE = float(os.getenv("STUB_FAILURE_RATE", "0.0"))

    return {
        "status": "updated",
        "current_mode": CURRENT_MODE,
        "delay_s": STUB_DELAY_S,
        "failure_rate": STUB_FAILURE_RATE,
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, body: ChatCompletionRequest):
    start_time = time.time()

    # Determine simulated delay
    delay = STUB_DELAY_S
    if CURRENT_MODE == "slow":
        delay = max(delay, 5.0)

    if delay > 0:
        await asyncio.sleep(delay)

    # Check simulated failure
    should_fail = (CURRENT_MODE == "fail") or (random.random() < STUB_FAILURE_RATE)
    if should_fail:
        REQUESTS_TOTAL.labels(mode=CURRENT_MODE, status="error").inc()
        raise HTTPException(
            status_code=500,
            detail="Simulated upstream LLM provider failure (stub error injection)",
        )

    # Construct plausible canned response for screening
    # Default is the Section 4.1 test case (ESCALATE_TO_HUMAN due to RULE_CONFLICT)
    content = (
        "Based on analysis of tender GEM/2026/B/8034326 and DoE policy OMs, the bidder "
        "declared category is STARTUP with average turnover 120 lakh against threshold 235 lakh. "
        "Under tender clause GEM_BID_8034326::MII.4 and DoE OM DOE_OM_2016_09_20::P2, "
        "relaxation is conditional on quality and technical specs. Recommend ESCALATE_TO_HUMAN."
    )

    REQUESTS_TOTAL.labels(mode=CURRENT_MODE, status="success").inc()
    REQUEST_DURATION.observe(time.time() - start_time)

    return {
        "id": "chatcmpl-stub-" + str(int(time.time())),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": body.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 180,
            "completion_tokens": 85,
            "total_tokens": 265,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
