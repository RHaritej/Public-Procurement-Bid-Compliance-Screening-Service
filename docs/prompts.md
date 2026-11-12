# Prompt Engineering and Versioning Report

**Author:** Member C (Agents & LLMOps)  
**System:** Bid Compliance Screening Service (UE24AM342AA5)  

---

## 1. Prompt Registry Architecture

Prompts are managed as versioned YAML assets residing under `prompts/` and indexed in `prompts/registry.yaml` (Requirement L2). This prevents prompt drift, enables reproducible evaluations, and decouples prompt lifecycle management from application code.

```yaml
prompts:
  analyst:
    active_version: "v2"
    versions:
      v1: "prompts/analyst/v1.yaml"
      v2: "prompts/analyst/v2.yaml"
  verifier:
    active_version: "v1"
    versions:
      v1: "prompts/verifier/v1.yaml"
```

---

## 2. Evolution: `analyst@v1` vs `analyst@v2`

### Baseline Prompt (`analyst@v1`)
- **Design Philosophy:** Direct criteria check. Prompted the model to check mandatory conditions MC-01 through MC-09 against the bid summary.
- **Identified Weaknesses:**
  1. Failed to consistently execute second-hop retrieval into the Policy corpus when a Startup or MSE failed numeric thresholds, resulting in false rejections on tender core ablation profiles.
  2. Frequently generated quotes exceeding 40 words or loosely paraphrased text spans, failing Verifier constraints.
  3. Omitted crucial advisory flags for QCBS technical evaluation cut-offs.

### Enhanced Prompt (`analyst@v2`)
- **Key Enhancements (The Deliberate Change for L3):**
  1. **Explicit Two-Hop Policy Guidance:** Explicit instruction that Startups and MSEs below turnover or experience thresholds must be evaluated for conditional relaxation against tender clauses (`MII.4`, `MII.3`) and DoE policy circulars (`DOE_OM_2016_09_20::P2`).
  2. **Mandatory CONFLICT Status:** Strict instruction that relaxation is conditional on meeting quality specifications; therefore, status must be `CONFLICT` (never an automatic pass).
  3. **Strict Citation Constraint:** Hard constraint that all quotes must be verbatim substrings under 40 words, citing valid `clause_id` and `passage_id`.
  4. **Advisory Flag Enforcement:** Explicit rule to surface QCBS evaluation cut-offs (`TENDER_QCBS::NOTE3`) whenever relaxations are triggered.

---

## 3. Verifier Prompt (`verifier@v1`)
Designed with zero tolerance for hallucinations:
- Evaluates citations strictly against the session passage store.
- Enforces quote length $\le 40$ words.
- Rejects any finding where the stated summary claim is unsupported by the cited text.

