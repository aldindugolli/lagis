# LAGIS - Query Agent
# Handles user questions via Telegram

import logging
from typing import Dict, Any

from src.core.llm.engine import get_llm
from src.core.memory.memory import get_memory

logger = logging.getLogger("LAGIS.Query")


class QueryAgent:
    """Processes user queries using memory and LLM"""
    
    def __init__(self):
        self.llm = get_llm()
        self.memory = get_memory()
    
    def run(self, query: str) -> str:
        """Process a user query and return answer"""
        
        # Get relevant context from memory
        brief = self.memory.get_latest_brief()
        events = self.memory.get_recent_events(10)
        
        context_parts = []
        
        if brief:
            context_parts.append(f"LATEST BRIEF:\n{brief.get('content', '')[:1000]}")
        
        if events:
            events_text = "\n".join([
                f"- {e.get('event_title', '')} (severity: {e.get('severity_score', 0)})"
                for e in events[:5]
            ])
            context_parts.append(f"RECENT EVENTS:\n{events_text}")
        
        context = "\n\n".join(context_parts) if context_parts else "No historical data available."
        
        prompt = f"""Based on the intelligence data below, answer the user's question.

INTELLIGENCE DATA:
{context}

USER QUESTION: {query}

Provide a detailed, accurate answer based on the intelligence data. If insufficient data exists, say so."""

        logger.info(f"Processing query: {query[:50]}...")
        
        answer = self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1024,
            system="You are a geopolitical intelligence analyst. Answer based on the provided data."
        )
        
        return answer


_query_agent = None


def get_query_agent() -> QueryAgent:
    global _query_agent
    if _query_agent is None:
        _query_agent = QueryAgent()
    return _query_agent


def process_query(query: str) -> str:
    """Process a user query"""
    agent = get_query_agent()
    return agent.run(query)
