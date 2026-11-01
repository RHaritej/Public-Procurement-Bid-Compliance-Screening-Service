"""Input Prompt Injection & Adversarial Payload Guardrail (Requirement L4).

Detects and defangs attempts to manipulate or jailbreak LLM screening prompts.
Covers:
- System prompt overrides and instruction resets
- Markdown / LaTeX jailbreaks
- SQL/Code injection in free-text fields
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+prompt\s*(override|reset)",
    r"you\s+are\s+now\s+(an?|the)",
    r"bypass\s+(all\s+)?(rules|validation|checks|guardrails)",
    r"as\s+an\s+unrestricted\s+ai",
    r"jailbreak",
    r"do\s+anything\s+now",
    r"dan\s+mode",
    r"<script\b[^>]*>",
    r"exec\s*\(",
    r"eval\s*\(",
    r"drop\s+table",
    r"delete\s+from",
    r"UNION\s+SELECT",
]

COMPILED_INJECTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


class PromptInjectionGuard:
    """Validates and sanitizes free-text fields submitted in bids."""

    def __init__(self, patterns: Optional[List[re.Pattern]] = None):
        self.patterns = patterns or COMPILED_INJECTION_PATTERNS

    def inspect_text(self, text: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Checks if text contains prompt injection signals.

        Returns:
            (is_safe: bool, reason: Optional[str])
        """
        if not text:
            return True, None

        for pattern in self.patterns:
            if pattern.search(text):
                return False, f"Prompt injection pattern detected: '{pattern.pattern}'"

        return True, None

    def sanitize(self, text: str) -> str:
        """Strips control and escape characters."""
        if not text:
            return ""
        clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        return clean.strip()
