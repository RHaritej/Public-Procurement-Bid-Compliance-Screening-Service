"""Evaluation runner comparing analyst prompt versions (v1 vs v2).
Reference: Section 7 (Requirements L3, L5, L6).
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List

from bidscreen_contracts.bid_summary import BidSummary
from packages.agents.graph import run_screening
from packages.agents.tools.corpus_store import CORPUS_PASSAGES
from eval.metrics import evaluate_run

REPORTS_DIR = Path(__file__).parent / "reports"
SCENARIOS_PATH = Path(__file__).parent / "scenarios" / "scenarios.jsonl"


def load_scenarios() -> List[Dict[str, Any]]:
    scenarios = []
    with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                scenarios.append(json.loads(line.strip()))
    return scenarios


def run_evaluation_suite(prompt_version: str = "analyst@v2") -> Dict[str, Any]:
    scenarios = load_scenarios()
    results = []
    total_metrics = {
        "route_accuracy": 0.0,
        "groundedness": 0.0,
        "context_relevance": 0.0,
        "faithfulness": 0.0,
        "hallucination_rate": 0.0,
    }

    start_time = time.time()
    for sc in scenarios:
        sc_id = sc["scenario_id"]
        expected_route = sc["expected_route"]
        profile = sc.get("profile", "full")

        bid = BidSummary.model_validate(sc["bid"])
        run_id = f"eval-{prompt_version}-{sc_id}"
        correlation_id = f"corr-{sc_id}"

        res = run_screening(
            run_id=run_id,
            bid=bid,
            correlation_id=correlation_id,
            prompt_version=prompt_version,
            profile=profile,
        )

        metrics = evaluate_run(res, expected_route, CORPUS_PASSAGES)
        for k in total_metrics:
            total_metrics[k] += metrics[k]

        results.append({
            "scenario_id": sc_id,
            "name": sc["name"],
            "expected_route": expected_route,
            "actual_route": res.route.value,
            "escalation_reason": res.escalation_reason.value if res.escalation_reason else None,
            "metrics": metrics,
            "findings_count": len(res.findings),
            "advisory_flags_count": len(res.advisory_flags),
        })

    n = max(1, len(scenarios))
    avg_metrics = {k: round(v / n, 4) for k, v in total_metrics.items()}
    duration_s = round(time.time() - start_time, 2)

    report = {
        "prompt_version": prompt_version,
        "total_scenarios": len(scenarios),
        "evaluation_duration_seconds": duration_s,
        "average_metrics": avg_metrics,
        "scenario_results": results,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / f"eval_report_{prompt_version.replace('@', '_')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


def compare_prompt_versions() -> Dict[str, Any]:
    """Runs evaluation on v1 and v2, reporting deltas."""
    print("=" * 70)
    print("RUNNING PROMPT EVALUATION SUITE: analyst@v1 vs analyst@v2")
    print("=" * 70)

    report_v1 = run_evaluation_suite(prompt_version="analyst@v1")
    report_v2 = run_evaluation_suite(prompt_version="analyst@v2")

    v1_metrics = report_v1["average_metrics"]
    v2_metrics = report_v2["average_metrics"]

    comparison = {}
    print(f"\n{'Metric':<25} | {'analyst@v1':<12} | {'analyst@v2':<12} | {'Delta':<10}")
    print("-" * 65)

    for metric in v1_metrics:
        v1_val = v1_metrics[metric]
        v2_val = v2_metrics[metric]
        delta = round(v2_val - v1_val, 4)
        comparison[metric] = {
            "v1": v1_val,
            "v2": v2_val,
            "delta": delta,
        }
        sign = "+" if delta > 0 else ""
        print(f"{metric:<25} | {v1_val:<12.4f} | {v2_val:<12.4f} | {sign}{delta:<10.4f}")

    comp_report = {
        "comparison": comparison,
        "v1_summary": report_v1["average_metrics"],
        "v2_summary": report_v2["average_metrics"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    comp_file = REPORTS_DIR / "eval_comparison.json"
    with open(comp_file, "w", encoding="utf-8") as f:
        json.dump(comp_report, f, indent=2)

    print("\nComparison saved to:", comp_file)
    return comp_report


if __name__ == "__main__":
    compare_prompt_versions()

