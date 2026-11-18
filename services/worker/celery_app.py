"""Celery application configuration for asynchronous screening runs.

Service: worker (Member A ownership)
"""

from __future__ import annotations

from bidscreen_common.config import get_settings

settings = get_settings()

try:
    from celery import Celery
    _HAS_CELERY = True
except ImportError:
    _HAS_CELERY = False

    class Celery:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            self.conf = {}

        def task(self, *args, **kwargs):
            def decorator(fn):
                def delay(*a, **kw):
                    raise RuntimeError("Celery is not installed or broker is unavailable")
                fn.delay = delay
                return fn
            return decorator

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
    broker_connection_retry_on_startup=False,
    broker_connection_max_retries=1,
    broker_connection_timeout=1.0,
)

if __name__ == "__main__":
    celery_app.start()
