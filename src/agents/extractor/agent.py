# LAGIS - Extractor Agent
# Extracts structured events from articles

from typing import Dict, Any

from src.core.llm.engine import get_llm
from src.core.memory.memory import get_memory


EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "event_title": {"type": "string"},
        "countries_involved": {"type": "array", "items": {"type": "string"}},
        "event_type": {"type": "string", "enum": ["military", "diplomatic", "economic", "political", "environmental", "social", "technological"]},
        "strategic_category": {"type": "string", "enum": ["conflict", "cooperation", "trade", "sanctions", "alliance", "treaty", "protest", "election", "natural_disaster"]},
        "severity_score": {"type": "number", "minimum": 1, "maximum": 10},
        "summary": {"type": "string"}
    },
    "required": ["event_title", "countries_involved", "event_type", "strategic_category", "severity_score", "summary"]
}


SYSTEM_PROMPT = """You are a geopolitical event extraction expert. 
Analyze news and extract structured events with strategic significance."""


class ExtractorAgent:
    """Extracts structured events from articles"""
    
    def __init__(self):
        self.llm = get_llm()
        self.memory = get_memory()
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute extraction - takes state, returns updated state"""
        articles = state.get("articles", [])
        events = []
        
        # Process only top 5 articles for speed
        for article in articles[:5]:
            print(f"Extracting: {article.get('title', '')[:50]}...")
            prompt = f"""Extract structured event from:

Title: {article.get('title', '')}
Content: {article.get('content', '')[:1000]}"""

            result = self.llm.generate_structured(
                prompt=prompt,
                schema=EVENT_SCHEMA,
                system=SYSTEM_PROMPT,
                temperature=0.2
            )
            
            if "error" not in result:
                result["source_url"] = article.get("url", "")
                events.append(result)
                self.memory.store_event(result)
        
        state["events"] = events
        state["status"] = "extracted"
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = ExtractorAgent()
    return agent.run(state)
