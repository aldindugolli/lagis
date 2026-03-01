# LAGIS - Analyst Agent
# Analyzes events for strategic implications with historical context

from typing import Dict, Any

from src.core.llm.engine import get_llm
from src.core.memory.memory import get_memory


ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "event_title": {"type": "string"},
        "immediate_impact": {"type": "string"},
        "power_balance_implications": {"type": "string"},
        "alliance_effects": {"type": "string"},
        "economic_consequences": {"type": "string"},
        "military_escalation_probability": {"type": "string", "enum": ["very_low", "low", "medium", "high", "very_high"]},
        "outlook_3_6_months": {"type": "string"},
        "confidence_score": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "required": ["immediate_impact", "power_balance_implications", "alliance_effects", "economic_consequences", "military_escalation_probability", "outlook_3_6_months", "confidence_score"]
}


SYSTEM_PROMPT = """You are a senior geopolitical analyst. Assess strategic implications."""


class AnalystAgent:
    """Analyzes events for strategic implications"""
    
    def __init__(self):
        self.llm = get_llm()
        self.memory = get_memory()
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis - takes state, returns updated state"""
        events = state.get("events", [])
        historical_context = state.get("historical_context", "")
        
        events_text = "\n".join([
            f"- {e.get('event_title', '')} ({e.get('countries_involved', [])}, severity: {e.get('severity_score', 0)})"
            for e in events
        ])
        
        prompt = f"""Analyze these geopolitical events and provide strategic assessment:

{events_text}

{historical_context}

Provide analysis for each event. Use the historical context to identify patterns and trends."""
        
        result = self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1024,
            system="You are a senior geopolitical analyst. Provide detailed strategic analysis of each event."
        )
        
        state["analysis_text"] = result
        state["analysis"] = [{"summary": result}]
        state["status"] = "analyzed"
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = AnalystAgent()
    return agent.run(state)
