# Public Procurement Bid Compliance Screening Service
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0-009688.svg)](https://fastapi.tiangolo.com)
[![Celery](https://img.shields.io/badge/Celery-5.6-37814A.svg)](https://docs.celeryq.dev)
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-v2-2496ED.svg)](https://docs.docker.com/compose/)

Autonomous pre-qualification and mandatory compliance screening service for public procurement tenders on the Government e-Marketplace (**GeM**).

Target Tender: **`GEM/2026/B/8034326`** (National Informatics Centre, 5 Onsite Professionals, Closed 28-09-2026).

---

## 1. Team Ownership & Responsibilities (§5)

| Member | Focus Area | Owned Codepaths & Components |
|---|---|---|
| **Hari Tej** *(Integration & Reliability Lead)* | **Platform & Reliability** | `contracts/`, `services/api/`, `services/worker/`, `services/llm_stub/`, `services/web/`, `packages/common/`, `infra/`, `loadtest/`, `scripts/`, `docker-compose.yml`, `Makefile`, `CODEOWNERS`, `docs/slo.md`, `docs/runbook.md`, `docs/architecture.md`, `docs/data_contract.md` |
| **Sri Ram V** | **Knowledge, Retrieval & Safety** | `corpus/`, `ingestion/`, `services/retrieval/`, `packages/guardrails/`, `eval/scenarios/`, `docs/corpus_and_chunking.md`, `docs/guardrails.md` |
| **Prithviraj** | **Agents & LLMOps** | `packages/agents/`, `packages/llm_gateway/`, `prompts/`, `eval/run_eval.py`, `docs/agent_design.md`, `docs/prompts.md`, `docs/eval_report.md` |

---

## 2. Quickstart

### Prerequisites
- Python 3.11+
- Docker & Docker Compose

### Local Development Setup
```bash
# 1. Clone repository
git clone <repo-url>
cd Public-Procurement-Bid-Compliance-Screening-Service

# 2. Configure environment
cp .env.example .env

# 3. Install shared contracts and common utilities locally
make setup

# 4. Start all services via Docker Compose
make up
```

All microservices will spin up:
- **Web UI:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Gateway & Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Prometheus:** [http://localhost:9090](http://localhost:9090)
- **Grafana Dashboard:** [http://localhost:3001](http://localhost:3001) (Credentials: `admin` / `admin`)
- **Jaeger Distributed Tracing:** [http://localhost:16686](http://localhost:16686)
- **LLM Stub:** [http://localhost:8003](http://localhost:8003)

---

## 3. Architecture & Service Boundaries

```
[Web UI / Client] 
        │  (HTTP POST /v1/screenings)
        ▼
[FastAPI Gateway :8000] ──> Validation ──[Invalid]──> [Quarantine Store]
        │ (Valid)
        ├──> Sliding Window Rate Limiter (Redis)
        ├──> Enqueue Screening Task
        ▼
[Redis Broker :6379]
        │
        ▼
[Celery Worker :8001] (--scale worker=3)
        │
        ├──> Classifier Node (Entities & Category)
        ├──> Multi-hop Retrieval (Chroma :8002)
        ├──> Analyst Agent <─> Tools (Thresholds, Modifying Provisions)
        ├──> Verifier Agent (Citation Groundedness Gate)
        └──> Deterministic Router Table (§4.3)
        │
        ▼
[PostgreSQL Database :5432] ──> Results, Traces, Human Feedback
```

---

## 4. API Usage Examples

### 4.1 Submit Bid for Screening (`POST /v1/screenings`)
```bash
curl -X POST "http://localhost:8000/v1/screenings" \
  -H "Content-Type: application/json" \
  -H "X-Client-Id: client-portal-01" \
  -H "X-Correlation-ID: custom-corr-101" \
  -d '{
    "bid_ref": "BID-SANDES-2026-001",
    "tender_id": "GEM/2026/B/8034326",
    "bidder": {
      "name": "Sandes Tech Labs Pvt Ltd",
      "declared_category": "STARTUP",
      "country_code": "IN",
      "incorporation_date": "2023-04-01",
      "startup_certificate_number": "DPIIT-TEST-0001",
      "annual_turnover_lakh": [40.0, 120.0, 200.0],
      "years_experience": 2.0,
      "manpower_payroll_percent": 20.0,
      "emd_submitted": true,
      "emd_amount_inr": 117600.0,
      "emd_exemption_claimed": false,
      "office_in_consignee_state": true,
      "documents_submitted": [
        "EXPERIENCE_PROOF",
        "TURNOVER_PROOF",
        "DPIIT_CERTIFICATE",
        "PAYROLL_PROOF"
      ],
      "similar_services": [
        {"contract_value_lakh": 120.0, "client_type": "CENTRAL"}
      ]
    },
    "notes": null
  }'
```
**Response (HTTP 202 Accepted):**
```json
{
  "run_id": "9a0a03bb-cbcf-44b4-82a9-063a5ba85770",
  "status": "QUEUED",
  "status_url": "/v1/screenings/9a0a03bb-cbcf-44b4-82a9-063a5ba85770",
  "correlation_id": "custom-corr-101",
  "created_at": "2026-10-31T20:00:00Z"
}
```

### 4.2 Poll Screening Status & Findings (`GET /v1/screenings/{run_id}`)
```bash
curl "http://localhost:8000/v1/screenings/9a0a03bb-cbcf-44b4-82a9-063a5ba85770"
```
**Completed Response:**
```json
{
  "run_id": "9a0a03bb-cbcf-44b4-82a9-063a5ba85770",
  "status": "COMPLETED",
  "recommended_route": "ESCALATE_TO_HUMAN",
  "escalation_reason": "RULE_CONFLICT",
  "findings": [
    {
      "condition_id": "MC-02",
      "condition_name": "Average Annual Turnover (Threshold: 235 Lakh)",
      "status": "CONFLICT",
      "citations": [
        {
          "clause_id": "GEM_BID_8034326::HDR.min_turnover",
          "quoted_text": "Minimum Average Annual Turnover of the bidder: 235 Lakhs."
        },
        {
          "clause_id": "DOE_OM_2016_09_20::P2",
          "quoted_text": "Prior turnover and prior experience relaxed for all Startups (whether MSE or not) subject to technical capability."
        }
      ]
    }
  ],
  "agent_steps": 4,
  "tool_calls": 5,
  "llm_cost_usd": 0.0052
}
```

### 4.3 Inspect Full Multi-Agent Trace (`GET /v1/runs/{run_id}/trace`)
```bash
curl "http://localhost:8000/v1/runs/9a0a03bb-cbcf-44b4-82a9-063a5ba85770/trace"
```

### 4.4 Submit Operator Feedback (`POST /v1/screenings/{run_id}/feedback`)
```bash
curl -X POST "http://localhost:8000/v1/screenings/9a0a03bb-cbcf-44b4-82a9-063a5ba85770/feedback" \
  -H "Content-Type: application/json" \
  -d '{"satisfactory": true, "reason": "Verified conflict correctly identified"}'
```

---

## 5. Automated Demo Scripts

Run the verification scripts located in `scripts/`:
```bash
# Run Section 4.1 startup conflict demo
make demo-01

# Run all automated scenarios
make demo-all
```

---

## 6. Testing & SLO Verification

```bash
# Run full API and validation test suite
make test

# Run Locust benchmark to verify p95 <= 60s at 20 concurrent submitters
make loadtest
```


---

## 7. Knowledge, Ingestion, Retrieval & Safety Implementation (Sri Ram V)

### 7.1 Ingestion Pipeline (`ingestion/`)
- **Pipeline (`ingestion/pipeline.py`):** Idempotent CLI tool that reads, parses, chunks, and metadata-tags the procurement corpus into structured semantic clauses with deterministic SHA-256 chunk identifiers.
- **Corpus Catalog (`corpus/corpus_index.json`):** Persisted catalog of 16 core tender and statutory policy clauses with freshness timestamps and page numbers.
- **Data Models (`ingestion/schema.py`):** Pydantic `CorpusChunk` model capturing `chunk_id`, `clause_id`, `corpus` (`TENDER` vs `POLICY`), `topics`, `applies_to` bidder categories, `legal_status`, and `metadata`.
- **Run Ingestion:**
  ```bash
  python -m ingestion.pipeline
  ```

### 7.2 Multi-Hop Retrieval Service (`services/retrieval/`)
- **Retriever Engine (`services/retrieval/retriever.py`):**
  - **S1 (Clause Lookup):** Direct lookup by exact canonical ID (`get_clause`).
  - **S2 (Scoped Keyword Search):** Multi-criteria filtering by corpus scope (`TENDER`, `POLICY`, `ALL`), target category, and topics (`search`).
  - **S3 (Modifying Provisions):** Cross-document discovery of statutory relaxations (e.g. DoE OM 2016-09-20, GFR Rule 170) modifying tender conditions (`find_modifying_provisions`).
- **REST Service (`services/retrieval/main.py`):** Standalone FastAPI microservice on port `:8002` with endpoints:
  - `GET /health` - Health check and indexed chunk counter.
  - `POST /retrieve` - Multi-criteria search.
  - `POST /clause` - Exact clause retrieval.
  - `POST /modifying` - Modifying provisions and conflict detection.

### 7.3 Guardrails & Safety Engine (`packages/guardrails/`)
- **Prompt Injection Defense (`packages/guardrails/prompt_injection.py`):** Detects instruction overrides, system prompt resets, jailbreak phrases, and script/code injection across free-text fields.
- **Output Boundary Guard (`packages/guardrails/output_filter.py`):** Enforces Section 2 boundary invariant (system never makes binding legal rejections or awards; advisory recommendations only) with automatic disclaimers and redactions.
- **Toxicity Filter (`packages/guardrails/toxicity.py`):** Filters abusive, defamatory, and corrupt claims in bid text and agent outputs.
- **Unified Engine (`packages/guardrails/engine.py`):** `validate_input(text)` and `validate_output(text)` returning structured `GuardrailResult` status.

### 7.4 Evaluation Scenarios (`eval/scenarios/`)
- **21 Fixed Scenarios (`eval/scenarios/scenarios.jsonl`):** Comprehensive benchmark covering Section 4.1 startup conflict, index ablation profiles, MSE relaxations, missing documentation, land-border checks, consortium edge cases, and adversarial guardrail injection attempts (S16 & S19).

### 7.5 Technical Documentation
- **[docs/corpus_and_chunking.md](file:///d:/Public-Procurement-Bid-Compliance-Screening-Service/Public-Procurement-Bid-Compliance-Screening-Service/docs/corpus_and_chunking.md):** Detailed analysis of two-corpus conflict, semantic clause chunking, metadata indexing, and multi-hop retrieval architecture.
- **[docs/guardrails.md](file:///d:/Public-Procurement-Bid-Compliance-Screening-Service/Public-Procurement-Bid-Compliance-Screening-Service/docs/guardrails.md):** Defense-in-depth safety specifications, prompt injection patterns, and legal boundary enforcement.
