# LAGIS - Context Agent
# Retrieves comprehensive historical, political, and strategic context before analysis

import json
import logging
from typing import Dict, Any, List, Set
from datetime import datetime, timedelta
from collections import defaultdict

from src.agents.knowledge.agent import get_knowledge_agent
from src.core.memory.memory import get_memory
from src.core.world_model.engine import get_world_model

logger = logging.getLogger("LAGIS.Context")


ACTOR_KEYWORDS = {
    "countries": ["russia", "ukraine", "china", "usa", "iran", "israel", "saudi", "nato", "eu", "india", "pakistan", "korea", "japan", "germany", "france", "uk", "turkey", "brazil", "kosovo", "serbia"],
    "organizations": ["nato", "eu", "un", "osce", "who", "opec", "wto", "asean", "au"],
    "actors": ["putin", "biden", "trump", "netanyahu", "khamenei", "xi", "erdogan", "boris johnson"]
}

STRATEGIC_TOPICS = [
    "military", "conflict", "war", "invasion", "attack", "ceasefire", "peace",
    "sanctions", "trade", "economy", "energy", "oil", "gas",
    "nuclear", "weapon", "missile", "troops", "military buildup",
    "diplomacy", "summit", "treaty", "agreement", "negotiation",
    "alliance", "partnership", "coalition", "security",
    "protest", "revolution", "coup", "election", "regime"
]


class ContextAgent:
    """Retrieves comprehensive historical context for informed geopolitical analysis"""
    
    def __init__(self):
        self.knowledge = get_knowledge_agent()
        self.memory = get_memory()
        self.world_model = get_world_model()
    
    def _extract_geopolitical_actors(self, events: List[Dict]) -> Dict[str, List[str]]:
        """Extract geopolitical actors from events"""
        actors = {"countries": set(), "organizations": set(), "issues": set()}
        
        for event in events:
            text = (event.get("event_title", "") + " " + event.get("summary", "")).lower()
            
            for country in ACTOR_KEYWORDS["countries"]:
                if country in text:
                    actors["countries"].add(country.title())
            
            for org in ACTOR_KEYWORDS["organizations"]:
                if org in text.upper():
                    actors["organizations"].add(org.upper())
            
            for topic in STRATEGIC_TOPICS:
                if topic in text:
                    actors["issues"].add(topic)
        
        return {k: list(v) for k, v in actors.items()}
    
    def _get_historical_events(self, topic: str, days: int = 90) -> List[Dict]:
        """Get historical events from memory"""
        try:
            import sqlite3
            conn = sqlite3.connect(str(self.memory.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM events
                WHERE event_title LIKE ? OR summary LIKE ?
                AND created_at >= datetime('now', '-' || ? || ' days')
                ORDER BY severity_score DESC, created_at DESC
            """, (f"%{topic}%", f"%{topic}%", days))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.warning(f"Failed to get historical events: {e}")
            return []
    
    def _get_country_context(self, countries: List[str]) -> Dict[str, Any]:
        """Get country context from world model"""
        country_context = {}
        
        for country in countries[:5]:
            try:
                country_data = self.world_model.get_country(country)
                if country_data:
                    country_context[country] = {
                        "stability": country_data.get("stability_score", "unknown"),
                        "economic_health": country_data.get("economic_health", "unknown"),
                        "military_posture": country_data.get("military_posture", "unknown"),
                    }
            except Exception:
                pass
        
        return country_context
    
    def _analyze_alliance_dynamics(self, countries: List[str]) -> str:
        """Analyze alliance relationships between involved countries"""
        alliance_groups = {
            "nato": ["usa", "germany", "france", "uk", "italy", "canada", "poland", "turkey"],
            "post_soviet": ["russia", "belarus", "kazakhstan", "armenia", "kyrgyzstan"],
            "brics": ["china", "india", "russia", "brazil", "south africa", "iran", "saudi"]
        }
        
        found_groups = []
        for group_name, members in alliance_groups.items():
            intersection = [c.lower() for c in countries if c.lower() in members]
            if len(intersection) >= 2:
                found_groups.append(f"{group_name.upper()} members: {', '.join(intersection)}")
        
        if found_groups:
            return "Alliance dynamics: " + "; ".join(found_groups)
        return ""
    
    def _analyze_economic_dependencies(self, countries: List[str]) -> str:
        """Analyze economic relationships"""
        economic_pairs = [
            ("russia", "china", "energy, trade"),
            ("germany", "russia", "energy, manufacturing"),
            ("usa", "china", "trade, technology"),
            ("iran", "china", "energy, trade"),
            ("saudi", "usa", "energy, security"),
            ("ukraine", "eu", "trade, agriculture"),
        ]
        
        dependencies = []
        for c1, c2, rel in economic_pairs:
            if c1 in [x.lower() for x in countries] and c2 in [x.lower() for x in countries]:
                dependencies.append(f"{c1.title()}-{c2.title()}: {rel}")
        
        if dependencies:
            return "Economic dependencies: " + "; ".join(dependencies)
        return ""
    
    def _build_strategic_context(self, actors: Dict[str, List[str]], events: List[Dict]) -> str:
        """Build comprehensive strategic context"""
        context_parts = []
        
        countries = actors.get("countries", [])
        issues = actors.get("issues", [])
        
        if countries:
            country_context = self._get_country_context(countries)
            if country_context:
                context_parts.append("\n[COUNTRY STATUS]")
                for c, data in country_context.items():
                    context_parts.append(f"  {c}: stability={data.get('stability')}, economy={data.get('economic_health')}")
            
            alliance_context = self._analyze_alliance_dynamics(countries)
            if alliance_context:
                context_parts.append(f"\n{alliance_context}")
            
            economic_context = self._analyze_economic_dependencies(countries)
            if economic_context:
                context_parts.append(f"\n{economic_context}")
        
        if issues:
            context_parts.append("\n[STRATEGIC ISSUES]")
            for issue in issues[:5]:
                historical = self._get_historical_events(issue, days=60)
                if historical:
                    context_parts.append(f"  {issue.upper()}: {len(historical)} recent events")
                    for h in historical[:2]:
                        context_parts.append(f"    - {h.get('event_title', '')[:60]}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _build_historical_context(self, events: List[Dict]) -> str:
        """Build historical event context"""
        context_parts = ["\n[HISTORICAL EVENTS]"]
        
        topics_to_check = []
        for event in events[:5]:
            title = event.get("event_title", "")
            for topic in STRATEGIC_TOPICS:
                if topic in title.lower():
                    topics_to_check.append(topic)
        
        topics_to_check = list(set(topics_to_check))[:3]
        
        for topic in topics_to_check:
            historical = self._get_historical_events(topic, days=90)
            if historical:
                context_parts.append(f"\n{topic.upper()} developments:")
                for h in historical[:3]:
                    date = h.get("created_at", "")[:10]
                    title = h.get("event_title", "")[:70]
                    severity = h.get("severity_score", 0)
                    context_parts.append(f"  [{date}] ({severity}) {title}")
        
        return "\n".join(context_parts)
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve comprehensive strategic context before analysis"""
        events = state.get("events", [])
        
        if not events:
            logger.info("No events for context retrieval")
            state["strategic_context"] = "No events available."
            state["actors"] = {}
            return state
        
        actors = self._extract_geopolitical_actors(events)
        
        strategic_context = self._build_strategic_context(actors, events)
        
        historical_context = self._build_historical_context(events)
        
        full_context = f"""STRATEGIC INTELLIGENCE CONTEXT
{'='*40}
{strategic_context}
{historical_context}
{'='*40}"""
        
        state["strategic_context"] = full_context
        state["actors"] = actors
        
        logger.info(f"Context retrieved for: {len(actors.get('countries', []))} countries, {len(actors.get('issues', []))} issues")
        state["status"] = "context_retrieved"
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = ContextAgent()
    return agent.run(state)
