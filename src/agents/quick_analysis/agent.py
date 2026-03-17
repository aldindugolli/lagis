# LAGIS - Fast Analysis Agent
# Rule-based analysis for ultra-fast processing (no LLM)
# Target: 45-60 second pipeline runtime

from typing import Dict, Any, List
from datetime import datetime


class FastAnalysisAgent:
    """Ultra-fast rule-based analysis (no LLM calls)"""
    
    def __init__(self):
        pass
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fast analysis - rule-based, no LLM"""
        relevant_articles = state.get("relevant_articles", [])
        articles = relevant_articles if relevant_articles else state.get("articles", [])
        
        if not articles:
            state["analysis_text"] = "No articles to analyze."
            state["events"] = []
            state["status"] = "analyzed"
            return state
        
        # Process only top 3 articles
        top_articles = articles[:3]
        
        events = []
        countries_set = set()
        severity_scores = []
        
        keywords_severity = {
            "war": 9, "military": 7, "invasion": 9, "strike": 7,
            "missile": 8, "bombing": 8, "nuclear": 10, "sanctions": 6,
            "protest": 4, "coup": 8, "crisis": 7, "attack": 7,
            "conflict": 7, "escalation": 8, "tension": 6, "deadly": 8
        }
        
        for article in top_articles:
            title = article.get("title", "")
            content = article.get("content", "")
            text = (title + " " + content).lower()
            
            # Extract countries
            countries = []
            country_keywords = {
                "russia": "Russia", "ukraine": "Ukraine", "iran": "Iran",
                "israel": "Israel", "china": "China", "usa": "United States",
                "korea": "Korea", "taiwan": "Taiwan", "nato": "NATO"
            }
            for kw, country in country_keywords.items():
                if kw in text:
                    countries.append(country)
                    countries_set.add(country)
            
            # Calculate severity
            severity = 5
            for kw, score in keywords_severity.items():
                if kw in text:
                    severity = max(severity, score)
            severity_scores.append(severity)
            
            # Determine risk level
            risk_level = "low"
            if severity >= 8:
                risk_level = "critical"
            elif severity >= 6:
                risk_level = "high"
            elif severity >= 4:
                risk_level = "medium"
            
            events.append({
                "title": title[:80],
                "countries": countries,
                "severity": severity,
                "implications": self._generate_implications(title, severity),
                "risk_level": risk_level
            })
        
        # Generate analysis text
        avg_severity = sum(severity_scores) / len(severity_scores) if severity_scores else 5
        
        if avg_severity >= 7:
            stability = "deteriorating"
            summary = f"High-severity events detected. Global stability is {stability} with {len(events)} critical events."
        elif avg_severity >= 5:
            stability = "stable"
            summary = f"Situational monitoring active. Global stability remains {stability}."
        else:
            stability = "stable"
            summary = "Low geopolitical tension detected. Situation remains stable."
        
        if countries_set:
            summary += f" Countries of interest: {', '.join(list(countries_set)[:5])}."
        
        state["events"] = events
        state["analysis_text"] = summary
        state["market_impact"] = "No significant market impact detected."
        state["risk_regions"] = list(countries_set)[:5] if countries_set else []
        state["status"] = "analyzed"
        
        return state
    
    def _generate_implications(self, title: str, severity: int) -> str:
        """Generate simple implications based on keywords"""
        title_lower = title.lower()
        
        if "war" in title_lower or "invasion" in title_lower:
            return "Potential for military escalation. International response likely."
        elif "sanction" in title_lower:
            return "Economic pressure may intensify. Trade relations affected."
        elif "nuclear" in title_lower:
            return "Strategic stability at risk. International concern high."
        elif "protest" in title_lower or "unrest" in title_lower:
            return "Political instability possible. Monitor for developments."
        else:
            return f"Event severity: {severity}/10. Monitor for escalation."


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for pipeline"""
    agent = FastAnalysisAgent()
    return agent.run(state)
