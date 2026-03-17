# LAGIS - Pipeline Utilities
# Shared utilities for agent pipeline

from typing import Dict, Any


def skip_stage(state: Dict[str, Any], reason: str) -> None:
    """Mark current stage as skipped"""
    state["_stage_skipped"] = reason


def add_llm_call(state: Dict[str, Any], tokens: int = 0) -> None:
    """Track LLM call in efficiency metrics"""
    if "_efficiency" not in state:
        state["_efficiency"] = {"llm_calls": 0, "tokens": 0}
    state["_efficiency"]["llm_calls"] = state["_efficiency"].get("llm_calls", 0) + 1
    state["_efficiency"]["tokens"] = state["_efficiency"].get("tokens", 0) + tokens
