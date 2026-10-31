#!/usr/bin/env bash
# Demo 09: Worker Horizontal Scaling Benchmark Comparison
set -euo pipefail

echo "================================================================="
echo "DEMO 09: Worker Scaling Comparison (--scale worker=3)"
echo "Tests throughput improvement and queuing latency under worker scaling"
echo "================================================================="

echo "Checking running worker instances in Docker Compose..."
docker compose ps worker || echo "Docker not running in local script mode"

echo "Command to scale workers:"
echo "  docker compose up -d --scale worker=3"
echo "Running quick concurrency batch test via curl..."

API_URL="${API_URL:-http://localhost:8000}"

for i in {1..5}; do
  curl -s -X POST "${API_URL}/v1/screenings" \
    -H "Content-Type: application/json" \
    -H "X-Client-Id: batch-test" \
    -d '{
      "bid_ref": "BATCH-BID-'$i'",
      "tender_id": "GEM/2026/B/8034326",
      "bidder": {
        "name": "Scale Test Bidder '$i'",
        "declared_category": "LARGE",
        "country_code": "IN",
        "incorporation_date": "2015-01-01",
        "annual_turnover_lakh": [300.0, 310.0, 320.0],
        "years_experience": 5.0,
        "manpower_payroll_percent": 30.0,
        "emd_submitted": true,
        "emd_amount_inr": 117600.0,
        "office_in_consignee_state": true,
        "documents_submitted": ["EXPERIENCE_PROOF", "TURNOVER_PROOF"]
      }
    }' | jq -r '.run_id' &
done

wait
echo "Batch submit complete. Inspect Grafana dashboard at http://localhost:3001 for worker distribution."
