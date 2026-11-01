"""Tool: get_clause (Section 6.4).
Looks up a specific clause by stable clause_id.
"""

from typing import Optional
from bidscreen_contracts.tools import Passage
from packages.agents.tools.corpus_store import CORPUS_PASSAGES


def get_clause(clause_id: str) -> Optional[Passage]:
    """Retrieves a passage by clause_id, or None if not found."""
    return CORPUS_PASSAGES.get(clause_id)

