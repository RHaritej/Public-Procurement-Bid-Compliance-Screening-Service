FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY services/llm_stub/requirements.txt /app/services/llm_stub/requirements.txt
RUN pip install --no-cache-dir -r /app/services/llm_stub/requirements.txt

COPY services/llm_stub/ /app/services/llm_stub/

EXPOSE 8003

CMD ["uvicorn", "services.llm_stub.main:app", "--host", "0.0.0.0", "--port", "8003"]
