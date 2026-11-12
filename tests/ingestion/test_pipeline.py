"""Unit tests for Ingestion Pipeline and Chunking (Member B)."""

import json
from pathlib import Path
from ingestion.schema import CorpusChunk
from ingestion.pipeline import IngestionPipeline, CURATED_CHUNKS


def test_chunk_creation_and_hashing():
    chunk = CorpusChunk.create(
        doc_id="TEST_DOC",
        clause_id="TEST_DOC::CLAUSE_1",
        corpus="TENDER",
        text="Sample clause text for testing.",
        topics=["turnover"],
    )
    assert chunk.chunk_id.startswith("CHK-")
    assert chunk.doc_id == "TEST_DOC"
    assert chunk.corpus == "TENDER"
    assert "turnover" in chunk.topics


def test_ingestion_pipeline_run(tmp_path):
    output_file = tmp_path / "test_corpus_index.json"
    pipeline = IngestionPipeline(output_path=output_file)
    meta = pipeline.run()

    assert output_file.exists()
    assert meta["total_chunks"] >= len(CURATED_CHUNKS)

    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "chunks" in data
    assert len(data["chunks"]) == meta["total_chunks"]

    # Verify Section 4.1 essential clauses are present
    clause_ids = [c["clause_id"] for c in data["chunks"]]
    assert "GEM_BID_8034326::HDR.min_turnover" in clause_ids
    assert "DOE_OM_2016_09_20::P2" in clause_ids


def test_ingestion_idempotence(tmp_path):
    output_file = tmp_path / "test_corpus_index.json"
    pipeline = IngestionPipeline(output_path=output_file)
    meta1 = pipeline.run()
    meta2 = pipeline.run()

    assert meta1["total_chunks"] == meta2["total_chunks"]
