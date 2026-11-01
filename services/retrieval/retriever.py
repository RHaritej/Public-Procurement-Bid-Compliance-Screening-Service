"""Multi-Hop Retrieval Engine for Tender and Policy Corpora (Requirement L1, F4).

Improves beyond single-pass dense retrieval by supporting:
1. Direct Clause Lookup (exact ID)
2. Scoped Keyword & Semantic Search
3. Cross-Document Modifying Provision Discovery (e.g., Startup/MSE relaxations)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ingestion.schema import CorpusChunk
from ingestion.pipeline import INDEX_OUTPUT_PATH, IngestionPipeline


class MultiHopRetriever:
    """Retrieves clauses and cross-references statutory relaxations across tender and policy corpora."""

    def __init__(self, index_path: Optional[Path] = None):
        self.index_path = index_path or INDEX_OUTPUT_PATH
        self.chunks: List[CorpusChunk] = []
        self._clause_map: Dict[str, CorpusChunk] = {}
        self._load_or_build_index()

    def _load_or_build_index(self) -> None:
        if not self.index_path.exists():
            pipeline = IngestionPipeline(self.index_path)
            pipeline.run()

        with open(self.index_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.chunks = [CorpusChunk(**item) for item in data.get("chunks", [])]
        self._clause_map = {c.clause_id: c for c in self.chunks}

    def get_clause(self, clause_id: str) -> Optional[CorpusChunk]:
        """Fetch exact clause by ID."""
        return self._clause_map.get(clause_id)

    def search(
        self,
        query: str,
        corpus_scope: str = "ALL",  # TENDER, POLICY, or ALL
        applies_to: Optional[str] = None,
        topics: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Multi-criteria search over chunks."""
        query_words = set(query.lower().split())
        scored: List[tuple[float, CorpusChunk]] = []

        for chunk in self.chunks:
            # Corpus filter
            if corpus_scope != "ALL" and chunk.corpus != corpus_scope:
                continue

            # Bidder category filter
            if applies_to and applies_to not in chunk.applies_to and "ALL" not in chunk.applies_to:
                continue

            # Topic filter
            if topics:
                if not any(t.lower() in [ct.lower() for ct in chunk.topics] for t in topics):
                    continue

            # Relevance scoring
            text_lower = chunk.text.lower()
            clause_lower = chunk.clause_id.lower()
            score = 0.0

            for word in query_words:
                if word in text_lower:
                    score += 1.0
                if word in clause_lower:
                    score += 2.0
                if any(word in t.lower() for t in chunk.topics):
                    score += 1.5

            if score > 0.0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, chunk in scored[:top_k]:
            results.append({
                "chunk_id": chunk.chunk_id,
                "clause_id": chunk.clause_id,
                "doc_id": chunk.doc_id,
                "corpus": chunk.corpus,
                "text": chunk.text,
                "score": round(score, 3),
                "metadata": chunk.metadata,
            })
        return results

    def find_modifying_provisions(
        self,
        condition_id: str,
        bidder_category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Discovers statutory or policy clauses that modify/relax a tender condition."""
        modifying: List[Dict[str, Any]] = []

        for chunk in self.chunks:
            modifies = chunk.metadata.get("modifies", [])
            # Also check if topics match relaxation + condition
            is_match = condition_id in modifies
            if not is_match and "relaxation" in [t.lower() for t in chunk.topics]:
                if condition_id == "MC-02" and "turnover" in [t.lower() for t in chunk.topics]:
                    is_match = True
                elif condition_id == "MC-03" and "experience" in [t.lower() for t in chunk.topics]:
                    is_match = True
                elif condition_id == "MC-01" and "emd" in [t.lower() for t in chunk.topics]:
                    is_match = True

            if is_match:
                if bidder_category and bidder_category not in chunk.applies_to and "ALL" not in chunk.applies_to:
                    continue
                modifying.append({
                    "clause_id": chunk.clause_id,
                    "doc_id": chunk.doc_id,
                    "corpus": chunk.corpus,
                    "text": chunk.text,
                    "effect": "RELAXES",
                    "legal_status": chunk.legal_status,
                })
        return modifying
