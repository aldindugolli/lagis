# LAGIS - Risk Agent
# Assesses country-level risk scores

from typing import Dict, Any

from src.core.llm.engine import get_llm
from src.core.memory.memory import get_memory


RISK_SCHEMA = {
    "type": "object",
    "properties": {
        "country": {"type": "string"},
        "political_stability": {"type": "number", "minimum": 0, "maximum": 10},
        "escalation_risk": {"type": "number", "minimum": 0, "maximum": 10},
        "economic_stress": {"type": "number", "minimum": 0, "maximum": 10},
        "alliance_shift_probability": {"type": "number", "minimum": 0, "maximum": 10},
        "overall_risk_score": {"type": "number", "minimum": 0, "maximum": 10},
        "trend": {"type": "string", "enum": ["improving", "stable", "deteriorating"]},
        "key_factors": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["country", "political_stability", "escalation_risk", "economic_stress", "alliance_shift_probability", "overall_risk_score", "trend", "key_factors"]
}


SYSTEM_PROMPT = """You are a geopolitical risk analyst. Assess country-level risk."""


class RiskAgent:
    """Assesses country-level risk scores"""
    
    def __init__(self):
        self.llm = get_llm()
        self.memory = get_memory()
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute risk assessment - takes state, returns updated state"""
        events = state.get("events", [])
        risk_scores = {}
        
        # Build combined events text
        events_text = "\n".join([
            f"- {e.get('event_title', '')} ({e.get('countries_involved', [])}, severity: {e.get('severity_score', 0)})"
            for e in events
        ])
        
        prompt = f"""Assess geopolitical risk for countries mentioned in these events:

{events_text}

Provide risk assessment for key countries."""

        result = self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1024,
            system="You are a geopolitical risk analyst. Provide risk scores (0-10) for countries mentioned."
        )
        
        # Store simple risk data
        countries = list(set([c for e in events for c in e.get('countries_involved', [])]))
        for country in countries[:10]:
            risk_scores[country] = {"overall_risk_score": 5, "trend": "stable", "summary": result[:200]}
            self.memory.store_risk_score(country, risk_scores[country])
        
        state["risk_scores"] = risk_scores
        state["risk_text"] = result
        state["status"] = "risk_assessed"
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = RiskAgent()
    return agent.run(state)
