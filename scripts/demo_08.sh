#!/usr/bin/env bash
# Demo 08: S14 - Malformed payload / Field level error quarantine
set -euo pipefail
API_URL="${API_URL:-http://localhost:8000}"

echo "================================================================="
echo "DEMO 08: S14 - Malformed Request Validation Failure -> HTTP 422 QUARANTINE"
echo "Expected Response: HTTP 422 with quarantine_id and field-level errors"
echo "================================================================="

curl -i -X POST "${API_URL}/v1/screenings" \
  -H "Content-Type: application/json" \
  -H "X-Client-Id: demo-script-08" \
  -d '{
    "bid_ref": "INVALID",
    "tender_id": "WRONG_TENDER_ID",
    "bidder": {
      "name": "X",
      "declared_category": "STARTUP",
      "country_code": "INVALID_CODE",
      "incorporation_date": "2099-01-01",
      "annual_turnover_lakh": [-10.0, 50.0],
      "years_experience": -2.0,
      "manpower_payroll_percent": 150.0,
      "emd_submitted": true,
      "office_in_consignee_state": true
    }
  }'
