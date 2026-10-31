#!/usr/bin/env bash
# Demo 03: S03 - LARGE bidder below turnover threshold -> REJECT_WITH_CITED_CONDITION (MC-02)
set -euo pipefail
API_URL="${API_URL:-http://localhost:8000}"

echo "================================================================="
echo "DEMO 03: S03 - LARGE Bidder with Turnover Deficit (150 Lakh vs 235 Lakh)"
echo "Expected Route: REJECT_WITH_CITED_CONDITION (MC-02)"
echo "================================================================="

RESPONSE=$(curl -s -X POST "${API_URL}/v1/screenings" \
  -H "Content-Type: application/json" \
  -H "X-Client-Id: demo-script-03" \
  -d '{
    "bid_ref": "DEMO-S03-LARGE-DEFICIT",
    "tender_id": "GEM/2026/B/8034326",
    "bidder": {
      "name": "Infra Global Corp",
      "declared_category": "LARGE",
      "country_code": "IN",
      "incorporation_date": "2015-05-10",
      "annual_turnover_lakh": [140.0, 150.0, 160.0],
      "years_experience": 5.0,
      "manpower_payroll_percent": 30.0,
      "emd_submitted": true,
      "emd_amount_inr": 117600.0,
      "emd_exemption_claimed": false,
      "office_in_consignee_state": true,
      "documents_submitted": ["EXPERIENCE_PROOF", "TURNOVER_PROOF"],
      "similar_services": [{"contract_value_lakh": 50.0, "client_type": "STATE"}]
    },
    "notes": null
  }')

echo "${RESPONSE}" | jq . || echo "${RESPONSE}"
RUN_ID=$(echo "${RESPONSE}" | jq -r '.run_id // empty')

if [ -n "${RUN_ID}" ]; then
  sleep 3
  curl -s "${API_URL}/v1/screenings/${RUN_ID}" | jq . || curl -s "${API_URL}/v1/screenings/${RUN_ID}"
fi
