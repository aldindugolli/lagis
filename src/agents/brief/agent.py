# LAGIS - Optimized Brief Generator
# With intelligence enrichment and output guardrails

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from src.core.memory.memory import get_memory
from src.core.config import BRIEFS_DIR
from src.interfaces.telegram_sender import get_telegram, sanitize_for_telegram

logger = logging.getLogger("LAGIS.Brief")

OUTPUT_LIMITS = {
    "exec_summary": 200,
    "implications": 3,
    "events": 4,
    "risk_countries": 5,
    "next_moves": 2,
    "total_chars": 3500
}

EVENT_TAGS = {
    "oil": "Energy Security Risk",
    "energy": "Energy Security Risk", 
    "pipeline": "Energy Security Risk",
    "missile": "Military Escalation",
    "airstrike": "Military Escalation",
    "attack": "Military Escalation",
    "strike": "Military Escalation",
    "bombing": "Military Escalation",
    "nuclear": "Strategic Nuclear Risk",
    "war": "Major Conflict",
    "invasion": "Major Conflict",
    "sanction": "Economic Pressure",
    "protest": "Political Instability",
    "troops": "Military Mobilization",
    "soldiers": "Military Mobilization"
}

GREAT_POWER = ["US", "NATO", "Russia", "China", "United States"]


def clean_title(title: str) -> str:
    """Remove internal severity scores from titles"""
    title = re.sub(r"^\d+\s+", "", title)
    title = re.sub(r"^\[\d+\]\s*", "", title)
    title = re.sub(r"\s*\[\d+\]\s*$", "", title)
    return title.strip()


def truncate(text: str, limit: int) -> str:
    """Truncate text at word boundary, never mid-word"""
    if len(text) <= limit:
        return text
    truncated = text[:limit]
    last_space = truncated.rfind(' ')
    if last_space > limit * 0.7:
        return truncated[:last_space] + "..."
    return truncated + "..."


def deduplicate_lines(lines: List[str]) -> List[str]:
    """Remove duplicate lines (case-insensitive, stripped)"""
    seen = set()
    result = []
    for line in lines:
        key = line.lower().strip()
        if key and key not in seen:
            seen.add(key)
            result.append(line)
    return result


def enrich_event(event: Dict) -> tuple:
    """Extract intelligence context from event"""
    title = event.get("title", event.get("event_title", ""))
    title = clean_title(title)
    
    title_lower = title.lower()
    
    tags = []
    for keyword, tag in EVENT_TAGS.items():
        if keyword in title_lower:
            if tag not in tags:
                tags.append(tag)
    
    has_great_power = any(gp.lower() in title_lower for gp in GREAT_POWER)
    if has_great_power and "Great Power Involvement" not in tags:
        tags.append("Great Power Involvement")
    
    if not tags:
        tags = ["General Intelligence"]
    
    return title, tags[0] if tags else "General Intelligence"


def enforce_output_limits(brief_parts: List[str]) -> List[str]:
    """Enforce hard limits on output sections"""
    result = []
    current_section = None
    section_count = 0
    
    for part in brief_parts:
        stripped = part.strip()
        
        if not stripped:
            result.append(part)
            continue
        
        if stripped.startswith("EXECUTIVE SUMMARY"):
            current_section = "exec"
            section_count = 0
            result.append(part)
            continue
        elif stripped.startswith("STRATEGIC IMPLICATIONS"):
            current_section = "impl"
            section_count = 0
            result.append(part)
            continue
        elif stripped.startswith("CRITICAL EVENTS"):
            current_section = "events"
            section_count = 0
            result.append(part)
            continue
        elif stripped.startswith("HIGH-RISK"):
            current_section = "risk"
            section_count = 0
            result.append(part)
            continue
        elif stripped.startswith("LIKELY NEXT"):
            current_section = "moves"
            section_count = 0
            result.append(part)
            continue
        elif stripped.startswith("=") or stripped.startswith("-"):
            current_section = None
            section_count = 0
            result.append(part)
            continue
        
        if current_section == "exec":
            if len(stripped) > OUTPUT_LIMITS["exec_summary"]:
                result.append(truncate(stripped, OUTPUT_LIMITS["exec_summary"]))
            else:
                result.append(part)
        elif current_section == "impl" and stripped.startswith("  -"):
            section_count += 1
            if section_count <= OUTPUT_LIMITS["implications"]:
                result.append(part)
        elif current_section == "events" and stripped.startswith("  -"):
            section_count += 1
            if section_count <= OUTPUT_LIMITS["events"]:
                result.append(part)
        elif current_section == "risk" and stripped.startswith("  "):
            section_count += 1
            if section_count <= OUTPUT_LIMITS["risk_countries"]:
                result.append(part)
        elif current_section == "moves" and stripped.startswith("  -"):
            section_count += 1
            if section_count <= OUTPUT_LIMITS["next_moves"]:
                result.append(part)
        else:
            result.append(part)
    
    return result


def format_intelligence_event(event: Dict) -> str:
    """Format event as intelligence entry with context"""
    title, tag = enrich_event(event)
    
    title = truncate(title, 70)
    
    implication_map = {
        "Energy Security Risk": "Threatens supply chains; market volatility expected",
        "Military Escalation": "Raises confrontation risk; regional stability at stake",
        "Strategic Nuclear Risk": "Extremely high stakes; international concern",
        "Major Conflict": "Significant loss potential; humanitarian impact",
        "Economic Pressure": "May affect trade; sanctions escalation",
        "Political Instability": "Regime vulnerability; internal conflict risk",
        "Military Mobilization": "Prepares for potential escalation",
        "Great Power Involvement": "Widens scope; increases complexity",
        "General Intelligence": "Monitor for developments"
    }
    
    implication = implication_map.get(tag, "Monitor for developments")
    
    return f"  - {title}\n    Signals: {implication}"


class OptimizedBriefAgent:
    """Generates intelligence briefs with quality safeguards"""
    
    def __init__(self):
        self.memory = get_memory()
        self.output_dir = BRIEFS_DIR
        self.telegram = get_telegram()
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate brief with intelligence enrichment"""
        synthesis = state.get("synthesis", {})
        events = state.get("deduplicated_events", []) or state.get("events", [])
        events = events[:5]
        risk_scores = synthesis.get("risk_scores", {}) or state.get("risk_scores", {})
        stability_index = state.get("stability_index", 7.0)
        signal_alerts = state.get("signal_alerts", [])
        early_signals = state.get("early_signals", [])
        scenarios = state.get("scenarios", [])
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        brief_parts = [
            "=" * 60,
            "GLOBAL STRATEGIC BRIEFING",
            f"Date: {date_str}",
            "=" * 60,
            "",
            "EXECUTIVE SUMMARY",
            ""
        ]
        
        exec_summary = synthesis.get("executive_summary", "Analysis in progress.")
        brief_parts.append(truncate(exec_summary, OUTPUT_LIMITS["exec_summary"]))
        brief_parts.append("")
        
        brief_parts.extend(["STRATEGIC IMPLICATIONS", "-" * 40])
        implications = synthesis.get("strategic_implications", [])
        if implications:
            for imp in deduplicate_lines(implications)[:OUTPUT_LIMITS["implications"]]:
                brief_parts.append(f"  - {truncate(imp, 100)}")
        else:
            brief_parts.append("  - Monitor regional developments")
            brief_parts.append("  - Assess economic impact")
        
        relationship_insights = synthesis.get("relationship_insights", [])
        if relationship_insights:
            brief_parts.append("")
            brief_parts.append("RELATIONSHIP INSIGHTS:")
            for insight in relationship_insights[:2]:
                brief_parts.append(f"  - {truncate(insight, 120)}")
        
        brief_parts.append("")
        
        brief_parts.extend(["ESCALATION OUTLOOK", "-" * 40])
        escalation = synthesis.get("escalation_outlook", {})
        if escalation:
            for key, value in escalation.items():
                if value in ["HIGH", "MODERATE", "LOW"]:
                    brief_parts.append(f"  - {key.replace('_', ' ').title()}: {value}")
        else:
            brief_parts.append("  - Overall: MODERATE")
        brief_parts.append("")
        
        if early_signals:
            brief_parts.extend(["EARLY SIGNALS (EMERGING RISKS)", "-" * 40])
            for sig in early_signals[:3]:
                narrative = sig.get("narrative", "Signal detected")
                confidence = sig.get("confidence", "low")
                prediction = sig.get("prediction", "")
                
                brief_parts.append(f"  - {narrative}")
                if prediction:
                    brief_parts.append(f"    -> {prediction}")
            brief_parts.append("")
        
        black_swan_alerts = state.get("black_swan_alerts", [])
        if black_swan_alerts:
            brief_parts.extend(["⚠️ BLACK SWAN ALERTS", "-" * 40])
            for alert in black_swan_alerts:
                brief_parts.append(f"  [{alert.get('risk', 'MEDIUM')}] {alert.get('type', 'Anomaly')}")
                brief_parts.append(f"    {alert.get('description', 'Rare event detected')}")
                brief_parts.append(f"    → {alert.get('implication', 'Monitor for escalation')}")
            brief_parts.append("")
        
        if scenarios:
            brief_parts.extend(["SCENARIO OUTLOOK", "-" * 40])
            for s in scenarios[:3]:
                brief_parts.append(f"  - {s.get('title', 'Scenario')}")
                brief_parts.append(f"    Probability: {s.get('probability', 'LOW')} | Timeframe: {s.get('timeframe', '1-2 weeks')}")
                impact = s.get("impact", [])
                if impact:
                    brief_parts.append(f"    Impact: {impact[0]}")
            brief_parts.append("")
        
        brief_parts.extend(["CRITICAL EVENTS", "-" * 40])
        for event in events[:OUTPUT_LIMITS["events"]]:
            brief_parts.append(format_intelligence_event(event))
        brief_parts.append("")
        
        brief_parts.extend(["HIGH-RISK COUNTRIES", "-" * 40])
        if risk_scores and isinstance(risk_scores, dict):
            sorted_risks = sorted(
                [(k, v) for k, v in risk_scores.items() if isinstance(v, int)],
                key=lambda x: x[1],
                reverse=True
            )
            for country, score in sorted_risks[:OUTPUT_LIMITS["risk_countries"]]:
                level = "HIGH" if score >= 7 else "MEDIUM" if score >= 5 else "LOW"
                brief_parts.append(f"  {country}: {score}/10 {level}")
        else:
            brief_parts.append("  - Situation stable")
        brief_parts.append("")
        
        brief_parts.extend(["LIKELY NEXT MOVES", "-" * 40])
        next_moves = synthesis.get("likely_next_moves", [])
        if next_moves:
            for move in deduplicate_lines(next_moves)[:OUTPUT_LIMITS["next_moves"]]:
                brief_parts.append(f"  - {truncate(move, 100)}")
        else:
            brief_parts.append("  - Monitor for developments")
        brief_parts.append("")
        
        learning_metrics = state.get("learning_metrics", {})
        if learning_metrics:
            brief_parts.extend(["INTELLIGENCE CONFIDENCE", "-" * 40])
            accuracy = learning_metrics.get("accuracy_rate", 0.5)
            total = learning_metrics.get("total_predictions", 0)
            confidence = learning_metrics.get("confidence", "Developing")
            pending = learning_metrics.get("pending", 0)
            brief_parts.append(f"  - Prediction Accuracy: {accuracy:.0%}")
            brief_parts.append(f"  - System Confidence: {confidence}")
            if total > 0:
                brief_parts.append(f"  - Track Record: {total} predictions ({pending} pending)")
            brief_parts.append("")
        
        strategic_recs = state.get("strategic_recommendations", {})
        recommendations = strategic_recs.get("recommendations", [])
        if recommendations:
            brief_parts.extend(["🎯 STRATEGIC RECOMMENDATIONS", "-" * 40])
            for rec in recommendations[:3]:
                brief_parts.append(f"  - {rec.get('action', 'Continue monitoring')}")
            brief_parts.append("")
        
        brief_parts.append(f"GLOBAL STABILITY INDEX: {stability_index}/10")
        if stability_index < 6.5:
            brief_parts.append("Trend: Deteriorating")
        elif stability_index > 7.5:
            brief_parts.append("Trend: Improving")
        else:
            brief_parts.append("Trend: Stable")
        brief_parts.append("")
        
        brief_parts.extend([
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60
        ])
        
        brief_parts = enforce_output_limits(brief_parts)
        
        brief_text = "\n".join(brief_parts)
        
        if len(brief_text) > OUTPUT_LIMITS["total_chars"]:
            brief_text = brief_text[:OUTPUT_LIMITS["total_chars"]]
        
        if "Generated:" not in brief_text:
            brief_text += f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        output_file = self.output_dir / f"brief_{datetime.now().strftime('%Y-%m-%d')}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(brief_text)
        
        self.memory.store_brief({
            "date": date_str,
            "content": brief_text,
            "top_events": [e.get("title", "") if isinstance(e, dict) else str(e) for e in events[:5]],
            "escalation_risks": list(risk_scores.keys())[:5] if isinstance(risk_scores, dict) else []
        })
        
        clean_text = sanitize_for_telegram(brief_text)
        self.telegram.send_message(clean_text)
        
        state["brief"] = brief_text
        state["status"] = "briefed"
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for pipeline"""
    agent = OptimizedBriefAgent()
    return agent.run(state)
