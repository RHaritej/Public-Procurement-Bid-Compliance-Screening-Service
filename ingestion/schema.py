"""Corpus chunk data models and schema definitions."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CorpusChunk(BaseModel):
    """Normalized chunk extracted from tender or policy documents."""

    chunk_id: str = Field(..., description="Unique chunk identifier, e.g. TENDER_CHUNK_001")
    doc_id: str = Field(..., description="Document ID or filename")
    clause_id: str = Field(..., description="Specific clause identifier, e.g. GEM_BID_8034326::HDR.min_turnover")
    corpus: str = Field(..., description="TENDER or POLICY")
    text: str = Field(..., min_length=1, description="Passage or clause text")
    topics: List[str] = Field(default_factory=list, description="Associated topics, e.g. turnover, experience, emd")
    applies_to: List[str] = Field(default_factory=list, description="Target bidder categories, e.g. STARTUP, MSE, ALL")
    legal_status: str = Field(default="IN_FORCE", description="IN_FORCE, SUPERSEDED, or ADVISORY")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata attributes")

    @classmethod
    def create(
        cls,
        doc_id: str,
        clause_id: str,
        corpus: str,
        text: str,
        topics: Optional[List[str]] = None,
        applies_to: Optional[List[str]] = None,
        legal_status: str = "IN_FORCE",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "CorpusChunk":
        raw_key = f"{doc_id}::{clause_id}::{text[:40]}"
        chunk_id = f"CHK-{hashlib.sha256(raw_key.encode('utf-8')).hexdigest()[:12].upper()}"
        return cls(
            chunk_id=chunk_id,
            doc_id=doc_id,
            clause_id=clause_id,
            corpus=corpus,
            text=text.strip(),
            topics=topics or [],
            applies_to=applies_to or ["ALL"],
            legal_status=legal_status,
            metadata=metadata or {},
        )
