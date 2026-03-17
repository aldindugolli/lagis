# LAGIS - Intelligence Synthesis Agent
# Rule-based strategic intelligence analysis

import re
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger("LAGIS.IntelligenceSynthesis")


class IntelligenceSynthesisAgent:
    """Rule-based strategic intelligence (no LLM needed)"""
    
    def __init__(self):
        pass
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic intelligence synthesis"""
        try:
            events = state.get("deduplicated_events", []) or state.get("events", [])
            signals = state.get("signal_alerts", [])
            
            if not events:
                logger.warning("No events for synthesis")
                state["synthesis"] = {}
                state["stability_index"] = 7.0
                return state
            
            synthesis = self._analyze_events(events, signals)
            
            state["synthesis"] = synthesis
            
            stability = self._calculate_stability_index(events, signals)
            state["stability_index"] = stability
            
            return state
        except Exception as e:
            logger.error(f"Error in intelligence_synthesis: {e}")
            state["synthesis"] = {}
            state["stability_index"] = 7.0
            return state
    
    def _analyze_events(self, events: List[Dict], signals: List[Dict]) -> Dict:
        """Rule-based analysis of events"""
        
        countries = set()
        high_severity_events = []
        
        for e in events:
            if isinstance(e, dict):
                title = e.get("title", e.get("event_title", ""))
                severity = e.get("severity", 5)
                countries_list = e.get("countries", e.get("countries_involved", []))
                
                if severity >= 8:
                    high_severity_events.append(title)
                
                for c in countries_list:
                    countries.add(c)
        
        summary = self._generate_summary(events, countries)
        implications = self._generate_implications(events)
        escalation = self._assess_escalation(events)
        next_moves = self._predict_next_moves(events, countries)
        market = self._assess_market_impact(events)
        risk_scores = self._calculate_risk_scores(events, countries)
        
        return {
            "executive_summary": summary,
            "strategic_implications": implications,
            "escalation_outlook": escalation,
            "likely_next_moves": next_moves,
            "market_impact": market,
            "risk_scores": risk_scores
        }
    
    def _generate_summary(self, events: List[Dict], countries: set) -> str:
        """Generate executive summary"""
        high_sev = sum(1 for e in events if isinstance(e, dict) and e.get("severity", 0) >= 8)
        
        country_list = list(countries)[:4]
        country_str = ", ".join(country_list) if country_list else "multiple regions"
        
        if high_sev >= 2:
            return f"Serious escalation detected with {high_sev} high-severity events. Situation involving {country_str} requires immediate attention."
        elif high_sev >= 1:
            return f"Tensions elevated with {high_sev} significant event. Countries of interest: {country_str}."
        else:
            return f"Situation stable with monitoring active. Regions: {country_str}."
    
    def _generate_implications(self, events: List[Dict]) -> List[str]:
        """Generate strategic implications"""
        implications = []
        
        for e in events:
            if not isinstance(e, dict):
                continue
            title = e.get("title", "").lower()
            
            if any(kw in title for kw in ["oil", "energy", "facility"]):
                implications.append("Energy Security: Attacks on infrastructure threaten supply chains")
            if any(kw in title for kw in ["military", "strike", "attack"]):
                implications.append("Military Escalation: Direct strikes increase confrontation risk")
            if any(kw in title for kw in ["iran", "israel"]):
                implications.append("Regional Conflict: Iran-Israel tensions could spread to Lebanon/Syria")
            if any(kw in title for kw in ["us", "america"]):
                implications.append("Superpower Involvement: US direct involvement raises stakes")
        
        if not implications:
            implications = ["Monitor developments", "Assess regional impact"]
        
        return implications[:4]
    
    def _assess_escalation(self, events: List[Dict]) -> Dict:
        """Assess escalation levels"""
        high_sev = sum(1 for e in events if isinstance(e, dict) and e.get("severity", 0) >= 8)
        
        d = "HIGH" if high_sev >= 2 else "MODERATE"
        p = "MODERATE" 
        u = "HIGH" if any("US" in str(e) for e in events if isinstance(e, dict)) else "LOW"
        e = "HIGH" if any("oil" in str(e).lower() for e in events) else "LOW"
        
        return {
            "direct_conflict": d,
            "proxy_escalation": p,
            "us_involvement": u,
            "energy_supply": e
        }
    
    def _predict_next_moves(self, events: List[Dict], countries: set) -> List[str]:
        """Predict likely next moves"""
        predictions = []
        
        country_str = ", ".join(list(countries)[:3])
        
        if "Iran" in countries or "Israel" in countries:
            predictions.append("Iran may retaliate through proxy forces (Hezbollah)")
            predictions.append("Israel likely to intensify defensive operations")
        
        if "US" in countries:
            predictions.append("US may deploy additional military assets to region")
        
        if not predictions:
            predictions = ["Monitor for developments", "Watch for diplomatic activity"]
        
        return predictions[:3]
    
    def _assess_market_impact(self, events: List[Dict]) -> str:
        """Assess market impact"""
        has_oil = any("oil" in str(e).lower() for e in events)
        
        if has_oil:
            return "Oil prices likely to rise. Energy markets face volatility."
        else:
            return "Limited market impact expected. Monitor energy sector."
    
    def _calculate_risk_scores(self, events: List[Dict], countries: set) -> Dict:
        """Calculate risk scores for countries"""
        scores = {}
        
        for c in countries:
            if not isinstance(c, str):
                continue
            score = 5
            for e in events:
                if not isinstance(e, dict):
                    continue
                title = (e.get("title", "") + " " + str(e.get("countries", []))).lower()
                if c.lower() in title:
                    score = max(score, e.get("severity", 5))
            
            scores[c] = score
        
        return scores
    
    def _calculate_stability_index(self, events: List[Dict], signals: List[Dict]) -> float:
        """Calculate global stability index"""
        base = 8.0
        
        severity_sum = 0
        for e in events:
            if isinstance(e, dict):
                severity_sum += e.get("severity", 5)
            else:
                severity_sum += 5
        
        avg_severity = severity_sum / len(events) if events else 5
        signal_count = len(signals) if signals else 0
        
        stability = base - ((avg_severity - 5) * 0.3) - (signal_count * 0.2)
        
        for event in events:
            if isinstance(event, dict):
                title = event.get("title", "").lower()
                if any(kw in title for kw in ["nuclear", "war", "invasion"]):
                    stability -= 0.5
        
        return round(max(0, min(10, stability)), 1)


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for pipeline"""
    agent = IntelligenceSynthesisAgent()
    return agent.run(state)
