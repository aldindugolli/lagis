# LAGIS - Unified State Object

from typing import Dict, Any, List, Optional
from datetime import datetime


class IntelligenceState:
    """Single source of truth for all agent state"""
    
    def __init__(self):
        self.data: Dict[str, Any] = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "articles": [],
            "events": [],
            "analysis": [],
            "risk_scores": {},
            "brief": "",
            "errors": [],
            "status": "initialized"
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        self.data.update(updates)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.data.copy()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntelligenceState":
        state = cls()
        state.data.update(data)
        return state


def create_initial_state() -> Dict[str, Any]:
    """Create initial state for pipeline"""
    return IntelligenceState().to_dict()
