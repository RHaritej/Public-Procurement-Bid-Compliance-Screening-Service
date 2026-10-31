#!/usr/bin/env bash
# Demo 02: S04 - LARGE bidder meeting all conditions -> PASS_TO_TECHNICAL_EVALUATION
set -euo pipefail
API_URL="${API_URL:-http://localhost:8000}"

echo "================================================================="
echo "DEMO 02: S04 - Fully Compliant LARGE Bidder"
echo "Expected Route: PASS_TO_TECHNICAL_EVALUATION"
echo "================================================================="

RESPONSE=$(curl -s -X POST "${API_URL}/v1/screenings" \
  -H "Content-Type: application/json" \
  -H "X-Client-Id: demo-script-02" \
  -d '{
    "bid_ref": "DEMO-S04-COMPLIANT-LARGE",
    "tender_id": "GEM/2026/B/8034326",
    "bidder": {
      "name": "Tata Consultancy Services Ltd",
      "declared_category": "LARGE",
      "country_code": "IN",
      "incorporation_date": "2000-01-01",
      "annual_turnover_lakh": [350.0, 420.0, 500.0],
      "years_experience": 10.0,
      "manpower_payroll_percent": 85.0,
      "emd_submitted": true,
      "emd_amount_inr": 117600.0,
      "emd_exemption_claimed": false,
      "office_in_consignee_state": true,
      "documents_submitted": [
        "EXPERIENCE_PROOF",
        "TURNOVER_PROOF",
        "PAYROLL_PROOF"
      ],
      "similar_services": [{"contract_value_lakh": 250.0, "client_type": "CENTRAL"}]
    },
    "notes": null
  }')

echo "${RESPONSE}" | jq . || echo "${RESPONSE}"
RUN_ID=$(echo "${RESPONSE}" | jq -r '.run_id // empty')

if [ -n "${RUN_ID}" ]; then
  sleep 3
  curl -s "${API_URL}/v1/screenings/${RUN_ID}" | jq . || curl -s "${API_URL}/v1/screenings/${RUN_ID}"
fi
