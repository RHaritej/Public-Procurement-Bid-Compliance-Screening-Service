# Evaluation and Benchmark Report

**Author:** Member C (Agents & LLMOps)  
**System:** Bid Compliance Screening Service (UE24AM342AA5)  
**Evaluation Set:** 14 Standard Test Scenarios (`eval/scenarios/scenarios.jsonl`, S01–S14)  

---

## 1. Metrics and Mathematical Formulas

Evaluation is computed automatically across five quantitative dimensions:

### 1.1 Groundedness ($G$)
Measures the proportion of citations whose quoted text spans are verifiably grounded within the retrieved passages.

$$\text{Groundedness} = \frac{\sum_{i=1}^{N_{\text{citations}}} \mathbb{I}(\text{Quote}_i \subseteq \text{PassageText}_{\text{clause}_i})}{N_{\text{citations}}}$$

### 1.2 Context Relevance ($CR$)
Measures retrieval precision by computing the fraction of retrieved passages that are actively cited in the final findings.

$$\text{Context Relevance} = \frac{|\text{Retrieved Passages} \cap \text{Cited Passages}|}{|\text{Retrieved Passages}|}$$

### 1.3 Faithfulness ($F$)
Measures the factual consistency of the finding summaries against the cited clauses, penalizing ungrounded claims or missing citations on definitive findings.

$$\text{Faithfulness} = G \times \left(1.0 - 0.5 \times \frac{N_{\text{unsupported}}}{N_{\text{conditions}}}\right)$$

### 1.4 Hallucination Rate ($H$)
Measures the prevalence of ungrounded or fabricated citations.

$$\text{Hallucination Rate} = 1.0 - G$$

### 1.5 Route Accuracy ($RA$)
Measures exact agreement between the recommended route and ground-truth routing decisions.

$$\text{Route Accuracy} = \frac{1}{N_{\text{scenarios}}} \sum_{s=1}^{N_{\text{scenarios}}} \mathbb{I}(\text{Route}_{\text{actual}} = \text{Route}_{\text{expected}})$$

---

## 2. Benchmark Results: Before and After Deliberate Change

The deliberate change was the migration from `analyst@v1` (single-pass criteria lookup) to `analyst@v2` (multi-hop policy relaxation reasoning and citation length constraints).

### Comparison Summary Across S01–S14

| Metric | Baseline (`analyst@v1`) | Enhanced (`analyst@v2`) | Absolute Delta | Percentage Change |
| :--- | :---: | :---: | :---: | :---: |
| **Route Accuracy** | 78.57% | **100.00%** | **+21.43%** | **+27.3%** |
| **Groundedness** | 82.40% | **100.00%** | **+17.60%** | **+21.4%** |
| **Context Relevance** | 64.20% | **76.50%** | **+12.30%** | **+19.2%** |
| **Faithfulness** | 79.10% | **100.00%** | **+20.90%** | **+26.4%** |
| **Hallucination Rate** | 17.60% | **0.00%** | **-17.60%** | **-100.0%** |

---

## 3. Detailed Failure Analysis of Baseline (`v1`)

1. **Failure on S01 & S02 (Multi-Hop Startup Relaxation):**  
   `analyst@v1` evaluated the turnover of INR 120 lakh strictly against `HDR.min_turnover` (235 lakh) and recommended `REJECT_WITH_CITED_CONDITION (MC-02)`. It failed to query `DOE_OM_2016_09_20::P2`. In contrast, `analyst@v2` executed the second hop, discovered the policy relaxation, and correctly routed to `ESCALATE_TO_HUMAN` with reason `RULE_CONFLICT`.
2. **Failure on S06 (Startup EMD Exemption):**  
   `analyst@v1` treated startup EMD exemption claims as unverified rather than recognizing Conflict C7 (tender allows MSE only while DIPP requests startup inclusion). `analyst@v2` correctly identified the conflict and cited both `GEM_BID_8034326::EMD.a` and `DIPP_DO_2017_06_22::P4`.
3. **Citation Formatting Violations:**  
   `v1` yielded 4 citations exceeding the 40-word limit. `v2` had 0 violations.

