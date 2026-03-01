# LAGIS - Market Correlation Agent
# Analyzes geopolitical events for market impact

import logging
from typing import Dict, Any

from src.core.llm.engine import get_llm
from src.core.memory.memory import get_memory

logger = logging.getLogger("LAGIS.Market")


SECTORS = [
    "Energy", "Defense", "Financials", "Technology",
    "Healthcare", "Transportation", "Commodities", "Currencies"
]


class MarketAgent:
    """Analyzes market impact of geopolitical events"""
    
    def __init__(self):
        self.llm = get_llm()
        self.memory = get_memory()
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute market analysis - takes state, returns updated state"""
        events = state.get("events", [])
        
        # Focus on high-severity events
        significant_events = [e for e in events if e.get("severity_score", 0) >= 4]
        
        if not significant_events:
            logger.info("No significant events for market analysis")
            state["market_impacts"] = []
            return state
        
        events_text = "\n".join([
            f"- {e.get('event_title', '')} (severity: {e.get('severity_score', 0)})"
            for e in significant_events[:5]
        ])
        
        prompt = f"""Analyze the market impact of these geopolitical events:

{events_text}

For each relevant sector ({', '.join(SECTORS)}), assess:
1. Direction (positive/negative/neutral)
2. Impact level (0-10)
3. Rationale

Provide analysis in plain text:"""

        logger.info("Analyzing market impacts...")
        
        result = self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1024,
            system="You are a financial markets analyst specializing in geopolitical risk."
        )
        
        # Store market analysis
        self.memory.store_brief({
            "date": state.get("date", ""),
            "content": f"Market Analysis: {result}",
            "top_events": [],
            "market_impacts": result[:500]
        })
        
        state["market_impacts"] = result
        state["status"] = "market_analyzed"
        
        logger.info("Market analysis complete")
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = MarketAgent()
    return agent.run(state)
