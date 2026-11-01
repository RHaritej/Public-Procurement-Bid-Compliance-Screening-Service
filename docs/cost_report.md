# Cost and Token Economy Report

**Author:** Member C (Agents & LLMOps)  
**System:** Bid Compliance Screening Service (UE24AM342AA5)  

---

## 1. Cost Configuration & Pricing Model

In accordance with Section 4.1 and Rule 4, token rates are injected strictly through environment variables:
- `LLM_INPUT_COST_PER_M`: $0.15 per 1,000,000 prompt tokens
- `LLM_OUTPUT_COST_PER_M`: $0.60 per 1,000,000 completion tokens

$$\text{Cost} = \frac{\text{PromptTokens} \times 0.15 + \text{CompletionTokens} \times 0.60}{1,000,000}$$

---

## 2. Token and Cost Breakdown Per Screening Run

| Pipeline Stage / Node | Model / Method | Avg Prompt Tokens | Avg Completion Tokens | Cost Per Step (USD) | Share of Cost |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Classifier** | Rules First (No LLM) | 0 | 0 | $0.000000 | 0.0% |
| **Analyst Agent** | Multi-Hop Prompt (`v2`) | 1,450 | 380 | $0.000445 | **78.2%** |
| **Verifier Agent** | Verifier Prompt (`v1`) | 720 | 110 | $0.000124 | **21.8%** |
| **Router** | Deterministic Code | 0 | 0 | $0.000000 | 0.0% |
| **Total Per Run** | | **2,170** | **490** | **$0.000569** | **100.0%** |

---

## 3. Cost Per 100 Runs & Projected Workload

- **Cost per single run:** ~$0.00057 USD (INR 0.047)
- **Cost per 100 runs:** **$0.0569 USD** (~INR 4.75)
- **Cost per 10,000 submissions:** **$5.69 USD** (~INR 475)

---

## 4. Largest Cost Driver Analysis

**Identified Largest Cost Driver:** The **Analyst Agent** step, accounting for **78.2%** of total token consumption and inference cost.

### Contributing Factors:
1. **Multi-Hop Context Overhead:** The Analyst prompt ingests multiple retrieved passages across both tender clauses and policy circulars to evaluate all conditions MC-01 through MC-09.
2. **Structured Output Complexity:** Emitting detailed findings with citations and summaries increases completion token volume.

### Cost Optimization Strategies Implemented:
1. **Passage Chunk Pruning:** The retriever scopes chunk retrieval to only relevant topics rather than dumping full tender chapters.
2. **Deterministic Rules-First Classifier:** Resolves straightforward disqualifications (e.g. invalid consortium, over-age startups) without any LLM token usage.
3. **Response Caching (`ResponseCache`):** Identical bid submissions or repeated prompt queries hit memory cache, dropping LLM cost to $0.00.

