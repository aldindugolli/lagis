# LAGIS - Kosovo Impact Intelligence Agent
# Evaluates geopolitical events impact on Kosovo and Balkan region

import logging
from typing import Dict, Any

from src.core.llm.engine import get_llm
from src.core.memory.memory import get_memory

logger = logging.getLogger("LAGIS.Kosovo")


KOSOVO_KEYWORDS = [
    "kosovo", "serbia", "belgrade", "prishtina", "balkan", "albania",
    "north macedonia", "montenegro", "bosnia", "vucic", "kurti",
    "eu mediation", "eulex", "nato kosovo", "kfor"
]


class KosovoImpactAgent:
    """Analyzes impact of events on Kosovo and Balkan region"""
    
    def __init__(self):
        self.llm = get_llm()
        self.memory = get_memory()
    
    def _is_relevant(self, event: Dict[str, Any]) -> bool:
        """Check if event is relevant to Kosovo/Balkans"""
        text = " ".join([
            event.get("event_title", ""),
            event.get("summary", ""),
            " ".join(event.get("countries_involved", []))
        ]).lower()
        
        return any(kw in text for kw in KOSOVO_KEYWORDS)
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Kosovo analysis - takes state, returns updated state"""
        events = state.get("events", [])
        
        # Filter Kosovo-relevant events
        kosovo_events = [e for e in events if self._is_relevant(e)]
        
        if not kosovo_events:
            logger.info("No Kosovo-relevant events found")
            state["kosovo_analysis"] = {
                "risk_level": "LOW",
                "summary": "No significant Kosovo-related developments detected.",
                "events": []
            }
            return state
        
        events_text = "\n".join([
            f"- {e.get('event_title', '')} ({e.get('countries_involved', [])})"
            for e in kosovo_events[:5]
        ])
        
        prompt = f"""Analyze the impact on Kosovo and the Balkan region:

{events_text}

Assess:
1. Security implications for Kosovo
2. Diplomatic consequences (EU, NATO, Serbia relations)
3. Economic impact
4. Risk level (LOW/MODERATE/HIGH/CRITICAL)
5. Short-term outlook

Provide analysis:"""

        logger.info(f"Analyzing {len(kosovo_events)} Kosovo-relevant events...")
        
        result = self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1024,
            system="You are a Balkans geopolitical analyst specializing in Kosovo affairs."
        )
        
        # Determine risk level based on severity
        max_severity = max([e.get("severity_score", 0) for e in kosovo_events])
        if max_severity >= 7:
            risk_level = "CRITICAL"
        elif max_severity >= 5:
            risk_level = "HIGH"
        elif max_severity >= 3:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"
        
        kosovo_analysis = {
            "risk_level": risk_level,
            "summary": result,
            "events": [e.get("event_title", "") for e in kosovo_events],
            "event_count": len(kosovo_events)
        }
        
        state["kosovo_analysis"] = kosovo_analysis
        state["status"] = "kosovo_analyzed"
        
        logger.info(f"Kosovo risk level: {risk_level}")
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = KosovoImpactAgent()
    return agent.run(state)
