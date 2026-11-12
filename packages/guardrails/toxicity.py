"""Toxicity, Hate Speech & Profanity Guardrail (Requirement L4).

Scans inputs (vendor notes, justifications) and outputs for toxic, abusive, or defamatory language.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple


TOXIC_TERMS = [
    r"\b(fraudster|corrupt|bribery|cheat|scam\s*artist|criminal)\b",
    r"\b(idiot|fool|stupid|moron)\b",
    r"\b(bastard|bitch|damn)\b",
]

COMPILED_TOXIC = [re.compile(p, re.IGNORECASE) for p in TOXIC_TERMS]


class ToxicityGuard:
    """Detects abusive, toxic, or defamatory language in bid text and agent outputs."""

    def __init__(self, patterns: Optional[List[re.Pattern]] = None):
        self.patterns = patterns or COMPILED_TOXIC

    def inspect_text(self, text: Optional[str]) -> Tuple[bool, Optional[str]]:
        if not text:
            return True, None

        for pattern in self.patterns:
            if pattern.search(text):
                return False, f"Toxicity / policy violation pattern detected: '{pattern.pattern}'"

        return True, None
