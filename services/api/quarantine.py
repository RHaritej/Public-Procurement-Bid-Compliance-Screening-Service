"""Quarantine service for malformed or non-compliant bid payloads.

When a payload fails validation, it is recorded in the quarantine store
with field-level error details and assigned a unique quarantine_id.
No run is created, no queue message is emitted, and no agent is invoked.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from bidscreen_common.logging import get_logger
from bidscreen_common.metrics import QUARANTINE_TOTAL

logger = get_logger("bidscreen.quarantine", service="bidscreen-api")

# In-memory quarantine cache for testing or when database is unreachable
_IN_MEMORY_QUARANTINE: dict[str, dict[str, Any]] = {}


class QuarantineService:
    """Manages recording and retrieval of quarantined payloads."""

    def __init__(self, db_pool: Optional[Any] = None) -> None:
        self.db_pool = db_pool

    async def quarantine_request(
        self,
        *,
        correlation_id: str,
        bid_ref: Optional[str],
        errors: list[dict[str, str]],
        raw_payload: Optional[dict[str, Any]] = None,
    ) -> str:
        """Store a quarantined submission and return its unique quarantine_id."""
        quarantine_id = f"Q-{uuid.uuid4().hex[:12].upper()}"
        created_at = datetime.now(timezone.utc).isoformat()

        record = {
            "quarantine_id": quarantine_id,
            "correlation_id": correlation_id,
            "bid_ref": bid_ref or "UNKNOWN",
            "errors": errors,
            "raw_payload": raw_payload or {},
            "created_at": created_at,
        }

        # Store in memory
        _IN_MEMORY_QUARANTINE[quarantine_id] = record
        QUARANTINE_TOTAL.inc()

        # Attempt to persist to PostgreSQL if pool is available
        if self.db_pool is not None:
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO quarantine (quarantine_id, correlation_id, bid_ref, errors_json, raw_payload_json, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        quarantine_id,
                        correlation_id,
                        bid_ref or "UNKNOWN",
                        json.dumps(errors),
                        json.dumps(raw_payload or {}),
                        datetime.now(timezone.utc),
                    )
            except Exception as e:
                logger.warning(
                    "failed_to_write_quarantine_db",
                    error=str(e),
                    quarantine_id=quarantine_id,
                )

        logger.info(
            "request_quarantined",
            quarantine_id=quarantine_id,
            correlation_id=correlation_id,
            bid_ref=bid_ref,
            error_count=len(errors),
        )
        return quarantine_id

    async def get_quarantine_record(self, quarantine_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a quarantined record by ID."""
        if quarantine_id in _IN_MEMORY_QUARANTINE:
            return _IN_MEMORY_QUARANTINE[quarantine_id]

        if self.db_pool is not None:
            try:
                async with self.db_pool.acquire() as conn:
                    row = await conn.fetchrow(
                        "SELECT * FROM quarantine WHERE quarantine_id = $1",
                        quarantine_id,
                    )
                    if row:
                        return {
                            "quarantine_id": row["quarantine_id"],
                            "correlation_id": row["correlation_id"],
                            "bid_ref": row["bid_ref"],
                            "errors": json.loads(row["errors_json"]),
                            "raw_payload": json.loads(row["raw_payload_json"]),
                            "created_at": row["created_at"].isoformat(),
                        }
            except Exception as e:
                logger.warning("failed_to_read_quarantine_db", error=str(e))

        return None
