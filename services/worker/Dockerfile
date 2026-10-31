FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY contracts/ /app/contracts/
COPY packages/common/ /app/packages/common/
COPY services/api/ /app/services/api/
COPY services/worker/ /app/services/worker/

RUN pip install --no-cache-dir -e /app/contracts/ -e /app/packages/common/
RUN pip install --no-cache-dir celery redis asyncpg structlog prometheus-client opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc fastapi

ENV PYTHONPATH=/app:/app/services/worker:/app/services/api:/app/contracts:/app/packages/common

CMD ["celery", "-A", "services.worker.celery_app.celery_app", "worker", "--loglevel=INFO", "--concurrency=2"]
