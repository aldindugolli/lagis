# LAGIS - Intelligence Engine
# Stage 5: Persistent geopolitical intelligence system
# Topic discovery, dossier building, world stability, escalation prediction

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from src.core.config import DATA_DIR
from src.core.llm.engine import get_llm
from src.core.memory.memory import get_memory
from src.agents.knowledge.agent import get_knowledge_agent

logger = logging.getLogger("LAGIS.Intelligence")


class IntelligenceEngine:
    """Comprehensive geopolitical intelligence system"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.topics_dir = self.data_dir / "topics"
        self.dossiers_dir = self.data_dir / "dossiers"
        self.world_state_file = self.data_dir / "world_state.json"
        
        self.topics_dir.mkdir(parents=True, exist_ok=True)
        self.dossiers_dir.mkdir(parents=True, exist_ok=True)
        
        self.llm = get_llm()
        self.memory = get_memory()
        self.knowledge = get_knowledge_agent()
        
        logger.info("Intelligence Engine initialized")
    
    # ==================== TOPIC DISCOVERY ====================
    
    def discover_topics(self, events: List[Dict]) -> List[Dict]:
        """Automatically discover emerging geopolitical topics"""
        if not events:
            return []
        
        existing_topics = self._load_existing_topics()
        
        new_topics = []
        
        topic_keywords = {
            "ukraine_war": ["ukraine", "russia", "kremlin", "kyiv", "moscow", "putin", "invasion"],
            "iran_nuclear": ["iran", "nuclear", "uranium", "tehran", "iaea", "enrichment"],
            "taiwan_strait": ["taiwan", "china", "beijing", "cross-strait", "xi"],
            "south_china_sea": ["south china sea", "spratly", "scarborough", "nine-dash"],
            "nato_expansion": ["nato", "expansion", "stockholm", "finland", "membership"],
            "sahel_instability": ["sahel", "mali", "niger", "burkina faso", "coup"],
            "red_sea_crisis": ["red sea", "houthi", "yemen", "shipping", "suez"],
            "balkans": ["kosovo", "serbia", "balkans", "belgrade", "pristina"],
            "us_china_rivalry": ["united states", "china", "washington", "beijing", "tariff"],
            "middle_east": ["israel", "gaza", "hamas", "netanyahu", "ceasefire"]
        }
        
        for event in events:
            text = (event.get("event_title", "") + " " + event.get("summary", "")).lower()
            
            for topic_name, keywords in topic_keywords.items():
                if any(kw in text for kw in keywords):
                    if topic_name not in [t.get("name") for t in existing_topics + new_topics]:
                        new_topics.append({
                            "name": topic_name,
                            "created_at": datetime.now().isoformat(),
                            "event_count": 1,
                            "actors": event.get("countries_involved", []),
                            "region": self._infer_region(topic_name),
                            "trend_score": event.get("severity_score", 5),
                            "keywords": keywords
                        })
        
        for topic in new_topics:
            self._save_topic(topic)
        
        logger.info(f"Discovered {len(new_topics)} new topics")
        return existing_topics + new_topics
    
    def _infer_region(self, topic: str) -> str:
        """Infer geographic region from topic"""
        region_map = {
            "ukraine_war": "Eastern Europe",
            "iran_nuclear": "Middle East",
            "taiwan_strait": "East Asia",
            "south_china_sea": "East Asia",
            "nato_expansion": "Europe",
            "sahel_instability": "Africa",
            "red_sea_crisis": "Middle East",
            "balkans": "Balkans",
            "us_china_rivalry": "Global",
            "middle_east": "Middle East"
        }
        return region_map.get(topic, "Global")
    
    def _load_existing_topics(self) -> List[Dict]:
        """Load existing topics"""
        topics = []
        for f in self.topics_dir.glob("*.json"):
            try:
                with open(f, 'r') as fp:
                    topics.append(json.load(fp))
            except:
                pass
        return topics
    
    def _save_topic(self, topic: Dict) -> None:
        """Save topic to file"""
        filename = self.topics_dir / f"{topic['name']}.json"
        with open(filename, 'w') as f:
            json.dump(topic, f, indent=2)
    
    # ==================== DOSSIER SYSTEM ====================
    
    def build_dossiers(self, events: List[Dict]) -> List[str]:
        """Build long-term dossiers for geopolitical actors"""
        actors = self._extract_actors(events)
        
        dossier_files = []
        
        for actor in actors[:10]:
            dossier = self._create_dossier(actor, events)
            if dossier:
                filename = self.dossiers_dir / f"{actor.lower().replace(' ', '_')}.json"
                with open(filename, 'w') as f:
                    json.dump(dossier, f, indent=2)
                dossier_files.append(actor)
        
        logger.info(f"Built dossiers for {len(dossier_files)} actors")
        return dossier_files
    
    def _extract_actors(self, events: List[Dict]) -> List[str]:
        """Extract geopolitical actors from events"""
        actors = set()
        for event in events:
            for actor in event.get("countries_involved", []):
                actors.add(actor)
        return list(actors)
    
    def _create_dossier(self, actor: str, events: List[Dict]) -> Optional[Dict]:
        """Create dossier for an actor"""
        actor_events = [e for e in events if actor in e.get("countries_involved", [])]
        
        if not actor_events:
            return None
        
        prompt = f"""Create a concise intelligence dossier for {actor.upper()}.

Recent events:
{chr(10).join([f"- {e.get('event_title', '')[:80]}" for e in actor_events[:10]])}

Provide JSON:
{{
    "actor": "{actor}",
    "type": "country/organization",
    "current_situation": "1-2 sentences",
    "key_allies": ["list"],
    "key_adversaries": ["list"],
    "military_capability": "brief assessment",
    "economic_position": "brief assessment",
    "strategic_objectives": ["list"],
    "recent_timeline": ["event 1", "event 2", "event 3"],
    "risk_factors": ["list"],
    "last_updated": "{datetime.now().isoformat()}"
}}"""
        
        try:
            result = self.llm.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=512,
                system="You create concise intelligence dossiers."
            )
            dossier = json.loads(result) if result.startswith('{') else {}
            return dossier
        except Exception as e:
            logger.warning(f"Dossier creation failed for {actor}: {e}")
            return {"actor": actor, "error": str(e)}
    
    # ==================== WORLD STABILITY MODEL ====================
    
    def update_world_stability(self, events: List[Dict], risk_scores: Dict) -> Dict:
        """Update global stability model"""
        stability = {
            "timestamp": datetime.now().isoformat(),
            "indicators": self._calculate_indicators(events, risk_scores),
            "conflict_zones": self._identify_conflict_zones(events),
            "sanctions_tracking": self._track_sanctions(events),
            "alliance_shifts": self._detect_alliance_shifts(events),
            "nuclear_risk": self._assess_nuclear_risk(events),
            "overall_index": 0.0
        }
        
        stability["overall_index"] = self._calculate_stability_index(stability)
        
        with open(self.world_state_file, 'w') as f:
            json.dump(stability, f, indent=2)
        
        logger.info(f"World stability index: {stability['overall_index']:.1f}/10")
        return stability
    
    def _calculate_indicators(self, events: List[Dict], risk_scores: Dict) -> Dict:
        """Calculate stability indicators"""
        high_severity = len([e for e in events if e.get("severity_score", 0) >= 7])
        military_events = len([e for e in events if "military" in e.get("event_type", "").lower()])
        economic_events = len([e for e in events if "economic" in e.get("event_type", "").lower()])
        
        return {
            "conflict_intensity": min(high_severity * 2, 10),
            "military_activity": min(military_events * 1.5, 10),
            "economic_stress": min(economic_events * 1.5, 10),
            "diplomatic_tension": min(len(events) * 0.3, 10)
        }
    
    def _identify_conflict_zones(self, events: List[Dict]) -> List[Dict]:
        """Identify active conflict zones"""
        zones = defaultdict(lambda: {"events": 0, "severity": 0, "locations": set()})
        
        for event in events:
            if event.get("severity_score", 0) >= 5:
                for country in event.get("countries_involved", []):
                    zones[country]["events"] += 1
                    zones[country]["severity"] += event.get("severity_score", 0)
                    zones[country]["locations"].add(country)
        
        conflict_zones = []
        for country, data in zones.items():
            if data["events"] >= 2:
                conflict_zones.append({
                    "region": country,
                    "event_count": data["events"],
                    "avg_severity": data["severity"] / data["events"],
                    "status": "active" if data["severity"] / data["events"] >= 6 else "monitoring"
                })
        
        return sorted(conflict_zones, key=lambda x: x["avg_severity"], reverse=True)[:10]
    
    def _track_sanctions(self, events: List[Dict]) -> List[str]:
        """Track sanctions-related events"""
        sanctions = []
        for event in events:
            text = (event.get("event_title", "") + " " + event.get("summary", "")).lower()
            if "sanction" in text:
                sanctions.append(event.get("event_title", "")[:60])
        return sanctions[:10]
    
    def _detect_alliance_shifts(self, events: List[Dict]) -> List[str]:
        """Detect alliance-related events"""
        shifts = []
        keywords = ["alliance", "treaty", "partnership", "nato", "military agreement"]
        for event in events:
            text = (event.get("event_title", "") + " " + event.get("summary", "")).lower()
            if any(kw in text for kw in keywords):
                shifts.append(event.get("event_title", "")[:60])
        return shifts[:10]
    
    def _assess_nuclear_risk(self, events: List[Dict]) -> Dict:
        """Assess nuclear-related risks"""
        nuclear_keywords = ["nuclear", "uranium", "enrichment", "atomic", "weapon", "missile"]
        nuclear_events = []
        
        for event in events:
            text = (event.get("event_title", "") + " " + event.get("summary", "")).lower()
            if any(kw in text for kw in nuclear_keywords):
                nuclear_events.append({
                    "event": event.get("event_title", "")[:60],
                    "severity": event.get("severity_score", 0)
                })
        
        return {
            "nuclear_events_count": len(nuclear_events),
            "risk_level": "high" if len(nuclear_events) >= 3 else "medium" if len(nuclear_events) >= 1 else "low",
            "events": nuclear_events[:5]
        }
    
    def _calculate_stability_index(self, stability: Dict) -> float:
        """Calculate overall stability index (0-10)"""
        indicators = stability.get("indicators", {})
        
        if not indicators:
            return 5.0
        
        weights = {
            "conflict_intensity": 0.35,
            "military_activity": 0.25,
            "economic_stress": 0.20,
            "diplomatic_tension": 0.20
        }
        
        index = sum(indicators.get(k, 5) * w for k, w in weights.items())
        return round(10 - index, 1)
    
    # ==================== ESCALATION PREDICTION ====================
    
    def predict_escalation(self, events: List[Dict]) -> List[Dict]:
        """Estimate escalation probability for major events"""
        predictions = []
        
        high_severity = [e for e in events if e.get("severity_score", 0) >= 6]
        
        for event in high_severity:
            prediction = self._analyze_escalation(event)
            predictions.append(prediction)
        
        return sorted(predictions, key=lambda x: x["conflict_probability"], reverse=True)[:10]
    
    def _analyze_escalation(self, event: Dict) -> Dict:
        """Analyze escalation factors for an event"""
        text = (event.get("event_title", "") + " " + event.get("summary", "")).lower()
        
        military_factor = 0
        if any(kw in text for kw in ["military", "army", "troops", "soldiers", "attack", "invasion"]):
            military_factor = 3
        
        nuclear_factor = 0
        if any(kw in text for kw in ["nuclear", "weapon", "missile", "atomic"]):
            nuclear_factor = 4
        
        alliance_factor = 0
        if any(kw in text for kw in ["nato", "alliance", "treaty", "commitment"]):
            alliance_factor = 2
        
        escalation_trend = 0
        if any(kw in text for kw in ["escalat", "increasing", "growing", "worsen"]):
            escalation_trend = 2
        
        economic_factor = 0
        if any(kw in text for kw in ["sanction", "trade war", "embargo", "oil", "energy"]):
            economic_factor = 2
        
        total_risk = military_factor + nuclear_factor + alliance_factor + escalation_trend + economic_factor
        conflict_probability = min(total_risk / 15 * 100, 100)
        
        return {
            "event": event.get("event_title", "")[:60],
            "conflict_probability": round(conflict_probability, 1),
            "risk_factors": {
                "military_confrontation": military_factor,
                "nuclear_states": nuclear_factor,
                "alliance_commitments": alliance_factor,
                "escalation_trend": escalation_trend,
                "economic_warfare": economic_factor
            },
            "strategic_implications": self._generate_implications(event, conflict_probability),
            "severity": event.get("severity_score", 5)
        }
    
    def _generate_implications(self, event: Dict, probability: float) -> str:
        """Generate strategic implications text"""
        if probability >= 70:
            return "HIGH RISK - Immediate attention required. Potential for armed conflict."
        elif probability >= 40:
            return "MODERATE RISK - Situation deteriorating. Monitor closely."
        else:
            return "LOW-MODERATE RISK - Maintain awareness."
    
    # ==================== GLOBAL RISK MAP ====================
    
    def generate_risk_map(self, events: List[Dict], risk_scores: Dict) -> Dict:
        """Generate global risk map summary"""
        risk_map = {
            "generated_at": datetime.now().isoformat(),
            "hotspots": [],
            "rising_regions": [],
            "stable_regions": [],
            "watchlist": []
        }
        
        stability = self._load_world_stability()
        
        if stability:
            risk_map["overall_stability"] = stability.get("overall_index", 5.0)
            risk_map["conflict_zones"] = stability.get("conflict_zones", [])
        
        high_risk = [(c, r) for c, r in risk_scores.items() if r.get("overall_risk_score", 0) >= 6]
        for country, risk in sorted(high_risk, key=lambda x: x[1].get("overall_risk_score", 0), reverse=True)[:10]:
            risk_map["hotspots"].append({
                "country": country,
                "risk_score": risk.get("overall_risk_score", 0),
                "trend": risk.get("trend", "stable")
            })
        
        trends = self._analyze_trends(events)
        risk_map["rising_regions"] = [t for t in trends if t.get("direction") == "escalating"][:5]
        
        return risk_map
    
    def _load_world_stability(self) -> Optional[Dict]:
        """Load current world stability data"""
        if self.world_state_file.exists():
            try:
                with open(self.world_state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def _analyze_trends(self, events: List[Dict]) -> List[Dict]:
        """Analyze trends from events"""
        topics = ["ukraine", "iran", "china", "taiwan", "korea", "israel", "russia", "nato"]
        trends = []
        
        for topic in topics:
            topic_events = [e for e in events if topic.lower() in (e.get("event_title", "") + e.get("summary", "")).lower()]
            if topic_events:
                avg_severity = sum(e.get("severity_score", 0) for e in topic_events) / len(topic_events)
                direction = "escalating" if avg_severity >= 6 else "stable" if avg_severity >= 4 else "de-escalating"
                trends.append({
                    "topic": topic,
                    "direction": direction,
                    "event_count": len(topic_events),
                    "avg_severity": round(avg_severity, 1)
                })
        
        return trends
    
    # ==================== MAIN RUN ====================
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run full intelligence processing"""
        events = state.get("events", [])
        risk_scores = state.get("risk_scores", {})
        
        topics = self.discover_topics(events)
        dossiers = self.build_dossiers(events)
        world_stability = self.update_world_stability(events, risk_scores)
        escalation_predictions = self.predict_escalation(events)
        risk_map = self.generate_risk_map(events, risk_scores)
        
        state["intelligence"] = {
            "topics_discovered": len(topics),
            "dossiers_created": len(dossiers),
            "world_stability_index": world_stability.get("overall_index", 5.0),
            "escalation_predictions": escalation_predictions,
            "risk_map": risk_map
        }
        
        logger.info(f"Intelligence: {len(topics)} topics, {len(dossiers)} dossiers, stability={world_stability.get('overall_index', 5.0):.1f}")
        
        return state


_intelligence_engine: Optional[IntelligenceEngine] = None


def get_intelligence_engine() -> IntelligenceEngine:
    global _intelligence_engine
    if _intelligence_engine is None:
        _intelligence_engine = IntelligenceEngine()
    return _intelligence_engine


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    engine = get_intelligence_engine()
    return engine.process(state)
