FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY services/worker/requirements.txt /app/services/worker/requirements.txt
RUN pip install --no-cache-dir -r /app/services/worker/requirements.txt

COPY contracts/ /app/contracts/
COPY packages/common/ /app/packages/common/
RUN pip install --no-cache-dir -e /app/contracts/ -e /app/packages/common/

COPY services/worker/ /app/services/worker/
COPY services/api/ /app/services/api/

ENV PYTHONPATH=/app:/app/services/worker:/app/services/api:/app/contracts:/app/packages/common

CMD ["celery", "-A", "services.worker.celery_app.celery_app", "worker", "--loglevel=INFO", "--concurrency=2"]
