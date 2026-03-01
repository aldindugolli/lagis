# LAGIS - Context Agent
# Retrieves historical context from knowledge base before analysis

import logging
from typing import Dict, Any, List

from src.agents.knowledge.agent import get_knowledge_agent
from src.core.memory.memory import get_memory

logger = logging.getLogger("LAGIS.Context")


class ContextAgent:
    """Retrieves historical context for improved analysis"""
    
    def __init__(self):
        self.knowledge = get_knowledge_agent()
        self.memory = get_memory()
    
    def _extract_topics_from_events(self, events: List[Dict]) -> List[str]:
        """Extract key topics from events for context search"""
        topics = set()
        
        keywords = [
            "war", "conflict", "military", "nato", "russia", "ukraine",
            "iran", "nuclear", "china", "taiwan", "korea", "terrorist",
            "sanctions", "trade", "economy", "election", "protest",
            "diplomacy", "treaty", "security", "attack", "invasion"
        ]
        
        for event in events:
            title = event.get("event_title", "").lower()
            summary = event.get("summary", "").lower()
            
            for kw in keywords:
                if kw in title or kw in summary:
                    topics.add(kw)
        
        return list(topics)[:5]
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve historical context before analysis"""
        events = state.get("events", [])
        
        if not events:
            logger.warning("No events to retrieve context for")
            state["historical_context"] = "No events available for context retrieval."
            return state
        
        topics = self._extract_topics_from_events(events)
        
        context_parts = ["HISTORICAL CONTEXT FROM PAST 30 DAYS:"]
        
        for topic in topics[:3]:
            try:
                similar = self.knowledge.get_historical_context(topic, days=30)
                if similar:
                    context_parts.append(f"\n--- {topic.upper()} Related Events ---")
                    for item in similar[:3]:
                        date = item.get('archived_date', 'Unknown')
                        title = item.get('title', 'Untitled')
                        content = item.get('content', '')[:200]
                        context_parts.append(f"[{date}] {title}: {content}...")
            except Exception as e:
                logger.warning(f"Failed to get context for {topic}: {e}")
        
        if len(context_parts) == 1:
            context_parts.append("No significant historical patterns detected.")
        
        historical_context = "\n".join(context_parts)
        state["historical_context"] = historical_context
        
        logger.info(f"Retrieved context for topics: {topics}")
        state["status"] = "context_retrieved"
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = ContextAgent()
    return agent.run(state)
