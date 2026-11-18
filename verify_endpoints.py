import urllib.request
import json

endpoints = [
    ("LLM Stub", "http://127.0.0.1:8003/health"),
    ("Retrieval", "http://127.0.0.1:8002/health"),
    ("API Health", "http://127.0.0.1:8000/health"),
    ("API Docs", "http://127.0.0.1:8000/docs"),
    ("Web Frontend", "http://127.0.0.1:3000/index.html")
]

print("=== CHECKING RUNNING ENDPOINTS ===")
for name, url in endpoints:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = resp.read()
            print(f"[OK] {name} ({url}) -> Status: {resp.status}, Bytes: {len(data)}")
    except Exception as e:
        print(f"[FAIL] {name} ({url}) -> Error: {e}")

print("\n=== SUBMITTING SAMPLE PROCUREMENT BID ===")
sample_bid = {
    "bid_ref": "BID-2026-LIVE-TEST",
    "tender_id": "GEM/2026/B/8034326",
    "bidder": {
        "name": "Live Test Startup Technologies Pvt Ltd",
        "declared_category": "STARTUP",
        "country_code": "IN",
        "incorporation_date": "2023-04-01",
        "startup_certificate_number": "DPIIT-LIVE-001",
        "annual_turnover_lakh": [40.0, 120.0, 200.0],
        "years_experience": 2.0,
        "manpower_payroll_percent": 20.0,
        "emd_submitted": True,
        "emd_amount_inr": 117600.0,
        "emd_exemption_claimed": False,
        "office_in_consignee_state": True,
        "documents_submitted": [
            "EXPERIENCE_PROOF",
            "TURNOVER_PROOF",
            "DPIIT_CERTIFICATE",
            "PAYROLL_PROOF"
        ],
        "similar_services": [
            {"contract_value_lakh": 120.0, "client_type": "CENTRAL"}
        ]
    },
    "notes": "Testing live submission through screening agent"
}

try:
    req = urllib.request.Request(
        "http://127.0.0.1:8000/v1/screenings",
        data=json.dumps(sample_bid).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Client-Id": "live-tester", "X-Correlation-ID": "corr-live-001"}
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        submit_res = json.loads(resp.read().decode("utf-8"))
        print(f"[SUBMISSION ACCEPTED] HTTP {resp.status}")
        print("Submission response:", json.dumps(submit_res, indent=2))
        run_id = submit_res["run_id"]
        status_url = f"http://127.0.0.1:8000/v1/screenings/{run_id}"

    # Poll for completion
    import time
    for attempt in range(10):
        time.sleep(1)
        with urllib.request.urlopen(status_url, timeout=5) as poll_resp:
            run_data = json.loads(poll_resp.read().decode("utf-8"))
            current_status = run_data.get("status")
            print(f"Polling {attempt + 1}: Status = {current_status}")
            if current_status in ("COMPLETED", "FAILED"):
                print("\n=== FINAL SCREENING RESULT & TRACE ===")
                print(json.dumps(run_data, indent=2))
                break
except Exception as e:
    import traceback
    traceback.print_exc()

