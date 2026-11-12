"""Execution limits and timeouts configured via environment variables.
Reference: Section 4.2.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentLimits:
    max_steps: int = int(os.getenv("MAX_STEPS", "12"))
    max_tool_calls: int = int(os.getenv("MAX_TOOL_CALLS", "15"))
    run_timeout_s: float = float(os.getenv("RUN_TIMEOUT_S", "60.0"))
    max_verify_retries: int = int(os.getenv("MAX_VERIFY_RETRIES", "2"))
    llm_timeout_s: float = float(os.getenv("LLM_TIMEOUT_S", "20.0"))
    tool_timeout_s: float = float(os.getenv("TOOL_TIMEOUT_S", "5.0"))


# Global default instance
DEFAULT_LIMITS = AgentLimits()

