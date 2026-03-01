# LAGIS - Executive Agent
# Generates final intelligence briefing with historical context

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from src.core.llm.engine import get_llm
from src.core.memory.memory import get_memory
from src.core.config import BRIEFS_DIR
from src.agents.knowledge.agent import get_knowledge_agent


BRIEF_SCHEMA = {
    "type": "object",
    "properties": {
        "top_events": {"type": "array", "items": {"type": "string"}},
        "escalation_risks": {"type": "array", "items": {"type": "string"}},
        "market_implications": {"type": "array", "items": {"type": "string"}},
        "strategic_opportunities": {"type": "array", "items": {"type": "string"}},
        "confidence_score": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "required": ["top_events", "escalation_risks", "market_implications", "strategic_opportunities", "confidence_score"]
}


SYSTEM_PROMPT = """You are a senior intelligence analyst creating an executive briefing."""


class ExecutiveAgent:
    """Generates executive intelligence briefing"""
    
    def __init__(self):
        self.llm = get_llm()
        self.memory = get_memory()
        self.output_dir = BRIEFS_DIR
        self.knowledge = get_knowledge_agent()
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute briefing - takes state, returns updated state"""
        events = state.get("events", [])
        risk_scores = state.get("risk_scores", {})
        kosovo_analysis = state.get("kosovo_analysis", {})
        
        events_text = "\n".join([
            f"- {e.get('event_title', '')} (severity: {e.get('severity_score', 0)})"
            for e in events[:10]
        ])
        
        risk_text = "\n".join([
            f"- {c}: Risk {r.get('overall_risk_score', 0)}/10"
            for c, r in list(risk_scores.items())[:10]
        ])
        
        # Get historical context from knowledge base
        historical_context = ""
        try:
            historical_context = self.knowledge.retrieve_context_for_brief("geopolitical", days=30)
        except Exception as e:
            logging.getLogger("LAGIS.Executive").warning(f"Failed to get historical context: {e}")
        
        # Build Kosovo section
        kosovo_section = ""
        if kosovo_analysis:
            risk_level = kosovo_analysis.get("risk_level", "UNKNOWN")
            kosovo_section = f"""

KOSOVO IMPACT:
- Risk Level: {risk_level}
- Summary: {kosovo_analysis.get('summary', 'No analysis')[:500]}
- Events: {len(kosovo_analysis.get('events', []))} Kosovo-related events detected
"""
        
        prompt = f"""Create an executive intelligence briefing:

TOP EVENTS:
{events_text}

HIGH-RISK COUNTRIES:
{risk_text}
{kosovo_section}

{historical_context}

Provide a detailed strategic briefing. Use the historical context to identify trends and patterns."""

        brief_text = self.llm.generate(
            prompt=prompt,
            temperature=0.4,
            max_tokens=512,
            system="You are a senior intelligence analyst. Create a professional executive briefing."
        )
        
        # Check for errors
        if brief_text.startswith("Error:"):
            print(f"Executive error: {brief_text}")
            brief_text = f"No brief generated due to error: {brief_text}"
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Add header and Kosovo section
        kosovo_header = ""
        if kosovo_analysis:
            risk_level = kosovo_analysis.get("risk_level", "UNKNOWN")
            kosovo_header = f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🇽🇰 KOSOVO STRATEGIC IMPACT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Risk Level: {risk_level}
{ kosovo_analysis.get('summary', 'No significant Kosovo developments.')[:800] }
"""
        
        full_brief = f"""{'='*60}
GLOBAL STRATEGIC BRIEFING
Date: {date_str}
{'='*60}

{brief_text}
{kosovo_header}

{'='*60}
"""
        
        output_path = self.output_dir / f"brief_{date_str}.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_brief)
        
        # Store in memory
        self.memory.store_brief({
            "date": date_str,
            "content": full_brief,
            "top_events": [e.get("event_title", "") for e in events[:5]],
            "escalation_risks": list(risk_scores.keys())[:5]
        })
        
        state["brief"] = full_brief
        state["status"] = "briefed"
        
        # Send to Telegram
        self._send_to_telegram(full_brief)
        
        return state
    
    def _send_to_telegram(self, brief: str):
        """Send brief to Telegram if configured"""
        try:
            from src.interfaces.telegram_sender import get_telegram
            telegram = get_telegram()
            if telegram.enabled:
                telegram.send_brief(brief)
        except Exception as e:
            logger = logging.getLogger("LAGIS.Executive")
            logger.warning(f"Telegram send failed: {e}")
    
    def _format_brief(self, brief: Dict[str, Any]) -> str:
        lines = [
            "=" * 60,
            "GLOBAL STRATEGIC BRIEFING",
            f"Date: {brief.get('date', '')}",
            f"Confidence: {brief.get('confidence_score', 0)*100:.0f}%",
            "=" * 60,
            "",
            "TOP GLOBAL EVENTS",
            "-" * 40,
        ]
        for event in brief.get("top_events", []):
            lines.append(f"  • {event}")
        
        lines.extend(["", "ESCALATION RISKS", "-" * 40])
        for risk in brief.get("escalation_risks", []):
            lines.append(f"  • {risk}")
        
        lines.extend(["", "MARKET IMPLICATIONS", "-" * 40])
        for imp in brief.get("market_implications", []):
            lines.append(f"  • {imp}")
        
        lines.extend(["", "STRATEGIC OPPORTUNITIES", "-" * 40])
        for opp in brief.get("strategic_opportunities", []):
            lines.append(f"  • {opp}")
        
        lines.extend(["", "=" * 60])
        return "\n".join(lines)


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = ExecutiveAgent()
    return agent.run(state)
