"""Root pytest configuration setting sys.path for all modules and packages."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

# Ensure all packages and submodules are importable across test suites
paths = [
    ROOT_DIR,
    ROOT_DIR / "contracts",
    ROOT_DIR / "packages" / "common",
    ROOT_DIR / "packages" / "agents",
    ROOT_DIR / "packages" / "llm_gateway",
    ROOT_DIR / "packages" / "guardrails",
    ROOT_DIR / "services" / "api",
    ROOT_DIR / "services" / "worker",
    ROOT_DIR / "services" / "retrieval",
    ROOT_DIR / "services" / "llm_stub",
]

for p in paths:
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)
