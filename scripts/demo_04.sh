#!/usr/bin/env bash
# Demo 04: S07 - EMD Not Submitted without Exemption -> REJECT_WITH_CITED_CONDITION (MC-01)
set -euo pipefail
API_URL="${API_URL:-http://localhost:8000}"

echo "================================================================="
echo "DEMO 04: S07 - EMD Not Submitted"
echo "Expected Route: REJECT_WITH_CITED_CONDITION (MC-01)"
echo "================================================================="

RESPONSE=$(curl -s -X POST "${API_URL}/v1/screenings" \
  -H "Content-Type: application/json" \
  -H "X-Client-Id: demo-script-04" \
  -d '{
    "bid_ref": "DEMO-S07-NO-EMD",
    "tender_id": "GEM/2026/B/8034326",
    "bidder": {
      "name": "QuickTech India",
      "declared_category": "LARGE",
      "country_code": "IN",
      "incorporation_date": "2018-02-15",
      "annual_turnover_lakh": [300.0, 310.0, 320.0],
      "years_experience": 4.0,
      "manpower_payroll_percent": 25.0,
      "emd_submitted": false,
      "emd_amount_inr": 0,
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
