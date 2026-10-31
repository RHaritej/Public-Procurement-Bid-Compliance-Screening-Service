#!/usr/bin/env bash
# Demo 07: S12 - Consortium Bidder (Corpus Silent) -> ESCALATE_TO_HUMAN (NO_EVIDENCE_IN_CORPUS)
set -euo pipefail
API_URL="${API_URL:-http://localhost:8000}"

echo "================================================================="
echo "DEMO 07: S12 - Consortium Bidder"
echo "Expected Route: ESCALATE_TO_HUMAN (NO_EVIDENCE_IN_CORPUS)"
echo "================================================================="

RESPONSE=$(curl -s -X POST "${API_URL}/v1/screenings" \
  -H "Content-Type: application/json" \
  -H "X-Client-Id: demo-script-07" \
  -d '{
    "bid_ref": "DEMO-S12-CONSORTIUM",
    "tender_id": "GEM/2026/B/8034326",
    "bidder": {
      "name": "Alpha-Beta Consortium JV",
      "declared_category": "CONSORTIUM",
      "country_code": "IN",
      "incorporation_date": "2020-03-01",
      "annual_turnover_lakh": [300.0, 320.0, 350.0],
      "years_experience": 5.0,
      "manpower_payroll_percent": 40.0,
      "emd_submitted": true,
      "emd_amount_inr": 117600.0,
      "emd_exemption_claimed": false,
      "office_in_consignee_state": true,
      "documents_submitted": ["EXPERIENCE_PROOF", "TURNOVER_PROOF"]
    },
    "notes": null
  }')

echo "${RESPONSE}" | jq . || echo "${RESPONSE}"
RUN_ID=$(echo "${RESPONSE}" | jq -r '.run_id // empty')

if [ -n "${RUN_ID}" ]; then
  sleep 3
  curl -s "${API_URL}/v1/screenings/${RUN_ID}" | jq . || curl -s "${API_URL}/v1/screenings/${RUN_ID}"
fi
