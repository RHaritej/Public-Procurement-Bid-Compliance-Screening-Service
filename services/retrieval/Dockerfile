FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY contracts/ /app/contracts/
COPY packages/common/ /app/packages/common/
COPY ingestion/ /app/ingestion/
COPY services/retrieval/ /app/services/retrieval/
COPY corpus/ /app/corpus/

RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic pypdf

ENV PYTHONPATH=/app:/app/contracts:/app/packages/common:/app/services/retrieval

EXPOSE 8002

CMD ["uvicorn", "services.retrieval.main:app", "--host", "0.0.0.0", "--port", "8002"]
