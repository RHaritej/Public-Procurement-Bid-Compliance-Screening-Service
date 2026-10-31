#!/usr/bin/env bash
# Demo 10: Full End-to-End Screening Flow (Submit -> Poll -> Trace -> Feedback)
set -euo pipefail
API_URL="${API_URL:-http://localhost:8000}"

echo "================================================================="
echo "DEMO 10: Complete E2E Lifecycle Demo"
echo "POST /v1/screenings -> GET /v1/screenings/{id} -> GET /v1/runs/{id}/trace -> POST feedback"
echo "================================================================="

echo "1. Submitting bid..."
RESP=$(curl -s -X POST "${API_URL}/v1/screenings" \
  -H "Content-Type: application/json" \
  -H "X-Client-Id: e2e-demo" \
  -d '{
    "bid_ref": "E2E-BID-COMPLETE",
    "tender_id": "GEM/2026/B/8034326",
    "bidder": {
      "name": "Sandes Prime Solutions",
      "declared_category": "STARTUP",
      "country_code": "IN",
      "incorporation_date": "2023-04-01",
      "startup_certificate_number": "DPIIT-TEST-0001",
      "annual_turnover_lakh": [40.0, 120.0, 200.0],
      "years_experience": 2.0,
      "manpower_payroll_percent": 25.0,
      "emd_submitted": true,
      "emd_amount_inr": 117600.0,
      "office_in_consignee_state": true,
      "documents_submitted": ["EXPERIENCE_PROOF", "TURNOVER_PROOF", "DPIIT_CERTIFICATE", "PAYROLL_PROOF"]
    }
  }')

RUN_ID=$(echo "${RESP}" | jq -r '.run_id')
echo "Created Run ID: ${RUN_ID}"

echo ""
echo "2. Polling result..."
sleep 2
RESULT=$(curl -s "${API_URL}/v1/screenings/${RUN_ID}")
echo "${RESULT}" | jq . || echo "${RESULT}"

echo ""
echo "3. Fetching execution trace..."
TRACE=$(curl -s "${API_URL}/v1/runs/${RUN_ID}/trace")
echo "${TRACE}" | jq . || echo "${TRACE}"

echo ""
echo "4. Submitting human verification feedback..."
FEEDBACK=$(curl -s -X POST "${API_URL}/v1/screenings/${RUN_ID}/feedback" \
  -H "Content-Type: application/json" \
  -d '{"satisfactory": true, "reason": "Accurate recommendation per DoE OM 20-09-2016."}')
echo "${FEEDBACK}" | jq . || echo "${FEEDBACK}"

echo ""
echo "5. Retrieving aggregated feedback summary..."
SUMMARY=$(curl -s "${API_URL}/v1/feedback/summary")
echo "${SUMMARY}" | jq . || echo "${SUMMARY}"

echo "E2E Demo Completed Successfully."
