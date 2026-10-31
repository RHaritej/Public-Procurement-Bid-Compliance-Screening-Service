# Bid Summary Data Contract Specification
**Tender ID:** `GEM/2026/B/8034326`  
**Package:** `bidscreen_contracts.bid_summary`  
**Schema File:** `contracts/schemas/bid_summary.schema.json`

---

## 1. Specification Overview
The `BidSummary` contract is the single source of truth for all structured bid representations evaluated by the screening engine. It models the bidder's declared credentials, financial history, past experience, and compliance certifications.

---

## 2. Field Definitions and Constraints

| Field Path | Type | Constraints / Rules | Description |
|---|---|---|---|
| `bid_ref` | `string` | 6 to 40 characters | Unique submission reference assigned by the procurement portal. |
| `tender_id` | `string` | Must equal `GEM/2026/B/8034326` | Strict tender lock; prevents screening against wrong bids. |
| `bidder.name` | `string` | 2 to 200 characters | Registered legal name of the entity. |
| `bidder.declared_category` | `enum` | `LARGE`, `MSE`, `STARTUP`, `CONSORTIUM`, `FOREIGN` | Declared business category. |
| `bidder.country_code` | `string` | ISO-3166-1 alpha-2 (e.g. `IN`, `US`, `CN`) | `FOREIGN` cannot be `IN`. |
| `bidder.land_border_registered` | `boolean` | Required if country is in `CN, PK, BD, NP, BT, MM, AF` | GTC Clause 26 registration status. |
| `bidder.incorporation_date` | `date` | `YYYY-MM-DD`, cannot be future | Date of incorporation. |
| `bidder.udyam_number` | `string` (opt) | Optional (Required if MSE) | MSME Udyam registration ID. |
| `bidder.startup_certificate_number`| `string` (opt) | Optional (Required if STARTUP) | DPIIT startup recognition certificate ID. |
| `bidder.annual_turnover_lakh` | `list[float]` | Exactly 3 items, non-negative | Turnover in INR Lakh for last 3 financial years. |
| `bidder.years_experience` | `float` | $\ge 0.0$ | Total verified years of similar service experience. |
| `bidder.similar_services` | `list[object]`| `{contract_value_lakh, client_type}` | List of previous service contracts. |
| `bidder.manpower_payroll_percent` | `float` | 0.0 to 100.0 | Manpower on payroll $\ge$ 1 year (ATC Clause 5). |
| `bidder.emd_submitted` | `boolean` | `true` or `false` | Whether EMD was deposited. |
| `bidder.emd_amount_inr` | `float` (opt) | $\ge 0$ | EMD amount in INR (Requirement: INR 117,600). |
| `bidder.emd_exemption_claimed` | `boolean` | `true` or `false` | Exemption claimed under policy rules. |
| `bidder.office_in_consignee_state` | `boolean` | `true` or `false` | Whether local service office exists (ATC Clause 2). |
| `bidder.documents_submitted` | `list[string]`| List of document IDs | List of submitted certificates and proof documents. |
| `notes` | `string` (opt) | Max 2000 chars | Free-text notes (scanned for prompt injection). |

---

## 3. Sample Compliant Payload (Section 4.1 Test Case)
```json
{
  "bid_ref": "BID-SANDES-2026-001",
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
    "similar_services": [
      { "contract_value_lakh": 120.0, "client_type": "CENTRAL" }
    ]
  },
  "notes": null
}
```
