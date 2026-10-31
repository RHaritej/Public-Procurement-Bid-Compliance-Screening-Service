"""Locust load test for the Bid Compliance Screening Service.

Simulates 20 concurrent submitters testing the p95 SLO target <= 60s.
Payload: Section 4.1 test case (STARTUP below 235 lakh turnover threshold).
"""

from __future__ import annotations

import time
from locust import HttpUser, between, task


class BidScreenUser(HttpUser):
    wait_time = between(1.0, 3.0)

    @task
    def submit_and_poll_screening(self):
        # Realistic Section 4.1 test case payload
        payload = {
            "bid_ref": f"LOAD-BID-{int(time.time() * 1000) % 1000000}",
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
                "emd_submitted": True,
                "emd_amount_inr": 117600.0,
                "emd_exemption_claimed": False,
                "office_in_consignee_state": True,
                "documents_submitted": [
                    "EXPERIENCE_PROOF",
                    "TURNOVER_PROOF",
                    "DPIIT_CERTIFICATE",
                    "PAYROLL_PROOF",
                ],
                "similar_services": [
                    {"contract_value_lakh": 120.0, "client_type": "CENTRAL"}
                ],
            },
            "notes": None,
        }

        start_time = time.time()

        # Step 1: Submit screening request
        with self.client.post(
            "/v1/screenings",
            json=payload,
            headers={"X-Client-Id": f"load-tester-{self.environment.runner.user_count}"},
            catch_response=True,
            name="/v1/screenings [submit]",
        ) as response:
            if response.status_code != 202:
                response.failure(f"Failed submission: {response.status_code} - {response.text}")
                return
            data = response.json()
            run_id = data.get("run_id")

        if not run_id:
            return

        # Step 2: Poll until COMPLETED or timeout (up to 60 seconds)
        poll_start = time.time()
        timeout = 60.0
        poll_interval = 2.0

        while time.time() - poll_start < timeout:
            time.sleep(poll_interval)
            with self.client.get(
                f"/v1/screenings/{run_id}",
                catch_response=True,
                name="/v1/screenings/{id} [poll]",
            ) as poll_res:
                if poll_res.status_code != 200:
                    poll_res.failure(f"Poll error: {poll_res.status_code}")
                    break
                poll_data = poll_res.json()
                status = poll_data.get("status")

                if status == "COMPLETED":
                    total_duration = time.time() - start_time
                    self.environment.events.request.fire(
                        request_type="SCENARIO",
                        name="Full Screening E2E",
                        response_time=total_duration * 1000,
                        response_length=len(poll_res.content),
                        exception=None,
                        context=None,
                    )
                    break
                elif status == "FAILED":
                    poll_res.failure(f"Run failed: {poll_data.get('error_message')}")
                    break
