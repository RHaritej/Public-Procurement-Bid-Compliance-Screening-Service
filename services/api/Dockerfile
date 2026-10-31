FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY contracts/ /app/contracts/
COPY packages/common/ /app/packages/common/
COPY services/api/ /app/services/api/
COPY services/worker/ /app/services/worker/

RUN pip install --no-cache-dir -e /app/contracts/ -e /app/packages/common/
RUN pip install --no-cache-dir fastapi uvicorn[standard] redis asyncpg structlog prometheus-client opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc celery

ENV PYTHONPATH=/app:/app/services/api:/app/contracts:/app/packages/common

EXPOSE 8000

CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
