# LAGIS - Analyst Agent
# Analyzes events for strategic implications with deep historical and political context

from typing import Dict, Any

from src.core.llm.engine import get_llm
from src.core.memory.memory import get_memory
from src.orchestration.utils import add_llm_call


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


ANALYST_PROMPT = """You are a senior geopolitical analyst at a strategic intelligence organization.

Your analysis must go beyond surface-level summaries. For each event, provide:

1. STRATEGIC IMPLICATIONS: How does this affect the global balance of power?
2. ALLIANCE DYNAMICS: Which alliances are strengthened or weakened?
3. REGIONAL STABILITY: What is the impact on regional security?
4. LONG-TERM TRENDS: Does this represent a shift in strategic direction?
5. ECONOMIC CONSEQUENCES: What are the financial/market implications?

Consider historical patterns and past events when forming your assessment.

Provide detailed, actionable intelligence."""


class AnalystAgent:
    """Analyzes events for strategic implications with deep context"""
    
    def __init__(self):
        self.llm = get_llm()
        self.memory = get_memory()
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis with strategic context"""
        events = state.get("events", [])
        strategic_context = state.get("strategic_context", "")
        actors = state.get("actors", {})
        
        if not events:
            state["analysis_text"] = "No events to analyze."
            state["analysis"] = []
            state["status"] = "analyzed"
            return state
        
        events_text = "\n".join([
            f"- {e.get('event_title', '')} ({e.get('countries_involved', [])}, severity: {e.get('severity_score', 0)})"
            for e in events[:10]
        ])
        
        countries = actors.get("countries", [])
        countries_text = f"Involved countries: {', '.join(countries)}" if countries else ""
        
        prompt = f"""Analyze these geopolitical events with strategic context:

{countries_text}

EVENTS:
{events_text}

{strategic_context}

{ANALYST_PROMPT}"""

        result = self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1024,
            system=ANALYST_PROMPT
        )
        
        add_llm_call(state, tokens=int(len(result.split()) * 1.3))
        
        state["analysis_text"] = result
        state["analysis"] = [{"summary": result}]
        state["status"] = "analyzed"
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = AnalystAgent()
    return agent.run(state)
