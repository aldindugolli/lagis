# LAGIS - Strategic Synthesis Agent
# Single LLM call to synthesize all intelligence

import json
import logging
from typing import Dict, Any
from datetime import datetime

from src.core.llm.engine import get_llm
from src.orchestration.utils import add_llm_call

logger = logging.getLogger("LAGIS.Synthesis")


SYNTHESIS_PROMPT = """You are a senior intelligence analyst synthesizing a daily strategic briefing.

Generate a concise strategic synthesis from the following intelligence inputs.

EVENTS:
{events}

RISK ASSESSMENT:
{risks}

TREND ANALYSIS:
{trends}

MARKET IMPACT:
{market}

INTELLIGENCE:
{intelligence}

Provide your synthesis in this JSON format:
{{
    "executive_summary": "2-3 sentence overview of the global situation",
    "key_findings": [
        "Finding 1",
        "Finding 2",
        "Finding 3"
    ],
    "strategic_implications": [
        "Implication 1",
        "Implication 2"
    ],
    "conflict_probabilities": [
        {{"scenario": "Region/Issue", "probability": "high/medium/low", "reasoning": "brief"}}
    ],
    "stability_outlook": "Global stability assessment (stable/deteriorating/improving)",
    "watchlist": [
        "Country/Region 1",
        "Country/Region 2"
    ]
}}

Respond with ONLY valid JSON."""


class StrategicSynthesisAgent:
    """Synthesizes all intelligence into a single strategic assessment"""
    
    def __init__(self):
        self.llm = get_llm()
    
    def _format_events(self, events: list) -> str:
        """Format events for prompt"""
        if not events:
            return "No significant events."
        
        return "\n".join([
            f"- {e.get('event_title', '')[:70]} (severity: {e.get('severity_score', 0)})"
            for e in events[:8]
        ])
    
    def _format_risks(self, risk_scores: dict) -> str:
        """Format risk scores for prompt"""
        if not risk_scores:
            return "No risk assessments."
        
        lines = []
        for country, risk in list(risk_scores.items())[:10]:
            score = risk.get("overall_risk_score", 0)
            trend = risk.get("trend", "unknown")
            lines.append(f"- {country}: {score}/10 (trend: {trend})")
        
        return "\n".join(lines) if lines else "No high-risk countries."
    
    def _format_trends(self, trend_analysis: dict) -> str:
        """Format trends for prompt"""
        if not trend_analysis:
            return "No trend data."
        
        trends = trend_analysis.get("trends", [])
        if not trends:
            return "No significant trends."
        
        lines = []
        for t in trends[:5]:
            direction = t.get("direction", "unknown")
            topic = t.get("topic", "unknown")
            lines.append(f"- {topic}: {direction}")
        
        return "\n".join(lines)
    
    def _format_market(self, market_analysis: dict) -> str:
        """Format market analysis for prompt"""
        if not market_analysis:
            return "No market analysis."
        
        return market_analysis.get("summary", "No market summary.")[:300]
    
    def _format_intelligence(self, intelligence: dict) -> str:
        """Format intelligence for prompt"""
        if not intelligence:
            return "No intelligence data."
        
        parts = []
        
        if "topics_discovered" in intelligence:
            parts.append(f"Topics discovered: {intelligence['topics_discovered']}")
        
        if "world_stability_index" in intelligence:
            parts.append(f"Stability index: {intelligence['world_stability_index']}")
        
        risk_map = intelligence.get("risk_map", {})
        if risk_map:
            hotspots = risk_map.get("hotspots", [])
            if hotspots:
                parts.append(f"Hotspots: {', '.join([h.get('country', '') for h in hotspots[:5]])}")
        
        return "\n".join(parts) if parts else "No intelligence summary."
    
    def _format_signals(self, signal_alerts: list) -> str:
        """Format signal spike alerts"""
        if not signal_alerts:
            return "No early warning signals detected."
        
        lines = []
        for alert in signal_alerts[:5]:
            country = alert.get("country", "Unknown")
            category = alert.get("category", "general").replace("_", " ")
            ratio = alert.get("spike_ratio", 0)
            priority = alert.get("priority", 0)
            
            if priority >= 4:
                lines.append(f"[HIGH] {country}: {category} - {ratio}x normal")
            else:
                lines.append(f"{country}: {category} - {ratio}x normal")
        
        return "\n".join(lines) if lines else "No early warning signals."
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategic synthesis"""
        events = state.get("events", [])
        risk_scores = state.get("risk_scores", {})
        trend_analysis = state.get("trend_analysis", {})
        market_analysis = state.get("market_analysis", {})
        intelligence = state.get("intelligence", {})
        signal_alerts = state.get("signal_alerts", [])
        
        if not events:
            logger.warning("No data for synthesis")
            state["synthesis"] = {"executive_summary": "Insufficient data for synthesis."}
            return state
        
        events_text = self._format_events(events)
        risks_text = self._format_risks(risk_scores)
        trends_text = self._format_trends(trend_analysis)
        market_text = self._format_market(market_analysis)
        intel_text = self._format_intelligence(intelligence)
        signals_text = self._format_signals(signal_alerts)
        
        prompt = SYNTHESIS_PROMPT.format(
            events=events_text,
            risks=risks_text,
            trends=trends_text,
            market=market_text,
            intelligence=intel_text
        )
        
        try:
            result = self.llm.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1024,
                system="You synthesize intelligence into strategic assessments. Return valid JSON."
            )
            
            add_llm_call(state, tokens=800)
            
            synthesis = {}
            try:
                synthesis = json.loads(result)
            except json.JSONDecodeError:
                synthesis = {
                    "executive_summary": result[:300],
                    "error": "Parse error"
                }
            
            state["synthesis"] = synthesis
            state["status"] = "synthesized"
            
            logger.info("Strategic synthesis complete")
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            state["synthesis"] = {"executive_summary": f"Synthesis error: {str(e)}"}
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = StrategicSynthesisAgent()
    return agent.run(state)
