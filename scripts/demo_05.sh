#!/usr/bin/env bash
# Demo 05: S10 - Land-Border Country Bidder Unregistered -> REJECT_WITH_CITED_CONDITION (MC-07)
set -euo pipefail
API_URL="${API_URL:-http://localhost:8000}"

echo "================================================================="
echo "DEMO 05: S10 - Land-Border Country Bidder Unregistered"
echo "Expected Route: REJECT_WITH_CITED_CONDITION (MC-07)"
echo "================================================================="

RESPONSE=$(curl -s -X POST "${API_URL}/v1/screenings" \
  -H "Content-Type: application/json" \
  -H "X-Client-Id: demo-script-05" \
  -d '{
    "bid_ref": "DEMO-S10-LAND-BORDER",
    "tender_id": "GEM/2026/B/8034326",
    "bidder": {
      "name": "East Asia Software Co",
      "declared_category": "FOREIGN",
      "country_code": "CN",
      "land_border_registered": false,
      "incorporation_date": "2012-08-01",
      "annual_turnover_lakh": [400.0, 450.0, 500.0],
      "years_experience": 6.0,
      "manpower_payroll_percent": 30.0,
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
