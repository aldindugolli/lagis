# LAGIS - Debate Agent
# Optimized multi-perspective analysis with single LLM call

import json
import logging
from typing import Dict, Any, List

from src.core.llm.engine import get_llm
from src.core.memory.memory import get_memory
from src.agents.knowledge.agent import get_knowledge_agent
from src.orchestration.utils import skip_stage, add_llm_call

logger = logging.getLogger("LAGIS.Debate")


MULTI_PERSPECTIVE_PROMPT = """Analyze these geopolitical events from FOUR different perspectives in a SINGLE response.

EVENTS:
{events}

HISTORICAL CONTEXT:
{context}

Provide your analysis in this JSON format:
{{
    "hawk": {{
        "analysis": "Military/security assessment - escalation risks, worst-case scenarios",
        "key_concerns": ["concern 1", "concern 2", "concern 3"],
        "confidence": 0.0-1.0
    }},
    "dove": {{
        "analysis": "Diplomatic/economic assessment - cooperation opportunities, de-escalation",
        "key_concerns": ["concern 1", "concern 2", "concern 3"],
        "confidence": 0.0-1.0
    }},
    "economic": {{
        "analysis": "Market/trade assessment - economic impacts, supply chains",
        "key_concerns": ["concern 1", "concern 2", "concern 3"],
        "confidence": 0.0-1.0
    }},
    "regional": {{
        "analysis": "Regional dynamics assessment - local actors, historical context",
        "key_concerns": ["concern 1", "concern 2", "concern 3"],
        "confidence": 0.0-1.0
    }},
    "consensus": {{
        "summary": "2-3 sentence agreement across perspectives",
        "disagreements": "Key areas where perspectives differ",
        "confidence_level": "high/medium/low",
        "recommended_action": "What should decision-makers do?"
    }}
}}

Respond with ONLY valid JSON."""


class DebateAgent:
    """Optimized debate with single LLM call"""
    
    def __init__(self):
        self.llm = get_llm()
        self.memory = get_memory()
        self.knowledge = get_knowledge_agent()
    
    def _get_context(self, topic: str) -> str:
        """Get historical context for topic"""
        try:
            articles = self.knowledge.get_historical_context(topic, days=30)
            if not articles:
                return "No recent historical context available."
            
            context = "Recent intelligence:\n"
            for a in articles[:3]:
                context += f"- {a.get('title', 'Unknown')}: {a.get('content', '')[:150]}...\n"
            return context
        except Exception:
            return "Historical context unavailable."
    
    def _should_run_debate(self, events: List[Dict]) -> bool:
        """Only run debate for significant events"""
        high_severity = len([e for e in events if e.get('severity_score', 0) >= 6])
        return high_severity >= 2 or (len(events) >= 5 and high_severity >= 1)
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimized debate with single LLM call"""
        events = state.get("events", [])
        
        if not events:
            logger.info("Skipping debate: No events")
            skip_stage(state, "no_events")
            state["debate_result"] = {"debate_complete": False, "skipped": True}
            return state
        
        if not self._should_run_debate(events):
            high_sev = len([e for e in events if e.get('severity_score', 0) >= 6])
            logger.info(f"Skipping debate: Only {high_sev} high-severity events")
            skip_stage(state, f"low_activity ({high_sev} severe)")
            state["debate_result"] = {"debate_complete": False, "skipped": True, "reason": "low_activity"}
            return state
        
        events_text = "\n".join([
            f"- {e.get('event_title', '')} (severity: {e.get('severity_score', 0)})"
            for e in events[:8]
        ])
        
        topic = events[0].get('event_title', 'geopolitical')[:30]
        context = self._get_context(topic)
        
        prompt = MULTI_PERSPECTIVE_PROMPT.format(events=events_text, context=context)
        
        try:
            result = self.llm.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1024,
                system="You are a multi-perspective intelligence analyst. Return valid JSON."
            )
            
            add_llm_call(state, tokens=800)
            
            try:
                debate_result = json.loads(result)
            except json.JSONDecodeError:
                debate_result = {
                    "error": "Parse failed",
                    "raw_response": result[:500],
                    "consensus": {"summary": "Analysis unavailable due to parse error"}
                }
            
            state["debate_result"] = {
                "synthesis": debate_result.get("consensus", {}),
                "perspectives": {
                    "hawk": debate_result.get("hawk", {}),
                    "dove": debate_result.get("dove", {}),
                    "economic": debate_result.get("economic", {}),
                    "regional": debate_result.get("regional", {})
                },
                "debate_complete": True
            }
            
            logger.info("Debate complete - single LLM call")
            
        except Exception as e:
            logger.error(f"Debate failed: {e}")
            skip_stage(state, f"error: {str(e)[:30]}")
            state["debate_result"] = {"debate_complete": False, "error": str(e)}
        
        state["status"] = "debated"
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = DebateAgent()
    return agent.run(state)
