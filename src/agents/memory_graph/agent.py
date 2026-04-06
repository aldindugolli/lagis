# LAGIS - Geopolitical Memory Graph
# Relationship-driven intelligence system
# NO LLM calls - Pure Python dict/JSON

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from src.core.config import DATA_DIR

logger = logging.getLogger("LAGIS.MemoryGraph")

GRAPH_FILE = DATA_DIR / "memory_graph.json"
GEXF_FILE = DATA_DIR / "memory_graph.gexf"

NODE_TYPES = {"country", "organization", "region", "conflict", "resource"}
EDGE_TYPES = {"conflict", "allied_with", "supports", "sanctions", "trades_with", "proxy_of", "nuclear_risk", "energy_dependency"}

RELATIONSHIP_RULES = {
    "conflict": ["attack", "airstrike", "bomb", "strike", "war", "invasion", "clash", "fighting", "hostile", "combat"],
    "supports": ["supports", "backs", "funds", "arms", "trains", "provides", "aid to", "backed by"],
    "allied_with": ["alliance", "ally", "partner", "cooperate", "joint", "treaty"],
    "sanctions": ["sanctions", "embargo", "restrict", "penalty"],
    "trades_with": ["trade", "exports", "imports", "oil export", "energy supply", "shipping"],
    "proxy_of": ["proxy", "surrogate", "via", "through"],
    "nuclear_risk": ["nuclear", "uranium", "enrichment", "atomic", "warhead"],
    "energy_dependency": ["oil", "gas", "energy", "pipeline", "lng", "petroleum"]
}

DEFAULT_NODES = {
    "Iran": {"type": "country", "risk_score": 7},
    "Israel": {"type": "country", "risk_score": 6},
    "United States": {"type": "country", "risk_score": 5},
    "Russia": {"type": "country", "risk_score": 6},
    "China": {"type": "country", "risk_score": 5},
    "Ukraine": {"type": "country", "risk_score": 8},
    "Hezbollah": {"type": "organization", "risk_score": 7},
    "Hamas": {"type": "organization", "risk_score": 7},
    "NATO": {"type": "organization", "risk_score": 5},
    "EU": {"type": "organization", "risk_score": 4}
}

DEFAULT_EDGES = [
    {"from": "Iran", "to": "Hezbollah", "type": "supports", "weight": 0.9},
    {"from": "Iran", "to": "Hamas", "type": "supports", "weight": 0.8},
    {"from": "Israel", "to": "Iran", "type": "conflict", "weight": 0.9},
    {"from": "United States", "to": "Israel", "type": "allied_with", "weight": 0.95},
    {"from": "United States", "to": "NATO", "type": "allied_with", "weight": 0.9},
    {"from": "Russia", "to": "Iran", "type": "allied_with", "weight": 0.7},
    {"from": "Russia", "to": "Ukraine", "type": "conflict", "weight": 1.0},
    {"from": "United States", "to": "Ukraine", "type": "allied_with", "weight": 0.8},
    {"from": "China", "to": "Russia", "type": "allied_with", "weight": 0.6},
    {"from": "Iran", "to": "United States", "type": "conflict", "weight": 0.85},
]


class GeopoliticalMemoryGraph:
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.graph_file = GRAPH_FILE
        self.graph_file.parent.mkdir(parents=True, exist_ok=True)
        self.graph = self._load_graph()
    
    def _load_graph(self) -> Dict:
        if self.graph_file.exists():
            try:
                with open(self.graph_file, 'r') as f:
                    data = json.load(f)
                    if data and "nodes" in data and "edges" in data:
                        return data
            except:
                pass
        return self._create_default_graph()
    
    def _create_default_graph(self) -> Dict:
        graph = {"nodes": {}, "edges": []}
        
        for node_id, node_data in DEFAULT_NODES.items():
            graph["nodes"][node_id] = {
                "type": node_data["type"],
                "risk_score": node_data["risk_score"],
                "last_updated": datetime.now().isoformat()[:10]
            }
        
        for edge in DEFAULT_EDGES:
            graph["edges"].append({
                **edge,
                "first_seen": datetime.now().isoformat()[:10],
                "last_seen": datetime.now().isoformat()[:10],
                "frequency": 1
            })
        
        with open(self.graph_file, 'w') as f:
            json.dump(graph, f, indent=2)
        
        return graph
    
    def _save_graph(self):
        with open(self.graph_file, 'w') as f:
            json.dump(self.graph, f, indent=2)
    
    def _save_gexf(self):
        gexf = ['<?xml version="1.0" encoding="UTF-8"?>']
        gexf.append('<gexf xmlns="http://gexf.net/1.3" version="1.3">')
        gexf.append('  <graph mode="static" defaultedgetype="undirected">')
        gexf.append('    <attributes class="node">')
        gexf.append('      <attribute id="0" title="type" type="string"/>')
        gexf.append('      <attribute id="1" title="risk_score" type="float"/>')
        gexf.append('    </attributes>')
        gexf.append('    <attributes class="edge">')
        gexf.append('      <attribute id="0" title="type" type="string"/>')
        gexf.append('      <attribute id="1" title="weight" type="float"/>')
        gexf.append('    </attributes>')
        gexf.append('    <nodes>')
        for node_id, node_data in self.graph["nodes"].items():
            gexf.append(f'      <node id="{node_id}" label="{node_id}">')
            gexf.append(f'        <attvalue for="0" value="{node_data.get("type", "unknown")}"/>')
            gexf.append(f'        <attvalue for="1" value="{node_data.get("risk_score", 5)}"/>')
            gexf.append('      </node>')
        gexf.append('    </nodes>')
        gexf.append('    <edges>')
        for i, edge in enumerate(self.graph["edges"]):
            gexf.append(f'      <edge id="{i}" source="{edge["from"]}" target="{edge["to"]}">')
            gexf.append(f'        <attvalue for="0" value="{edge.get("type", "unknown")}"/>')
            gexf.append(f'        <attvalue for="1" value="{edge.get("weight", 0.5)}"/>')
            gexf.append('      </edge>')
        gexf.append('    </edges>')
        gexf.append('  </graph>')
        gexf.append('</gexf>')
        
        with open(GEXF_FILE, 'w') as f:
            f.write('\n'.join(gexf))
    
    def _detect_relationship(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for rel_type, keywords in RELATIONSHIP_RULES.items():
            for kw in keywords:
                if kw in text_lower:
                    return rel_type
        return None
    
    def _find_actors(self, text: str) -> List[str]:
        actors = []
        text_lower = text.lower()
        
        actor_keywords = {
            "iran": ["iran", "iranian", "tehran"],
            "israel": ["israel", "israeli", "tel aviv"],
            "united states": ["united states", "usa", "us ", "america", "american", "washington"],
            "russia": ["russia", "russian", "moscow"],
            "china": ["china", "chinese", "beijing"],
            "ukraine": ["ukraine", "ukrainian", "kyiv", "kiev"],
            "hezbollah": ["hezbollah", "hezballah", "hezbullah"],
            "hamas": ["hamas", "palestinian"],
            "nato": ["nato"],
            "saudi arabia": ["saudi", "riyadh"],
            "syria": ["syria", "syrian", "damascus"],
            "north korea": ["north korea", "kim jong", "pyongyang"],
            "taiwan": ["taiwan", "taipei"],
            "eu": ["european union", "eu ", "brussels"],
            "netherlands": ["netherlands", "dutch", "amsterdam", "den haag"]
        }
        
        for actor_name, keywords in actor_keywords.items():
            for kw in keywords:
                if kw in text_lower:
                    if actor_name not in actors:
                        actors.append(actor_name)
                    break
        
        return actors
    
    def _normalize_actor(self, actor: str) -> str:
        normalization = {
            "us": "United States",
            "usa": "United States",
            "america": "United States",
            "american": "United States",
            "iranian": "Iran",
            "iran": "Iran",
            "israeli": "Israel",
            "israel": "Israel",
            "russian": "Russia",
            "russia": "Russia",
            "chinese": "China",
            "china": "China",
            "ukrainian": "Ukraine",
            "ukraine": "Ukraine",
            "nato": "NATO"
        }
        return normalization.get(actor.lower(), actor.title())
    
    def _edge_exists(self, from_actor: str, to_actor: str, rel_type: str) -> Optional[int]:
        for i, edge in enumerate(self.graph["edges"]):
            if (edge["from"] == from_actor and edge["to"] == to_actor and edge["type"] == rel_type) or \
               (edge["from"] == to_actor and edge["to"] == from_actor and edge["type"] == rel_type):
                return i
        return None
    
    def _decay_edges(self):
        today = datetime.now().date()
        for edge in self.graph["edges"]:
            try:
                last_seen = datetime.fromisoformat(edge["last_seen"]).date()
                days_old = (today - last_seen).days
                if days_old > 0:
                    edge["weight"] = max(0.1, edge["weight"] - (days_old * 0.01))
            except:
                pass
    
    def update_from_events(self, events: List[Dict]) -> List[str]:
        self._decay_edges()
        
        new_relationships = []
        today = datetime.now().isoformat()[:10]
        
        for event in events:
            title = event.get("title", "")
            content = event.get("content", "")
            if isinstance(content, dict):
                summary = content.get("summary", "")
            else:
                summary = str(content)[:500]
            text = title + " " + summary
            
            actors = self._find_actors(text)
            rel_type = self._detect_relationship(text)
            
            if len(actors) >= 2 and rel_type:
                for i in range(len(actors)):
                    for j in range(i + 1, len(actors)):
                        from_actor = self._normalize_actor(actors[i])
                        to_actor = self._normalize_actor(actors[j])
                        
                        if from_actor not in self.graph["nodes"]:
                            self.graph["nodes"][from_actor] = {
                                "type": "unknown",
                                "risk_score": 5,
                                "last_updated": today
                            }
                        if to_actor not in self.graph["nodes"]:
                            self.graph["nodes"][to_actor] = {
                                "type": "unknown",
                                "risk_score": 5,
                                "last_updated": today
                            }
                        
                        edge_idx = self._edge_exists(from_actor, to_actor, rel_type)
                        
                        if edge_idx is not None:
                            edge = self.graph["edges"][edge_idx]
                            edge["weight"] = min(1.0, edge["weight"] + 0.1)
                            edge["last_seen"] = today
                            edge["frequency"] = edge.get("frequency", 1) + 1
                        else:
                            self.graph["edges"].append({
                                "from": from_actor,
                                "to": to_actor,
                                "type": rel_type,
                                "weight": 0.5,
                                "first_seen": today,
                                "last_seen": today,
                                "frequency": 1
                            })
                            new_relationships.append(f"{from_actor} --[{rel_type}]--> {to_actor}")
                        
                        self.graph["nodes"][from_actor]["last_updated"] = today
                        self.graph["nodes"][to_actor]["last_updated"] = today
        
        self._save_graph()
        self._save_gexf()
        
        return new_relationships
    
    def get_related_actors(self, actor: str, depth: int = 1) -> Dict[str, List[str]]:
        actor = self._normalize_actor(actor)
        related = {"direct": [], "extended": []}
        
        for edge in self.graph["edges"]:
            if edge["from"] == actor:
                related["direct"].append((edge["to"], edge["type"], edge["weight"]))
            elif edge["to"] == actor:
                related["direct"].append((edge["from"], edge["type"], edge["weight"]))
        
        if depth > 1:
            visited = {actor}
            visited.update(r[0] for r in related["direct"])
            
            for connected, _, _ in related["direct"]:
                if connected not in visited:
                    for edge in self.graph["edges"]:
                        if edge["from"] == connected and edge["to"] not in visited:
                            related["extended"].append((edge["to"], edge["type"], edge["weight"]))
                            visited.add(edge["to"])
                        elif edge["to"] == connected and edge["from"] not in visited:
                            related["extended"].append((edge["from"], edge["type"], edge["weight"]))
                            visited.add(edge["from"])
        
        return related
    
    def get_conflicts(self, actor: str) -> List[Dict]:
        actor = self._normalize_actor(actor)
        conflicts = []
        
        for edge in self.graph["edges"]:
            if edge["type"] == "conflict":
                if edge["from"] == actor:
                    conflicts.append({"actor": edge["to"], "weight": edge["weight"]})
                elif edge["to"] == actor:
                    conflicts.append({"actor": edge["from"], "weight": edge["weight"]})
        
        return sorted(conflicts, key=lambda x: -x["weight"])
    
    def get_allies(self, actor: str) -> List[Dict]:
        actor = self._normalize_actor(actor)
        allies = []
        
        for edge in self.graph["edges"]:
            if edge["type"] in ("allied_with", "supports"):
                if edge["from"] == actor:
                    allies.append({"actor": edge["to"], "weight": edge["weight"], "type": edge["type"]})
                elif edge["to"] == actor:
                    allies.append({"actor": edge["from"], "weight": edge["weight"], "type": edge["type"]})
        
        return sorted(allies, key=lambda x: -x["weight"])
    
    def get_high_risk_connections(self, actor: str) -> List[Dict]:
        actor = self._normalize_actor(actor)
        connections = []
        
        for edge in self.graph["edges"]:
            if edge["from"] == actor or edge["to"] == actor:
                other = edge["to"] if edge["from"] == actor else edge["from"]
                
                if other in self.graph["nodes"]:
                    node = self.graph["nodes"][other]
                    risk = node.get("risk_score", 5)
                    weight = edge["weight"]
                    
                    if risk >= 7 or float(weight) >= 0.7 or edge["type"] in ("conflict", "nuclear_risk"):
                        connections.append({
                            "actor": other,
                            "relationship": edge["type"],
                            "weight": weight,
                            "risk_score": risk
                        })
        
        return sorted(connections, key=lambda x: -(x["risk_score"] + x["weight"] * 5))
    
    def calculate_graph_risk(self, actor: str) -> float:
        actor = self._normalize_actor(actor)
        
        if actor not in self.graph["nodes"]:
            return 5.0
        
        base_risk = self.graph["nodes"][actor].get("risk_score", 5)
        
        conflict_count = 0
        high_weight_edges = 0
        nuclear_connected = False
        
        for edge in self.graph["edges"]:
            if edge["from"] == actor or edge["to"] == actor:
                if edge["type"] == "conflict":
                    conflict_count += 1
                if edge["weight"] >= 0.7:
                    high_weight_edges += 1
                
                other = edge["to"] if edge["from"] == actor else edge["from"]
                if other in self.graph["nodes"]:
                    if self.graph["nodes"][other].get("type") == "nuclear_risk":
                        nuclear_connected = True
        
        risk = base_risk + (conflict_count * 1.5) + (high_weight_edges * 1.0)
        if nuclear_connected:
            risk += 2
        
        return round(min(10, max(0, risk)), 1)
    
    def get_relationship_insights(self, actors: List[str]) -> List[str]:
        insights = []
        actors_normalized = [self._normalize_actor(a) for a in actors]
        
        for actor in actors_normalized:
            if actor not in self.graph["nodes"]:
                continue
            
            allies = self.get_allies(actor)
            strong_allies = [a for a in allies if a["weight"] >= 0.7]
            if strong_allies:
                ally_names = ", ".join([a["actor"] for a in strong_allies[:2]])
                insights.append(f"{actor} maintains strong {strong_allies[0]['type'].replace('_', ' ')} relationship with {ally_names} (weight: {strong_allies[0]['weight']:.1f})")
            
            conflicts = self.get_conflicts(actor)
            high_conflicts = [c for c in conflicts if c["weight"] >= 0.8]
            if high_conflicts:
                conflict_names = ", ".join([c["actor"] for c in high_conflicts[:2]])
                insights.append(f"{actor} has high-intensity conflict with {conflict_names} (weight: {high_conflicts[0]['weight']:.1f})")
            
            related = self.get_related_actors(actor)
            if related["direct"]:
                proxy_relationships = [r for r in related["direct"] if r[1] == "proxy_of" and float(r[2]) >= 0.6]
                if proxy_relationships:
                    insights.append(f"{actor} uses proxy forces for operational flexibility")
        
        return insights[:4]
    
    def deduplicate_events(self, events: List[Dict]) -> List[Dict]:
        if not events:
            return []
        
        deduplicated = []
        seen_titles = []
        
        for event in events:
            title = event.get("title", event.get("event_title", ""))
            
            is_duplicate = False
            for seen in seen_titles:
                if SequenceMatcher(None, title.lower(), seen.lower()).ratio() > 0.8:
                    is_duplicate = True
                    for existing in deduplicated:
                        existing_title = existing.get("title", existing.get("event_title", ""))
                        if SequenceMatcher(None, existing_title.lower(), seen.lower()).ratio() > 0.8:
                            if event.get("severity", 0) > existing.get("severity", 0):
                                existing["title"] = title
                                existing["severity"] = event.get("severity", 0)
                            break
                    break
            
            if not is_duplicate:
                deduplicated.append(event)
                seen_titles.append(title)
        
        return deduplicated
    
    def get_graph_summary(self) -> Dict:
        return {
            "node_count": len(self.graph["nodes"]),
            "edge_count": len(self.graph["edges"]),
            "conflict_edges": len([e for e in self.graph["edges"] if e["type"] == "conflict"]),
            "alliance_edges": len([e for e in self.graph["edges"] if e["type"] in ("allied_with", "supports")]),
            "avg_weight": round(sum(e["weight"] for e in self.graph["edges"]) / len(self.graph["edges"]), 2) if self.graph["edges"] else 0
        }


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    try:
        graph = GeopoliticalMemoryGraph()
        
        events = state.get("events", [])
        
        if events:
            relationships = graph.update_from_events(events)
            if relationships:
                logger.info(f"New relationships: {len(relationships)}")
                for r in relationships[:3]:
                    logger.info(f"  {r}")
            
            state["new_relationships"] = relationships
        
        actors = set()
        for e in events:
            if isinstance(e, dict):
                for c in e.get("countries", []):
                    actors.add(c)
        actors = list(actors)
        
        if actors:
            state["relationship_insights"] = graph.get_relationship_insights(actors)
            state["graph_summary"] = graph.get_graph_summary()
        
        state["deduplicated_events"] = graph.deduplicate_events(events)
        
        state["graph"] = graph
        
        return state
    except Exception as e:
        logger.error(f"Error in memory_graph: {e}", exc_info=True)
        return state
