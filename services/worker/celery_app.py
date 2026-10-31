"""Celery application configuration for asynchronous screening runs.

Service: worker (Member A ownership)
"""

from __future__ import annotations

from celery import Celery
from bidscreen_common.config import get_settings

settings = get_settings()

celery_app = Celery(
    "bidscreen_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["services.worker.tasks", "tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=int(settings.run_timeout_s),
    worker_prefetch_multiplier=1,
)

if __name__ == "__main__":
    celery_app.start()
