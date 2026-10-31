# Operational Runbook
**Service:** Public Procurement Bid Compliance Screening Service  
**Owner:** Member A (Platform & Reliability)

---

## 1. Service Architecture & Port Reference

| Service | Port | Healthcheck Endpoint | Description |
|---|---|---|---|
| `api` | 8000 | `/health` | FastAPI Gateway (validation, quarantine, rate-limiting) |
| `worker` | 8001 | - | Celery Worker (LangGraph agent executor) |
| `retrieval` | 8002 | `GET /` | Chroma Vector Search & Clause Lookup Service |
| `llm-stub` | 8003 | `/health` | OpenAI-compatible mock LLM provider |
| `web` | 3000 | `GET /` | Single-Page Application Operator UI |
| `prometheus` | 9090 | `/-/healthy` | Metrics storage & PromQL engine |
| `grafana` | 3001 | `/api/health` | Dashboards (Default login: `admin` / `admin`) |
| `jaeger` | 16686 | `/` | Distributed tracing web interface |
| `redis` | 6379 | `redis-cli ping` | Celery broker, cache & rate-limit counters |
| `postgres` | 5432 | `pg_isready` | Relational persistence for runs, quarantine, feedback |

---

## 2. Standard Operational Procedures

### 2.1 Starting the Complete System
```bash
cp .env.example .env
make up
```
Check all container states:
```bash
docker compose ps
```

### 2.2 Scaling Celery Workers
When load spikes or queue latency exceeds the 60s SLO threshold:
```bash
docker compose up -d --scale worker=3
```

### 2.3 Flushing Rate-Limit Counters and Redis Cache
```bash
docker compose exec redis redis-cli FLUSHDB
```

### 2.4 Re-indexing the Knowledge Corpus
To rebuild or update vector embeddings from processed chunks:
```bash
docker compose exec api curl -X POST http://retrieval:8002/reindex?profile=full
```
To build the ablation index (`tender_core` without MII relaxation clauses):
```bash
docker compose exec api curl -X POST http://retrieval:8002/reindex?profile=tender_core
```

---

## 3. Incident Remediation Guide

### Alert: `ScreeningRunDurationP95Exceeded` (> 60s)
1. Check Prometheus metric: `histogram_quantile(0.95, sum(rate(bidscreen_run_duration_seconds_bucket[5m])) by (le))`
2. Inspect Celery queue length in Redis:
   ```bash
   docker compose exec redis redis-cli LLEN celery
   ```
3. Scale workers: `docker compose up -d --scale worker=3`
4. Inspect Jaeger traces for slow external LLM or retrieval tool calls: `http://localhost:16686`

### Alert: `HighQuarantineRate`
1. Check the `quarantine` table in Postgres:
   ```bash
   docker compose exec postgres psql -U bidscreen -d bidscreen -c "SELECT * FROM quarantine ORDER BY created_at DESC LIMIT 5;"
   ```
2. Inspect `errors_json` to determine if client schemas have drifted or malformed submissions are being flooded.

### Alert: `CircuitBreakerTripped` (State = 2)
1. Upstream LLM provider is down or returning high 5xx error rates.
2. Verify LLM stub or provider health:
   ```bash
   curl -i http://localhost:8003/health
   ```
3. In tests, reset stub mode back to normal:
   ```bash
   curl -X POST http://localhost:8003/admin/mode -H "Content-Type: application/json" -d '{"mode": "normal"}'
   ```
