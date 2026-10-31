FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY services/llm_stub/ /app/services/llm_stub/

RUN pip install --no-cache-dir fastapi uvicorn[standard] prometheus-client pydantic

EXPOSE 8003

CMD ["uvicorn", "services.llm_stub.main:app", "--host", "0.0.0.0", "--port", "8003"]
