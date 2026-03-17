# LAGIS - Optimized Brief Generator
# Uses strategic synthesis for efficient brief generation

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from src.core.llm.engine import get_llm
from src.core.memory.memory import get_memory
from src.core.config import BRIEFS_DIR
from src.interfaces.telegram_sender import get_telegram

logger = logging.getLogger("LAGIS.Brief")


def clean_title(title: str) -> str:
    """Remove internal severity scores from titles"""
    title = re.sub(r"^\d+\s+", "", title)
    title = re.sub(r"^\[\d+\]\s*", "", title)
    title = re.sub(r"\s*\[\d+\]\s*$", "", title)
    return title.strip()


class OptimizedBriefAgent:
    """Generates briefs using strategic synthesis"""
    
    def __init__(self):
        self.llm = get_llm()
        self.memory = get_memory()
        self.output_dir = BRIEFS_DIR
        self.telegram = get_telegram()
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate brief from quick_analysis or synthesis"""
        synthesis = state.get("synthesis", {})
        events = state.get("deduplicated_events", []) or state.get("events", [])
        events = events[:5]
        analysis_text = state.get("analysis_text", "")
        risk_scores = synthesis.get("risk_scores", {}) or state.get("risk_scores", {})
        intelligence = state.get("intelligence", {})
        market_impact = state.get("market_impact", "")
        risk_regions = state.get("risk_regions", [])
        stability_index = state.get("stability_index", 7.0)
        signal_alerts = state.get("signal_alerts", [])
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        brief_parts = [
            "=" * 60,
            "GLOBAL STRATEGIC BRIEFING",
            f"Date: {date_str}",
            "=" * 60,
            ""
        ]
        
        if synthesis:
            exec_summary = synthesis.get("executive_summary", "No summary available.")
            brief_parts.append(f"EXECUTIVE SUMMARY\n{exec_summary}\n")
            
            key_findings = synthesis.get("key_findings", [])
            if key_findings:
                brief_parts.append("KEY FINDINGS")
                for finding in key_findings:
                    brief_parts.append(f"  - {finding}")
                brief_parts.append("")
            
            implications = synthesis.get("strategic_implications", [])
            if implications:
                brief_parts.append("STRATEGIC IMPLICATIONS")
                for imp in implications:
                    brief_parts.append(f"  - {imp}")
                brief_parts.append("")
            
            escalation = synthesis.get("escalation_outlook", {})
            if escalation:
                brief_parts.append("ESCALATION OUTLOOK")
                for key, value in escalation.items():
                    brief_parts.append(f"  - {key.replace('_', ' ').title()}: {value}")
                brief_parts.append("")
            
            market = synthesis.get("market_impact", "")
            if market:
                brief_parts.append(f"MARKET IMPACT\n{market}\n")
            
            next_moves = synthesis.get("likely_next_moves", [])
            if next_moves:
                brief_parts.extend([
                    "LIKELY NEXT MOVES",
                    "-" * 40
                ])
                for move in next_moves:
                    brief_parts.append(f"  - {move}")
                brief_parts.append("")
            
            conflicts = synthesis.get("conflict_probabilities", [])
            if conflicts:
                brief_parts.append("CONFLICT RISK ASSESSMENT")
                for c in conflicts[:5]:
                    scenario = c.get("scenario", "Unknown")
                    prob = c.get("probability", "unknown")
                    brief_parts.append(f"  - {scenario}: {prob.upper()}")
                brief_parts.append("")
            
        stability = synthesis.get("stability_outlook", "")
        if stability:
            brief_parts.append(f"GLOBAL STABILITY: {stability}\n")
        
        if stability_index:
            trend = "deteriorating" if stability_index < 6.5 else "stable" if stability_index > 7.5 else "stable"
            brief_parts.extend([
                "",
                f"GLOBAL STABILITY INDEX: {stability_index}/10",
                f"Trend: {trend}",
            ])
            for alert in signal_alerts[:5]:
                country = alert.get("country", "Unknown")
                category = alert.get("category", "general").replace("_", " ")
                ratio = alert.get("spike_ratio", 0)
                priority = alert.get("priority", 0)
                marker = "[CRITICAL]" if priority >= 4 else ""
                brief_parts.append(f"{marker} {country}: {category} - {ratio}x normal level")
            brief_parts.append("")
        
        brief_parts.extend([
            "-" * 60,
            "CRITICAL EVENTS",
            "-" * 60,
        ])
        
        for e in events:
            title = clean_title(e.get("title") or e.get("event_title", "Unknown")[:60])
            brief_parts.append(f"  - {title}")
        
        brief_parts.extend([
            "",
            "-" * 60,
            "HIGH-RISK COUNTRIES",
            "-" * 60,
        ])
        
        if risk_scores and isinstance(risk_scores, dict):
            sorted_risks = sorted(
                risk_scores.items(),
                key=lambda x: x[1] if isinstance(x[1], int) else x[1].get("overall_risk_score", 0),
                reverse=True
            )
            
            for country, score in sorted_risks[:5]:
                if isinstance(score, int):
                    level = "HIGH" if score >= 7 else "MEDIUM" if score >= 5 else "LOW"
                    brief_parts.append(f"{country}: {score}/10 {level}")
                else:
                    s = score.get("overall_risk_score", 5)
                    trend = score.get("trend", "stable")
                    brief_parts.append(f"{country}: {s}/10 ({trend})")
        else:
            countries_shown = set()
            for e in events[:5]:
                countries = e.get("countries", e.get("countries_involved", []))
                if countries:
                    for c in countries[:3]:
                        if c not in countries_shown:
                            countries_shown.add(c)
                            brief_parts.append(f"{c}: 5/10 (monitor)")
        
        if intelligence:
            stability_index = intelligence.get("world_stability_index", 0)
            brief_parts.extend([
                "",
                f"WORLD STABILITY INDEX: {stability_index}/10",
            ])
        
        brief_parts.extend([
            "",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
        ])
        
        brief_text = "\n".join(brief_parts)
        
        output_path = self.output_dir / f"brief_{date_str}.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(brief_text)
        
        self.memory.store_brief({
            "date": date_str,
            "content": brief_text,
            "top_events": [e.get("event_title", "") for e in events[:5]],
            "escalation_risks": list(risk_scores.keys())[:5]
        })
        
        if self.telegram.enabled:
            try:
                self.telegram.send_brief(brief_text)
                logger.info("Brief sent to Telegram")
            except Exception as e:
                logger.error(f"Telegram send failed: {e}")
        
        state["brief"] = brief_text
        state["status"] = "briefed"
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = OptimizedBriefAgent()
    return agent.run(state)
