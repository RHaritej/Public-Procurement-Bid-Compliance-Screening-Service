#!/usr/bin/env bash
# Demo 06: S11 - Turnover Proof Missing from Documents -> SEEK_CLARIFICATION
set -euo pipefail
API_URL="${API_URL:-http://localhost:8000}"

echo "================================================================="
echo "DEMO 06: S11 - Missing Mandatory Document (Turnover Proof)"
echo "Expected Route: SEEK_CLARIFICATION"
echo "================================================================="

RESPONSE=$(curl -s -X POST "${API_URL}/v1/screenings" \
  -H "Content-Type: application/json" \
  -H "X-Client-Id: demo-script-06" \
  -d '{
    "bid_ref": "DEMO-S11-MISSING-DOC",
    "tender_id": "GEM/2026/B/8034326",
    "bidder": {
      "name": "Beta Consultancy Services",
      "declared_category": "LARGE",
      "country_code": "IN",
      "incorporation_date": "2016-04-12",
      "annual_turnover_lakh": [280.0, 310.0, 340.0],
      "years_experience": 5.0,
      "manpower_payroll_percent": 30.0,
      "emd_submitted": true,
      "emd_amount_inr": 117600.0,
      "emd_exemption_claimed": false,
      "office_in_consignee_state": true,
      "documents_submitted": ["EXPERIENCE_PROOF"]
    },
    "notes": null
  }')

echo "${RESPONSE}" | jq . || echo "${RESPONSE}"
RUN_ID=$(echo "${RESPONSE}" | jq -r '.run_id // empty')

if [ -n "${RUN_ID}" ]; then
  sleep 3
  curl -s "${API_URL}/v1/screenings/${RUN_ID}" | jq . || curl -s "${API_URL}/v1/screenings/${RUN_ID}"
fi
