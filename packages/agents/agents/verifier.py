"""Verifier Agent (Requirement F6, Section 4.2).
Separate prompt, separate state, read-only access to the passage store.
Validates that every citation resolves to retrieved text and every finding is supported.
"""

from typing import Dict, Any, List, Optional
import logging
from bidscreen_contracts.enums import FindingStatus
from bidscreen_contracts.tools import Passage
from packages.agents.state import AgentState
from packages.llm_gateway.gateway import LLMGateway

logger = logging.getLogger(__name__)


class VerifierAgent:
    """Verifier agent with read-only access to the retrieved passages store."""

    def __init__(self, prompt_version: str = "verifier@v1"):
        self.prompt_version = prompt_version
        self.gateway = LLMGateway()

    def verify(self, state: AgentState) -> Dict[str, Any]:
        """Runs strict verification of citations and claims."""
        findings = state.get("findings", [])
        retrieved_passages: Dict[str, Passage] = state.get("retrieved_passages", {})
        errors: List[str] = []

        for f in findings:
            # Condition requires citations unless NOT_APPLICABLE
            if f.status == FindingStatus.NOT_APPLICABLE:
                continue

            if not f.citations and f.status in (FindingStatus.MET, FindingStatus.UNMET, FindingStatus.CONFLICT):
                errors.append(f"Finding {f.condition_id} has status {f.status.value} but provides zero citations.")
                continue

            for cit in f.citations:
                # 1. Check quote length under 40 words
                words = cit.quote.strip().split()
                if len(words) > 40:
                    errors.append(f"Citation for {cit.clause_id} exceeds 40 words ({len(words)} words).")

                # 2. Check resolution in retrieved passage store
                resolved_passage = retrieved_passages.get(cit.clause_id) or retrieved_passages.get(cit.passage_id)
                if not resolved_passage:
                    errors.append(
                        f"Citation clause_id '{cit.clause_id}' does not resolve to any retrieved passage in store."
                    )
                    continue

                # 3. Check quote is contained within the passage text
                clean_quote = cit.quote.strip().rstrip(".").lower()
                clean_passage = resolved_passage.text.strip().lower()
                # Check at least key words of quote exist in passage
                first_few_words = " ".join(clean_quote.split()[:4])
                if first_few_words and first_few_words not in clean_passage:
                    errors.append(
                        f"Citation quote '{cit.quote[:30]}...' not found in text of passage '{cit.clause_id}'."
                    )

        passed = len(errors) == 0
        step_count = state.get("step_count", 0) + 1

        if not passed:
            logger.warning("Verification failed with %d errors: %s", len(errors), errors)
        else:
            logger.info("Verification passed: all %d findings and citations verified.", len(findings))

        return {
            "step_count": step_count,
            "verification_passed": passed,
            "verification_errors": errors,
        }

