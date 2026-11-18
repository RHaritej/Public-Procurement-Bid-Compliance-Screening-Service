"""CLI Entry Point for Corpus Ingestion Pipeline (Requirement D2, L1).

Invocable from command-line: python -m ingestion.cli
Records data freshness and pipeline throughput.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from ingestion.pipeline import IngestionPipeline, INDEX_OUTPUT_PATH


def main():
    parser = argparse.ArgumentParser(description="BidScreen Corpus Ingestion Pipeline CLI")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=INDEX_OUTPUT_PATH,
        help="Path for generated corpus index JSON",
    )
    parser.add_argument(
        "--profile",
        "-p",
        type=str,
        default="full",
        choices=["full", "tender_core"],
        help="Corpus profile: full or tender_core (ablation)",
    )
    args = parser.parse_args()

    print(f"Starting ingestion pipeline (profile: {args.profile})...")
    start = time.time()
    pipeline = IngestionPipeline(output_path=args.output)
    metadata = pipeline.run()
    elapsed = time.time() - start

    chunks = metadata.get("total_chunks", 0)
    throughput = (chunks / elapsed) if elapsed > 0 else 0.0

    print("=================================================================")
    print(" CORPUS INGESTION SUCCESSFUL (IDEMPOTENT)")
    print("=================================================================")
    print(f"  • Freshness Timestamp : {metadata.get('generated_at')}")
    print(f"  • Total Chunks        : {chunks}")
    print(f"  • PDFs Scanned        : {metadata.get('pdf_sources_scanned')}")
    print(f"  • Ingestion Time      : {elapsed:.4f}s")
    print(f"  • Pipeline Throughput : {throughput:.2f} chunks/sec")
    print(f"  • Index Written To    : {args.output}")
    print("=================================================================")


if __name__ == "__main__":
    main()
