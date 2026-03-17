# LAGIS - Geopolitical Memory Graph
# Stores relationships between actors for contextual intelligence

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Set
from datetime import datetime
from difflib import SequenceMatcher

from src.core.config import DATA_DIR

logger = logging.getLogger("LAGIS.MemoryGraph")


class GeopoliticalMemoryGraph:
    """Manages persistent geopolitical relationships"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.graph_file = self.data_dir / "geopolitical_graph.json"
        self.graph_file.parent.mkdir(parents=True, exist_ok=True)
        self.graph = self._load_graph()
        
        self.relationship_keywords = {
            "allies": ["allied", "alliance", "partner", "support", "backed by", "cooperate"],
            "adversaries": ["enemy", "adversary", "hostile", "confront", "attack", "war", "conflict"],
            "conflicts": ["war", "conflict", "battle", "fighting", "clashes"],
        }
    
    def _load_graph(self) -> Dict:
        """Load existing graph or create new"""
        if self.graph_file.exists():
            try:
                with open(self.graph_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return self._create_default_graph()
    
    def _create_default_graph(self) -> Dict:
        """Create default relationships based on known geopolitics"""
        return {
            "Iran": {
                "allies": ["Russia", "Hezbollah", "Syria", "Houthis"],
                "adversaries": ["Israel", "United States", "Saudi Arabia"],
                "conflicts": ["Iran-Israel Conflict", "Iran-US Tensions"],
                "last_updated": datetime.now().isoformat()
            },
            "Israel": {
                "allies": ["United States", "United Kingdom"],
                "adversaries": ["Iran", "Hezbollah", "Hamas", "Syria"],
                "conflicts": ["Israel-Gaza War", "Israel-Hezbollah Conflict"],
                "last_updated": datetime.now().isoformat()
            },
            "Russia": {
                "allies": ["Iran", "China", "Syria", "North Korea"],
                "adversaries": ["Ukraine", "NATO", "United States"],
                "conflicts": ["Ukraine War"],
                "last_updated": datetime.now().isoformat()
            },
            "United States": {
                "allies": ["Israel", "United Kingdom", "NATO", "Ukraine"],
                "adversaries": ["Iran", "North Korea", "Russia"],
                "conflicts": ["US-Iran Tensions"],
                "last_updated": datetime.now().isoformat()
            },
            "China": {
                "allies": ["Russia", "North Korea"],
                "adversaries": ["Taiwan", "United States"],
                "conflicts": ["Taiwan Strait Tensions"],
                "last_updated": datetime.now().isoformat()
            },
            "Ukraine": {
                "allies": ["United States", "NATO", "European Union"],
                "adversaries": ["Russia"],
                "conflicts": ["Ukraine War"],
                "last_updated": datetime.now().isoformat()
            },
            "Hezbollah": {
                "allies": ["Iran", "Syria"],
                "adversaries": ["Israel", "United States"],
                "conflicts": ["Israel-Hezbollah Conflict"],
                "last_updated": datetime.now().isoformat()
            },
            "NATO": {
                "allies": ["United States", "United Kingdom", "Ukraine"],
                "adversaries": ["Russia"],
                "conflicts": [],
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def _save_graph(self):
        """Persist graph to disk"""
        with open(self.graph_file, 'w') as f:
            json.dump(self.graph, f, indent=2)
    
    def is_similar(self, a: str, b: str) -> bool:
        """Check if two strings are similar (>80%)"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.8
    
    def update_from_events(self, events: List[Dict]) -> Dict[str, List[str]]:
        """Extract and update relationships from events"""
        new_relationships = {
            "allies": [],
            "adversaries": []
        }
        
        for event in events:
            text = (event.get("title", "") + " " + event.get("summary", "")).lower()
            
            actor_pairs = [
                ("Iran", "Russia"), ("Iran", "Hezbollah"), ("Iran", "Syria"),
                ("US", "Israel"), ("US", "NATO"), ("Russia", "China"),
                ("Israel", "Hezbollah"), ("Iran", "Israel"), ("US", "Iran"),
                ("Russia", "Ukraine"), ("China", "Taiwan")
            ]
            
            for actor1, actor2 in actor_pairs:
                if actor1.lower() in text and actor2.lower() in text:
                    if actor1 not in self.graph:
                        self.graph[actor1] = {"allies": [], "adversaries": [], "conflicts": []}
                    if actor2 not in self.graph:
                        self.graph[actor2] = {"allies": [], "adversaries": [], "conflicts": []}
                    
                    for kw in self.relationship_keywords["adversaries"]:
                        if kw in text:
                            if actor2 not in self.graph[actor1].get("adversaries", []):
                                self.graph[actor1].setdefault("adversaries", []).append(actor2)
                                new_relationships["adversaries"].append(f"{actor1} -> adversary -> {actor2}")
                            if actor1 not in self.graph[actor2].get("adversaries", []):
                                self.graph[actor2].setdefault("adversaries", []).append(actor1)
                            break
                    
                    for kw in self.relationship_keywords["allies"]:
                        if kw in text:
                            if actor2 not in self.graph[actor1].get("allies", []):
                                self.graph[actor1].setdefault("allies", []).append(actor2)
                                new_relationships["allies"].append(f"{actor1} -> ally -> {actor2}")
                            if actor1 not in self.graph[actor2].get("allies", []):
                                self.graph[actor2].setdefault("allies", []).append(actor1)
                            break
        
        for actor in self.graph:
            self.graph[actor]["last_updated"] = datetime.now().isoformat()
        
        self._save_graph()
        
        return new_relationships
    
    def get_context_for(self, countries: List[str]) -> str:
        """Get relationship context for analysis"""
        context_parts = []
        
        for country in countries:
            if country in self.graph:
                data = self.graph[country]
                allies = data.get("allies", [])
                adversaries = data.get("adversaries", [])
                conflicts = data.get("conflicts", [])
                
                parts = []
                if allies:
                    parts.append(f"Allies: {', '.join(allies)}")
                if adversaries:
                    parts.append(f"Adversaries: {', '.join(adversaries)}")
                if conflicts:
                    parts.append(f"Active conflicts: {', '.join(conflicts)}")
                
                if parts:
                    context_parts.append(f"{country}: {'; '.join(parts)}")
        
        return "\n".join(context_parts) if context_parts else "No relationship data available."
    
    def deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        """Remove duplicate events based on title similarity"""
        if not events:
            return []
        
        deduplicated = []
        seen_titles = []
        
        for event in events:
            title = event.get("title", event.get("event_title", ""))
            
            is_duplicate = False
            for seen in seen_titles:
                if self.is_similar(title, seen):
                    is_duplicate = True
                    for existing in deduplicated:
                        existing_title = existing.get("title", existing.get("event_title", ""))
                        if self.is_similar(existing_title, seen):
                            if event.get("severity", 0) > existing.get("severity", 0):
                                existing["title"] = title
                                existing["severity"] = event.get("severity", 0)
                            break
                    break
            
            if not is_duplicate:
                deduplicated.append(event)
                seen_titles.append(title)
        
        return deduplicated


def get_memory_graph() -> GeopoliticalMemoryGraph:
    """Get singleton instance"""
    if not hasattr(get_memory_graph, "_instance"):
        get_memory_graph._instance = GeopoliticalMemoryGraph()
    return get_memory_graph._instance


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for pipeline"""
    graph = get_memory_graph()
    
    events = state.get("events", [])
    if events:
        relationships = graph.update_from_events(events)
        if relationships.get("allies") or relationships.get("adversaries"):
            logger.info(f"Updated relationships: {len(relationships['allies'])} allies, {len(relationships['adversaries'])} adversaries")
    
    countries = set()
    for e in events:
        for c in e.get("countries", e.get("countries_involved", [])):
            countries.add(c)
    
    if countries:
        context = graph.get_context_for(list(countries))
        state["actor_relationships"] = context
    
    state["deduplicated_events"] = graph.deduplicate_events(events)
    
    return state
