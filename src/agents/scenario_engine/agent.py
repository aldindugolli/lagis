# LAGIS - Scenario Engine Agent
# Rule-based probabilistic scenario generation with graph intelligence
# NO LLM calls - fully rule-based inference

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.config import DATA_DIR

logger = logging.getLogger("LAGIS.ScenarioEngine")

SCENARIOS_DIR = DATA_DIR / "scenarios"
PROBABILITY_THRESHOLDS = {"HIGH": 15, "MEDIUM": 10}


class ActorRiskLevel:
    IRAN = 8
    ISRAEL = 7
    RUSSIA = 7
    CHINA = 6
    USA = 6
    NORTH_KOREA = 8
    HEZBOLLAH = 7
    
    @classmethod
    def get(cls, actor: str) -> int:
        actor = actor.upper()
        return getattr(cls, actor, 5)


class GraphScenarioBoost:
    """Boost scenario probability based on graph relationships"""
    
    @staticmethod
    def get_proxy_relationship(graph, actor: str) -> Optional[float]:
        if hasattr(graph, 'get_allies'):
            allies = graph.get_allies(actor)
            for ally in allies:
                if ally.get("type") == "supports" and ally.get("weight", 0) >= 0.7:
                    return ally.get("weight")
        return None
    
    @staticmethod
    def get_conflict_intensity(graph, actor1: str, actor2: str) -> float:
        if hasattr(graph, 'get_conflicts'):
            conflicts = graph.get_conflicts(actor1)
            for conflict in conflicts:
                if conflict.get("actor") == actor2:
                    return conflict.get("weight", 0)
        return 0.5
    
    @staticmethod
    def has_allied_support(graph, actor: str) -> Optional[str]:
        if hasattr(graph, 'get_allies'):
            allies = graph.get_allies(actor)
            for ally in allies:
                if ally.get("weight", 0) >= 0.8:
                    return ally.get("actor")
        return None


class ScenarioTemplates:
    TEMPLATES = [
        {
            "pattern": ["airstrike", "iran"],
            "title": "Iran retaliates via proxy forces",
            "actors": ["Iran", "Hezbollah", "Israel"],
            "description": "Iran avoids direct confrontation but escalates through Hezbollah attacks on Israel",
            "impact": ["Regional instability increases", "Israel defense systems under pressure", "Risk of Lebanon escalation"]
        },
        {
            "pattern": ["airstrike", "iran"],
            "title": "Iran launches direct missile response",
            "actors": ["Iran", "Israel", "US"],
            "description": "Iran responds with direct missile strikes against Israeli or US regional assets",
            "impact": ["Direct Iran-Israel military exchange", "US involvement escalation", "Oil facility risk"]
        },
        {
            "pattern": ["missile", "israel"],
            "title": "Israel escalates air campaign",
            "actors": ["Israel", "Lebanon", "Syria"],
            "description": "Israel intensifies airstrikes targeting Iranian assets in Syria and Lebanon",
            "impact": ["Syrian airspace tensions", "Russian involvement risk", "Regional humanitarian crisis"]
        },
        {
            "pattern": ["oil", "facility"],
            "title": "Energy infrastructure disruption",
            "actors": ["Iran", "US", "Global Markets"],
            "description": "Attacks or threats targeting oil infrastructure cause market volatility",
            "impact": ["Oil price surge", "Shipping disruption through Strait of Hormuz", "Energy security crisis"]
        },
        {
            "pattern": ["troops", "deployment"],
            "title": "Military mobilization accelerates",
            "actors": ["US", "Iran", "Regional Allies"],
            "description": "Troop movements signal preparation for potential escalation",
            "impact": ["Regional military buildup", "Diplomatic channels close", "Escalation momentum"]
        },
        {
            "pattern": ["sanctions", "iran"],
            "title": "Economic pressure intensifies",
            "actors": ["Iran", "US", "EU"],
            "description": "New sanctions target Iranian economy, increasing regime desperation",
            "impact": ["Iran nuclear compliance risk", "Regional economic instability", "Gray market expansion"]
        },
        {
            "pattern": ["drone", "attack"],
            "title": "Autonomous weapons escalation",
            "actors": ["Iran", "US", "Ukraine"],
            "description": "Drone attacks proliferate as preferred method of remote strikes",
            "impact": ["Civilian casualties risk", "Counter-drone technology race", "Escalation ambiguity"]
        },
        {
            "pattern": ["nuclear", "enrichment"],
            "title": "Nuclear program acceleration",
            "actors": ["Iran", "Israel", "US"],
            "description": "Iran resumes higher-level uranium enrichment in response to pressure",
            "impact": ["Nuclear weapons proximity", "Israeli preemptive strike risk", "International crisis"]
        },
        {
            "pattern": ["hezbollah", "israel"],
            "title": "Lebanon front opens",
            "actors": ["Hezbollah", "Israel", "Lebanon"],
            "description": "Hezbollah launches sustained attacks opening northern Israel front",
            "impact": ["Lebanon sovereignty erosion", "Refugee crisis", "Iran-Israel direct war path"]
        },
        {
            "pattern": ["warning", "ultimatum"],
            "title": "Diplomatic breakdown",
            "actors": ["US", "Iran", "EU"],
            "description": "Failed negotiations lead to hardline positions on both sides",
            "impact": ["No off-ramps remaining", "Military timeline accelerates", "Regional alignment shifts"]
        }
    ]
    
    @classmethod
    def find_matches(cls, events: List[Dict]) -> List[Dict]:
        matches = []
        event_texts = []
        
        for e in events:
            if isinstance(e, dict):
                title = e.get("title", "").lower()
                countries = " ".join(e.get("countries", [])).lower()
                event_texts.append(title + " " + countries)
        
        all_text = " ".join(event_texts)
        
        for template in cls.TEMPLATES:
            pattern_matches = sum(1 for kw in template["pattern"] if kw in all_text)
            if pattern_matches >= 2:
                matches.append(template)
        
        return matches


class ScenarioScorer:
    
    @staticmethod
    def calculate(event_severity: int, signal_strength: int, actor_risks: List[int], 
                  graph_boost: float = 0) -> int:
        actor_risk = max(actor_risks) if actor_risks else 5
        
        score = event_severity + signal_strength + actor_risk + graph_boost
        
        return min(score, 20)
    
    @staticmethod
    def probability_from_score(score: int) -> str:
        if score >= PROBABILITY_THRESHOLDS["HIGH"]:
            return "HIGH"
        elif score >= PROBABILITY_THRESHOLDS["MEDIUM"]:
            return "MEDIUM"
        else:
            return "LOW"
    
    @staticmethod
    def timeframe_from_probability(probability: str) -> str:
        if probability == "HIGH":
            return "24-72h"
        elif probability == "MEDIUM":
            return "3-7 days"
        else:
            return "1-2 weeks"


class ScenarioEngine:
    
    def __init__(self):
        self.templates = ScenarioTemplates()
        self.scorer = ScenarioScorer()
        self.graph_booster = GraphScenarioBoost()
    
    def _extract_trigger(self, events: List[Dict], template: Dict) -> str:
        for e in events:
            if isinstance(e, dict):
                title = e.get("title", "").lower()
                if any(kw in title for kw in template["pattern"]):
                    return title[:60] + "..." if len(title) > 60 else title
        return f"Current escalation involving {', '.join(template['actors'][:2])}"
    
    def _get_graph_context(self, template: Dict, graph) -> str:
        context_parts = []
        
        for actor in template["actors"]:
            if hasattr(graph, 'get_related_actors'):
                related = graph.get_related_actors(actor, depth=1)
                if related["direct"]:
                    context_parts.append(f"{actor} connected to {len(related['direct'])} actors")
            
            proxy = self.graph_booster.get_proxy_relationship(graph, actor)
            if proxy:
                context_parts.append(f"{actor} has strong proxy network (weight: {proxy:.1f})")
        
        return "; ".join(context_parts[:2]) if context_parts else ""
    
    def _generate_scenario(self, template: Dict, events: List[Dict], signal_strength: int, graph=None) -> Dict:
        event_severity = 0
        for e in events:
            if isinstance(e, dict):
                event_severity = max(event_severity, e.get("severity", 5))
        
        actor_risks = [ActorRiskLevel.get(a) for a in template["actors"]]
        
        graph_boost = 0
        if graph:
            for actor in template["actors"]:
                proxy_weight = self.graph_booster.get_proxy_relationship(graph, actor)
                if proxy_weight and proxy_weight >= 0.7:
                    graph_boost += 2
                
                conflict_intensity = self.graph_booster.get_conflict_intensity(
                    graph, actor, template["actors"][0] if template["actors"] else ""
                )
                if conflict_intensity >= 0.8:
                    graph_boost += 1
        
        score = self.scorer.calculate(event_severity, signal_strength, actor_risks, graph_boost)
        probability = self.scorer.probability_from_score(score)
        timeframe = self.scorer.timeframe_from_probability(probability)
        
        graph_context = self._get_graph_context(template, graph) if graph else ""
        
        return {
            "title": template["title"],
            "probability": probability,
            "timeframe": timeframe,
            "trigger": self._extract_trigger(events, template),
            "actors": template["actors"],
            "description": template["description"],
            "impact": template["impact"][:2],
            "score": score,
            "graph_context": graph_context
        }
    
    def generate(self, events: List[Dict], early_signals: List[Dict], graph=None) -> List[Dict]:
        if not events:
            return []
        
        matches = self.templates.find_matches(events)
        
        if not matches:
            matches = [self.templates.TEMPLATES[0]]
        
        signal_strength = 1
        for sig in early_signals:
            if sig.get("confidence") == "high":
                signal_strength = 3
                break
            elif sig.get("confidence") == "medium":
                signal_strength = 2
        
        scenarios = []
        for template in matches[:5]:
            scenario = self._generate_scenario(template, events, signal_strength, graph)
            scenarios.append(scenario)
        
        scenarios.sort(key=lambda x: x["score"], reverse=True)
        
        high = [s for s in scenarios if s["probability"] == "HIGH"][:1]
        medium = [s for s in scenarios if s["probability"] == "MEDIUM"][:1]
        low = [s for s in scenarios if s["probability"] == "LOW"][:1]
        
        final = high + medium + low
        
        return final[:3]
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        events = state.get("deduplicated_events", []) or state.get("events", [])
        early_signals = state.get("early_signals", [])
        graph = state.get("graph")
        
        scenarios = self.generate(events, early_signals, graph)
        
        state["scenarios"] = scenarios
        
        if scenarios:
            logger.info(f"Generated {len(scenarios)} scenarios")
            for s in scenarios[:3]:
                logger.info(f"  [{s['probability']}] {s['title'][:50]} ({s['timeframe']})")
                if s.get("graph_context"):
                    logger.info(f"    Context: {s['graph_context']}")
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    engine = ScenarioEngine()
    return engine.run(state)
