"""FastAPI Microservice for Corpus Retrieval (:8002).

Exposes HTTP endpoints conforming to docker-compose.yml service `retrieval:8002`.
Endpoints:
- GET /health
- POST /retrieve
- POST /clause
- POST /modifying
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from services.retrieval.retriever import MultiHopRetriever

app = FastAPI(
    title="BidScreen Corpus Retrieval Service",
    description="Multi-Hop Statutory and Tender Retrieval Microservice",
    version="1.0.0",
)

retriever = MultiHopRetriever()


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1)
    corpus_scope: str = Field(default="ALL")
    applies_to: Optional[str] = Field(default=None)
    topics: Optional[List[str]] = Field(default=None)
    top_k: int = Field(default=5, ge=1, le=20)


class ClauseRequest(BaseModel):
    clause_id: str = Field(...)


class ModifyingRequest(BaseModel):
    condition_id: str = Field(...)
    bidder_category: Optional[str] = Field(default=None)


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "service": "retrieval",
        "indexed_chunks": len(retriever.chunks),
    }


@app.post("/retrieve", tags=["Retrieval"])
def retrieve(req: RetrieveRequest):
    results = retriever.search(
        query=req.query,
        corpus_scope=req.corpus_scope,
        applies_to=req.applies_to,
        topics=req.topics,
        top_k=req.top_k,
    )
    return {
        "query": req.query,
        "results": results,
        "total_results": len(results),
    }


@app.post("/clause", tags=["Retrieval"])
def get_clause(req: ClauseRequest):
    chunk = retriever.get_clause(req.clause_id)
    if not chunk:
        raise HTTPException(status_code=404, detail=f"Clause '{req.clause_id}' not found.")
    return chunk.model_dump()


@app.post("/modifying", tags=["Retrieval"])
def find_modifying(req: ModifyingRequest):
    results = retriever.find_modifying_provisions(
        condition_id=req.condition_id,
        bidder_category=req.bidder_category,
    )
    return {
        "condition_id": req.condition_id,
        "bidder_category": req.bidder_category,
        "provisions": results,
        "conflict_detected": len(results) > 0,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.retrieval.main:app", host="0.0.0.0", port=8002)
