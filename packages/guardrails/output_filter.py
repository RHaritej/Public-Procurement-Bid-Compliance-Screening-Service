"""Output Determination Boundary Guardrail (Requirement L4, Section 2).

Enforces strict system boundaries:
The Bid Compliance Screening Service NEVER rejects or qualifies a bid.
It ONLY produces advisory findings and recommended routes for a tender committee.
If an agent or model attempts to issue a definitive legal qualification or rejection,
this guardrail intercepts, redacts, and normalizes the output.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


FORBIDDEN_DETERMINATIONS = [
    r"\b(we\s+hereby\s+reject\s+this\s+bid)\b",
    r"\b(this\s+bid\s+is\s+hereby\s+disqualified)\b",
    r"\b(the\s+bidder\s+is\s+hereby\s+awarded\s+the\s+contract)\b",
    r"\b(tender\s+is\s+awarded\s+to)\b",
    r"\b(final\s+binding\s+disqualification)\b",
]

COMPILED_FORBIDDEN = [re.compile(p, re.IGNORECASE) for p in FORBIDDEN_DETERMINATIONS]

ADVISORY_DISCLAIMER = (
    "DISCLAIMER: The screening service produces pre-qualification recommendations only. "
    "All decisions remain subject to official tender committee determination."
)


class OutputFilterGuard:
    """Guards against unauthorized authoritative determinations by agents/LLMs."""

    def __init__(self, patterns: Optional[List[re.Pattern]] = None):
        self.patterns = patterns or COMPILED_FORBIDDEN

    def validate_output(self, text: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Verifies that output text does not claim authoritative legal determination."""
        if not text:
            return True, None

        for pattern in self.patterns:
            if pattern.search(text):
                return False, f"Unauthorized authoritative determination detected: '{pattern.pattern}'"

        return True, None

    def sanitize_output(self, text: str) -> str:
        """Normalizes and appends disclaimer if unauthorized wording is found."""
        if not text:
            return ""
        sanitized = text
        for pattern in self.patterns:
            sanitized = pattern.sub("[ADVISORY RECOMMENDATION ONLY]", sanitized)
        return sanitized
