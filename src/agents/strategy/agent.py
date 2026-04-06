# LAGIS - Strategic Recommendations Agent
# Generates precise, actor-specific intelligence recommendations
# NO LLM calls - Pure rule-based mapping

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("LAGIS.Strategy")

PROXY_ACTORS = {
    "Iran": ["Hezbollah", "Hamas", "Houthis"],
    "Israel": [],
    "Russia": ["Wagner", "separatist forces"],
}

REGION_MAP = {
    "Iran": "Middle East",
    "Israel": "Middle East",
    "Hezbollah": "Lebanon/Syria border",
    "Hamas": "Gaza",
    "Houthis": "Red Sea/Yemen",
    "Russia": "Eastern Europe",
    "Ukraine": "Eastern Europe",
    "China": "Indo-Pacific",
    "Taiwan": "Taiwan Strait",
    "North Korea": "Korean Peninsula"
}


class StrategyAgent:
    
    def __init__(self):
        pass
    
    def _get_proxy_actors(self, state: Dict[str, Any]) -> Dict[str, List[str]]:
        graph = state.get("graph")
        proxies = {}
        
        if hasattr(graph, 'get_allies'):
            for main_actor, proxy_list in PROXY_ACTORS.items():
                proxies[main_actor] = proxy_list
        
        return proxies
    
    def _get_primary_actors(self, state: Dict[str, Any]) -> List[str]:
        actors = set()
        
        scenarios = state.get("scenarios", [])
        for s in scenarios:
            if s.get("probability") == "HIGH":
                for a in s.get("actors", [])[:2]:
                    actors.add(a)
        
        black_swan = state.get("black_swan_alerts", [])
        for alert in black_swan:
            if alert.get("risk") == "HIGH":
                for a in alert.get("actors", [])[:2]:
                    actors.add(a)
        
        risk_scores = state.get("synthesis", {}).get("risk_scores", {})
        if isinstance(risk_scores, dict):
            for country, score in risk_scores.items():
                if isinstance(score, int) and score >= 7:
                    actors.add(country)
        
        return list(actors)[:3]
    
    def _is_proxy_scenario(self, scenario: Dict) -> bool:
        title = scenario.get("title", "").lower()
        proxy_keywords = ["proxy", "hezbollah", "militia", "via"]
        return any(kw in title for kw in proxy_keywords)
    
    def _generate_proxy_recommendation(self, scenario: Dict, proxies: Dict) -> Optional[str]:
        title = scenario.get("title", "")
        actors = scenario.get("actors", [])
        
        main_actor = None
        for a in actors:
            if a in proxies:
                main_actor = a
                break
        
        if not main_actor:
            for a in actors:
                if a in PROXY_ACTORS:
                    main_actor = a
                    break
        
        if main_actor and main_actor in proxies:
            proxy_list = proxies[main_actor]
            if proxy_list:
                proxy = proxy_list[0]
                return f"Monitor {proxy} activity for indicators of {main_actor}-directed retaliation"
        
        return None
    
    def _generate_silence_recommendation(self, alert: Dict) -> str:
        actors = alert.get("actors", [])
        if actors:
            actor = actors[0]
            return f"Increase surveillance of {actor} communications due to abnormal silence indicating possible pre-event concealment"
        return "Investigate anomalous communications silence in the region"
    
    def _generate_military_recommendation(self, actors: List[str]) -> Optional[str]:
        if "Iran" in actors:
            return "Monitor Iranian Revolutionary Guard Corps positioning and regional force deployments"
        if "Russia" in actors:
            return "Track Russian military movements near conflict zones"
        if "China" in actors:
            return "Monitor PLA military posture in the Taiwan Strait area"
        return None
    
    def _generate_energy_recommendation(self, actors: List[str]) -> Optional[str]:
        if any(a in actors for a in ["Iran", "Russia"]):
            return "Assess Strait of Hormuz oil transit vulnerability to escalation"
        return None
    
    def _generate_alliance_recommendation(self, actors: List[str]) -> Optional[str]:
        if "US" in actors or "NATO" in str(actors):
            return "Track US diplomatic messaging and NATO force posture changes in theater"
        return None
    
    def _deduplicate(self, recs: List[str]) -> List[str]:
        seen = set()
        unique = []
        for r in recs:
            normalized = r.lower()[:60]
            if normalized not in seen:
                seen.add(normalized)
                unique.append(r)
        return unique
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            recommendations = []
            primary_actors = self._get_primary_actors(state)
            proxies = self._get_proxy_actors(state)
            
            scenarios = state.get("scenarios", [])
            for s in scenarios:
                if s.get("probability") == "HIGH":
                    if self._is_proxy_scenario(s):
                        proxy_rec = self._generate_proxy_recommendation(s, proxies)
                        if proxy_rec:
                            recommendations.append(("URGENT: " + proxy_rec, "high"))
                            break
            
            black_swan = state.get("black_swan_alerts", [])
            for alert in black_swan:
                if alert.get("risk") == "HIGH":
                    alert_type = alert.get("type", "")
                    if "Silence" in alert_type:
                        silence_rec = self._generate_silence_recommendation(alert)
                        recommendations.append(("IMMEDIATE: " + silence_rec, "critical"))
                        break
            
            synthesis = state.get("synthesis", {})
            escalation = synthesis.get("escalation_outlook", {})
            
            if escalation.get("direct_conflict") == "HIGH":
                military_rec = self._generate_military_recommendation(primary_actors)
                if military_rec:
                    recommendations.append(("URGENT: " + military_rec, "high"))
            
            if escalation.get("energy_supply") == "HIGH":
                energy_rec = self._generate_energy_recommendation(primary_actors)
                if energy_rec:
                    recommendations.append(("Monitor: " + energy_rec, "medium"))
            
            if escalation.get("us_involvement") == "HIGH":
                alliance_rec = self._generate_alliance_recommendation(primary_actors)
                if alliance_rec:
                    recommendations.append(("Track: " + alliance_rec, "medium"))
            
            unique_recs = []
            seen = set()
            for rec, priority in recommendations:
                key = rec.lower()[:50]
                if key not in seen:
                    seen.add(key)
                    unique_recs.append({"action": rec, "priority": priority})
            
            unique_recs.sort(key=lambda x: {"critical": 0, "high": 1, "medium": 2}.get(x["priority"], 3))
            final_recs = unique_recs[:3]
            
            if not final_recs:
                summary = "Standard threat monitoring posture."
            elif any(r["priority"] == "critical" for r in final_recs):
                summary = "Critical intelligence gaps require immediate investigation."
            else:
                summary = "Elevated threat level - enhanced monitoring advised."
            
            state["strategic_recommendations"] = {
                "summary": summary,
                "recommendations": final_recs
            }
            
            if final_recs:
                logger.info(f"Strategy: Generated {len(final_recs)} recommendations")
                for r in final_recs:
                    logger.info(f"  [{r['priority'].upper()}] {r['action'][:70]}")
            
        except Exception as e:
            logger.error(f"Error in strategy agent: {e}")
            state["strategic_recommendations"] = {
                "summary": "Continue standard monitoring.",
                "recommendations": []
            }
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = StrategyAgent()
    return agent.run(state)
