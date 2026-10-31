#!/usr/bin/env bash
# Demo 01: Section 4.1 Startup below turnover threshold -> ESCALATE_TO_HUMAN (Conflict C1)
set -euo pipefail
API_URL="${API_URL:-http://localhost:8000}"

echo "================================================================="
echo "DEMO 01: S01 - Section 4.1 Test Case (Startup below Turnover)"
echo "Expected Route: ESCALATE_TO_HUMAN"
echo "Expected Findings: MC-02 CONFLICT, MC-03 CONFLICT"
echo "================================================================="

RESPONSE=$(curl -s -X POST "${API_URL}/v1/screenings" \
  -H "Content-Type: application/json" \
  -H "X-Client-Id: demo-script-01" \
  -d '{
    "bid_ref": "DEMO-S01-STARTUP",
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
      "similar_services": [{"contract_value_lakh": 120.0, "client_type": "CENTRAL"}]
    },
    "notes": null
  }')

echo "Submission Response:"
echo "${RESPONSE}" | jq . || echo "${RESPONSE}"
RUN_ID=$(echo "${RESPONSE}" | jq -r '.run_id // empty')

if [ -n "${RUN_ID}" ]; then
  echo ""
  echo "Polling run status for: ${RUN_ID}..."
  sleep 3
  curl -s "${API_URL}/v1/screenings/${RUN_ID}" | jq . || curl -s "${API_URL}/v1/screenings/${RUN_ID}"
fi
