"""Ingestion package initialization."""

from ingestion.schema import CorpusChunk
from ingestion.pipeline import IngestionPipeline

__all__ = ["CorpusChunk", "IngestionPipeline"]
