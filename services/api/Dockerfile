FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY services/api/requirements.txt /app/services/api/requirements.txt
RUN pip install --no-cache-dir -r /app/services/api/requirements.txt

COPY contracts/ /app/contracts/
COPY packages/ /app/packages/
COPY corpus/ /app/corpus/
COPY ingestion/ /app/ingestion/
COPY prompts/ /app/prompts/
RUN pip install --no-cache-dir -e /app/contracts/ -e /app/packages/common/

COPY services/api/ /app/services/api/
COPY services/worker/ /app/services/worker/
COPY services/web/ /app/services/web/

ENV PYTHONPATH=/app:/app/services/api:/app/contracts:/app/packages/common:/app/packages

EXPOSE 8000

CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
