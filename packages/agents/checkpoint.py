"""Checkpoint mechanism for saving and restoring agent state."""

import copy
import logging
from typing import Dict, Any, Optional
from packages.agents.state import AgentState

logger = logging.getLogger(__name__)


class MemoryCheckpointer:
    """In-memory checkpointer for saving and recovering agent state between nodes."""

    def __init__(self):
        self._checkpoints: Dict[str, Dict[str, Any]] = {}

    def save(self, run_id: str, checkpoint_name: str, state: AgentState):
        key = f"{run_id}:{checkpoint_name}"
        self._checkpoints[key] = copy.deepcopy(dict(state))
        logger.debug("Checkpoint saved: %s", key)

    def load(self, run_id: str, checkpoint_name: str) -> Optional[AgentState]:
        key = f"{run_id}:{checkpoint_name}"
        state = self._checkpoints.get(key)
        if state:
            logger.info("Checkpoint loaded: %s", key)
            return copy.deepcopy(state)
        logger.warning("Checkpoint not found: %s", key)
        return None

    def clear(self, run_id: str):
        keys_to_del = [k for k in self._checkpoints if k.startswith(f"{run_id}:")]
        for k in keys_to_del:
            del self._checkpoints[k]

