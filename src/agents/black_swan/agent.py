# LAGIS - Black Swan Anomaly Detection
# Identifies rare, low-frequency, high-impact geopolitical anomalies
# NO LLM calls - Pure rule-based detection

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from src.core.config import DATA_DIR

logger = logging.getLogger("LAGIS.BlackSwan")

SIGNALS_FILE = DATA_DIR / "signals_history.json"
GRAPH_FILE = DATA_DIR / "memory_graph.json"
ANOMALY_FILE = DATA_DIR / "anomaly_history.json"

SIGNAL_CATEGORIES = {
    "military": ["troops", "missile", "drill", "exercise", "deployment", "military", "army"],
    "conflict": ["attack", "airstrike", "clash", "offensive", "strike", "war", "invasion"],
    "economic": ["sanctions", "tariff", "oil", "gas", "trade", "embargo", "economic"],
    "political": ["warning", "threat", "tensions", "ultimatum", "diplomatic", "negotiations"],
    "nuclear": ["nuclear", "uranium", "enrichment", "atomic", "radiation", "warhead"]
}

COUNTRIES = ["iran", "israel", "china", "russia", "taiwan", "ukraine", "usa", "north korea", "saudi arabia", "syria"]

HISTORICAL_BASELINES = {
    "nuclear": 3,
    "military": 10,
    "conflict": 8,
    "economic": 5,
    "political": 7
}

ANOMALY_THRESHOLDS = {
    "signal_spike_ratio": 2.5,
    "weak_edge_weight": 0.3,
    "edge_surge_delta": 0.2,
    "cascade_min_categories": 3,
    "silence_days": 2
}


class BlackSwanDetector:
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.signals_file = SIGNALS_FILE
        self.graph_file = GRAPH_FILE
        self.anomaly_file = ANOMALY_FILE
        self.anomaly_history = self._load_anomaly_history()
    
    def _load_anomaly_history(self) -> Dict:
        if self.anomaly_file.exists():
            try:
                with open(self.anomaly_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"alerts": [], "last_updated": datetime.now().isoformat()[:10]}
    
    def _save_anomaly_history(self):
        self.anomaly_history["last_updated"] = datetime.now().isoformat()[:10]
        with open(self.anomaly_file, 'w') as f:
            json.dump(self.anomaly_history, f, indent=2)
    
    def _load_signals(self) -> Dict:
        if self.signals_file.exists():
            try:
                with open(self.signals_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"categories": {}, "countries": {}, "timestamp": []}
    
    def _load_graph(self) -> Optional[Dict]:
        if self.graph_file.exists():
            try:
                with open(self.graph_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def _detect_signal_anomaly(self, category: str, current: int, history: List[int]) -> Optional[Dict]:
        if not history or len(history) < 3:
            return None
        
        avg = sum(history) / len(history)
        if avg == 0:
            if current > 5:
                return self._create_anomaly(
                    "Signal Anomaly",
                    f"Unusual spike in {category} signals: {current} vs historical avg of {avg:.1f}",
                    ["System"],
                    rarity=4,
                    magnitude=min(5, current // 3)
                )
            return None
        
        ratio = current / avg
        baseline = HISTORICAL_BASELINES.get(category, 5)
        
        if ratio >= ANOMALY_THRESHOLDS["signal_spike_ratio"] and current > baseline:
            return self._create_anomaly(
                "Signal Anomaly",
                f"Rare spike in {category} signals: {current} ({ratio:.1f}x historical average)",
                self._get_category_actors(category),
                rarity=4,
                magnitude=min(5, int(ratio))
            )
        
        return None
    
    def _get_category_actors(self, category: str) -> List[str]:
        category_map = {
            "nuclear": ["Iran", "North Korea"],
            "military": ["Russia", "China", "US"],
            "conflict": ["Israel", "Iran", "Ukraine"],
            "economic": ["Russia", "Iran", "China"],
            "political": []
        }
        return category_map.get(category, [])
    
    def _detect_rare_actor_combinations(self, events: List[Dict], graph: Dict) -> List[Dict]:
        anomalies = []
        
        actor_pairs_detected = set()
        for event in events[:10]:
            title = event.get("title", "").lower()
            countries = event.get("countries", [])
            
            if not countries or len(countries) < 2:
                continue
            
            for i, actor1 in enumerate(countries):
                for actor2 in countries[i+1:]:
                    pair = tuple(sorted([actor1, actor2]))
                    if pair in actor_pairs_detected:
                        continue
                    actor_pairs_detected.add(pair)
                    
                    edge = self._find_edge(graph, actor1, actor2)
                    if edge:
                        weight = edge.get("weight", 0.5)
                        if weight < ANOMALY_THRESHOLDS["weak_edge_weight"]:
                            anomalies.append(self._create_anomaly(
                                "Rare Actor Combination",
                                f"Unusual actor pairing: {actor1} + {actor2} (relationship weight: {weight:.2f})",
                                [actor1, actor2],
                                rarity=5,
                                magnitude=3,
                                cross_confirm=1
                            ))
        
        return anomalies[:2]
    
    def _find_edge(self, graph: Optional[Dict], from_actor: str, to_actor: str) -> Optional[Dict]:
        if not graph or "edges" not in graph:
            return None
        
        for edge in graph["edges"]:
            if (edge["from"] == from_actor and edge["to"] == to_actor) or \
               (edge["from"] == to_actor and edge["to"] == from_actor):
                return edge
        return None
    
    def _detect_cascading_signals(self, category_counts: Dict, history: Dict) -> Optional[Dict]:
        if not history or "categories" not in history:
            return None
        
        spiking_categories = []
        for cat, current in category_counts.items():
            cat_history = history["categories"].get(cat, [])
            if len(cat_history) >= 3:
                avg = sum(cat_history) / len(cat_history)
                if avg > 0 and current / avg >= 2.0:
                    spiking_categories.append(cat)
        
        if len(spiking_categories) >= ANOMALY_THRESHOLDS["cascade_min_categories"]:
            return self._create_anomaly(
                "Cascading Signals",
                f"Systemic instability: {', '.join(spiking_categories)} signals spiking simultaneously",
                ["System"],
                rarity=5,
                magnitude=5,
                cross_confirm=3
            )
        
        return None
    
    def _detect_edge_surge(self, graph: Dict, events: List[Dict]) -> List[Dict]:
        anomalies = []
        
        if not events:
            return anomalies
        
        recent_actors = set()
        for event in events[:5]:
            recent_actors.update(event.get("countries", []))
        
        if not recent_actors:
            return anomalies
        
        for edge in graph.get("edges", []):
            if edge["from"] in recent_actors or edge["to"] in recent_actors:
                weight = edge.get("weight", 0.5)
                
                if weight >= 0.8 and edge.get("type") == "conflict":
                    anomalies.append(self._create_anomaly(
                        "Edge Surge",
                        f"Escalation anomaly: {edge['from']} ↔ {edge['to']} conflict intensity at {weight:.0%}",
                        [edge["from"], edge["to"]],
                        rarity=4,
                        magnitude=min(5, int(weight * 5)),
                        cross_confirm=2
                    ))
        
        return anomalies[:1]
    
    def _detect_silence_anomaly(self, history: Dict, current_counts: Dict) -> List[Dict]:
        anomalies = []
        today = datetime.now().date()
        
        if not history or "countries" not in history:
            return anomalies
        
        for country in COUNTRIES:
            country_history = history["countries"].get(country, [])
            if len(country_history) < 7:
                continue
            
            recent_avg = sum(country_history[-3:]) / 3 if len(country_history) >= 3 else 0
            current = current_counts.get(country, 0)
            
            baseline = sum(country_history) / len(country_history)
            
            if baseline > 5 and recent_avg > 5 and current == 0:
                anomalies.append(self._create_anomaly(
                    "Silence Anomaly",
                    f"Anomalous silence: {country.title()} suddenly inactive despite {baseline:.1f} avg signals",
                    [country.title()],
                    rarity=5,
                    magnitude=4,
                    cross_confirm=2
                ))
        
        return anomalies[:1]
    
    def _detect_regional_concentration(self, events: List[Dict]) -> Optional[Dict]:
        country_counts = defaultdict(int)
        for event in events:
            for country in event.get("countries", []):
                country_counts[country] += 1
        
        if not country_counts:
            return None
        
        max_country, max_count = max(country_counts.items(), key=lambda x: x[1])
        total = sum(country_counts.values())
        
        if total >= 5 and max_count / total >= 0.6:
            return self._create_anomaly(
                "Regional Concentration",
                f"Dangerous focus: {max_count}/{total} events in {max_country} region",
                [max_country],
                rarity=3,
                magnitude=min(5, max_count // 2),
                cross_confirm=1
            )
        
        return None
    
    def _create_anomaly(self, anomaly_type: str, description: str, actors: List[str],
                       rarity: int, magnitude: int, cross_confirm: int = 1) -> Dict:
        score = rarity + magnitude + cross_confirm
        
        if score >= 10:
            risk = "HIGH"
        elif score >= 6:
            risk = "MEDIUM"
        else:
            risk = "LOW"
        
        implications = {
            "Signal Anomaly": "Potential escalation involving strategic/tactical shift",
            "Rare Actor Combination": "Unusual alliance or conflict pattern emerging",
            "Cascading Signals": "Systemic instability - multiple stress points activated",
            "Edge Surge": "Rapid escalation in bilateral tensions",
            "Silence Anomaly": "Possible information suppression or pre-event calm",
            "Regional Concentration": "Escalation concentrated in specific theater"
        }
        
        return {
            "type": anomaly_type,
            "description": description,
            "risk": risk,
            "score": score,
            "actors": actors,
            "implication": implications.get(anomaly_type, "Monitor for escalation"),
            "timestamp": datetime.now().isoformat()[:10]
        }
    
    def _score_anomaly(self, anomaly: Dict) -> float:
        return anomaly.get("score", 0)
    
    def _should_include_anomaly(self, anomaly: Dict) -> bool:
        if anomaly.get("risk") == "HIGH":
            return True
        if anomaly.get("risk") == "MEDIUM" and anomaly.get("score", 0) >= 7:
            return True
        return False
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            history = self._load_signals()
            graph = self._load_graph()
            events = state.get("deduplicated_events", []) or state.get("events", [])
            signal_counts = state.get("signal_counts", {}).get("categories", {})
            
            if not signal_counts:
                signal_counts = {cat: 0 for cat in SIGNAL_CATEGORIES}
            
            anomalies = []
            
            for cat, current in signal_counts.items():
                cat_history = history.get("categories", {}).get(cat, [])
                anomaly = self._detect_signal_anomaly(cat, current, cat_history)
                if anomaly and self._should_include_anomaly(anomaly):
                    anomalies.append(anomaly)
            
            if graph:
                rare_combos = self._detect_rare_actor_combinations(events, graph)
                for anomaly in rare_combos:
                    if self._should_include_anomaly(anomaly):
                        anomalies.append(anomaly)
                
                edge_surges = self._detect_edge_surge(graph, events)
                for anomaly in edge_surges:
                    if self._should_include_anomaly(anomaly):
                        anomalies.append(anomaly)
            
            cascading = self._detect_cascading_signals(signal_counts, history)
            if cascading and self._should_include_anomaly(cascading):
                anomalies.append(cascading)
            
            country_counts = signal_counts.get("countries", {}) if isinstance(signal_counts, dict) else {}
            silence = self._detect_silence_anomaly(history, country_counts)
            for anomaly in silence:
                if self._should_include_anomaly(anomaly):
                    anomalies.append(anomaly)
            
            concentration = self._detect_regional_concentration(events)
            if concentration and self._should_include_anomaly(concentration):
                anomalies.append(concentration)
            
            anomalies.sort(key=self._score_anomaly, reverse=True)
            
            final_alerts = anomalies[:2]
            
            if final_alerts:
                self.anomaly_history["alerts"].extend(final_alerts)
                self._save_anomaly_history()
                
                logger.info(f"Black Swan: Detected {len(final_alerts)} anomalies")
                for a in final_alerts:
                    logger.info(f"  [{a['risk']}] {a['type']}: {a['description'][:50]}")
            
            state["black_swan_alerts"] = final_alerts
            
        except Exception as e:
            logger.error(f"Error in black_swan: {e}")
            state["black_swan_alerts"] = []
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    detector = BlackSwanDetector()
    return detector.run(state)
