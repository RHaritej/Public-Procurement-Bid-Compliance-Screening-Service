"""Agent state definition for LangGraph workflow.
Reference: Section 4.2.
"""

from typing import TypedDict, List, Dict, Any, Optional
from bidscreen_contracts.enums import BidderCategory, Route, EscalationReason
from bidscreen_contracts.finding import Finding
from bidscreen_contracts.tools import Passage
from bidscreen_contracts.bid_summary import BidSummary


class AgentState(TypedDict, total=False):
    run_id: str
    correlation_id: str
    bid: BidSummary
    
    # Execution tracking
    step_count: int
    tool_call_count: int
    verify_retries: int
    current_strategy: str  # S1, S2, S3
    
    # Classifier outputs
    confirmed_category: Optional[BidderCategory]
    category_unclear: bool
    qualification_entities: Dict[str, Any]
    
    # Passage store (read-only to verifier)
    retrieved_passages: Dict[str, Passage]  # key: clause_id or passage_id
    
    # Analyst outputs
    findings: List[Finding]
    advisory_flags: List[str]
    
    # Verifier outputs
    verification_passed: bool
    verification_errors: List[str]
    
    # Router outputs
    route: Optional[Route]
    escalation_reason: Optional[EscalationReason]
    
    # Metadata and metrics
    prompt_versions: Dict[str, str]
    degraded: bool
    timings_ms: Dict[str, float]
    token_cost: Dict[str, Any]
    error: Optional[str]

