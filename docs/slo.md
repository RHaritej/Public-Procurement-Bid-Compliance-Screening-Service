# Service Level Objectives (SLO) Document
**System:** Bid Compliance Screening Service (Mini Project 06)  
**Author:** Member A (Platform & Reliability Lead)  
**Date:** 31 October 2026  
**Status:** COMMITTED (Target established prior to load testing per specification §7)

---

## 1. Primary Service Level Objective (p95 Run Duration)

| Metric | Target | Measurement Window |
|---|---|---|
| **End-to-End Screening Run Duration ($p_{95}$)** | **$\le$ 60.0 seconds** | 15-minute rolling window |
| **Concurrency Condition** | 20 concurrent submitters | Continuous load |
| **Simulated LLM Latency** | $\approx$ 2.0s per model call | Baseline provider delay |
| **Screening Route Accuracy / Groundedness** | 100% resolution of citations to retrieved corpus passages | Cumulative per evaluation pack |

### Rationale
Screening is an asynchronous pipeline involving entity extraction, multi-hop semantic and keyword retrieval against tender and policy corpora, citation verification, and deterministic routing. With 3–4 agent steps each averaging 2 seconds of LLM inference plus 50–100ms retrieval per hop, total processing time under single-worker execution is ~12–18s. At 20 concurrent submissions, queuing delay must not push $p_{95}$ beyond 60 seconds.

---

## 2. Supporting Reliability Targets

| Indicator | Target | Remediation Threshold |
|---|---|---|
| **API Availability ($p_{99}$)** | 99.9% uptime | < 99.5% trips alert |
| **Validation / Quarantine Latency ($p_{95}$)** | $\le$ 50 ms | Sync validation in API process |
| **Error Budget Burn Rate** | < 1% of total runs resulting in `FAILED` status | > 2% triggers deployment rollback |
| **Rate Limiter Precision** | Zero false negatives beyond 60 req/min per client | Monitored via `bidscreen_rate_limit_total` |

---

## 3. Scaling & Capacity Model

Under a single Celery worker (`--concurrency=2`):
- Throughput capacity: $\sim 6$ to $10$ completed runs / minute.
- Saturation point: $\sim 8$ concurrent submitters.

Under scaled worker deployment (`--scale worker=3`, total 6 concurrent worker processes):
- Throughput capacity: $\sim 20$ to $30$ completed runs / minute.
- $p_{95}$ remains securely below 40 seconds at 20 concurrent users.

---

## 4. Verification Command
To verify this SLO in a local or CI staging environment:
```bash
locust -f loadtest/locustfile.py --headless -u 20 -r 5 --run-time 60s --host http://localhost:8000
```
Grafana panel: `Screening Run Duration (p95)` on dashboard `bidscreen-main`.
