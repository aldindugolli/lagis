# LAGIS - Signal Spike Detection Agent
# Detects emerging geopolitical crises before they become major events

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from src.core.config import DATA_DIR
from src.orchestration.utils import skip_stage

logger = logging.getLogger("LAGIS.Signals")

SIGNALS_FILE = DATA_DIR / "signals_history.json"

SIGNAL_KEYWORDS = {
    "military_activity": [
        "missile", "airstrike", "bombing", "troops", "military", "invasion",
        "artillery", "drone", "combat", "offensive", "defensive", "attack",
        "naval", "exercises", "mobilization", "deployment", "army"
    ],
    "nuclear_activity": [
        "nuclear", "uranium", "enrichment", "warhead", "ballistic", "icbm",
        "missile test", "nuclear test", "proliferation", "atomic"
    ],
    "economic_warfare": [
        "sanctions", "tariff", "trade restriction", "embargo", "export control",
        "financial restriction", "currency", "economic blockade", "tariffs"
    ],
    "political_instability": [
        "coup", "protest", "uprising", "revolution", "martial law",
        "regime change", "political crisis", "state of emergency", "crackdown"
    ],
    "strategic_infrastructure": [
        "pipeline", "energy supply", "shipping lane", "strait", "port blockade",
        "oil", "gas", "critical minerals", "semiconductor", "rare earth"
    ],
    "diplomatic_tension": [
        "diplomatic", "summit", "negotiations", "treaty", "alliance",
        "expulsion", "diplomatic crisis", "recall ambassador", "ultimatum"
    ],
    "civil_unrest": [
        "protest", "demonstration", "riot", "strike", "unrest",
        "mass protest", "civil disorder", "police crackdown"
    ]
}

SPIKE_MULTIPLIER = 2.0
BASELINE_DAYS = 7


def classify_signal(event: Dict[str, Any]) -> Tuple[str, str]:
    """Classify event into signal category and extract country"""
    text = (event.get("event_title", "") + " " + event.get("summary", "")).lower()
    
    for category, keywords in SIGNAL_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            country = extract_country(event)
            return category, country
    
    return "general", extract_country(event)


def extract_country(event: Dict[str, Any]) -> str:
    """Extract country from event"""
    countries = event.get("countries_involved", [])
    if countries:
        return countries[0]
    
    text = (event.get("event_title", "") + " " + event.get("summary", "")).lower()
    
    country_keywords = {
        "iran": "Iran", "israel": "Israel", "russia": "Russia", "ukraine": "Ukraine",
        "china": "China", "taiwan": "Taiwan", "usa": "USA", "korea": "Korea",
        "nato": "NATO", "syria": "Syria", "yemen": "Yemen", "pakistan": "Pakistan",
        "india": "India", "saudi": "Saudi Arabia", "turkey": "Turkey"
    }
    
    for kw, country in country_keywords.items():
        if kw in text:
            return country
    
    return "Unknown"


def load_signal_history() -> Dict:
    """Load signal history from file"""
    if SIGNALS_FILE.exists():
        try:
            with open(SIGNALS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_signal_history(history: Dict) -> None:
    """Save signal history to file"""
    with open(SIGNALS_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def calculate_baseline(history: Dict, category: str, country: str) -> float:
    """Calculate moving average baseline"""
    if category not in history:
        return 0.0
    
    if country not in history[category]:
        return 0.0
    
    counts = history[category][country]
    if not counts:
        return 0.0
    
    return sum(counts) / len(counts)


def detect_spikes(events: List[Dict], history: Dict) -> List[Dict]:
    """Detect signal spikes"""
    today_counts = defaultdict(lambda: defaultdict(int))
    
    for event in events:
        category, country = classify_signal(event)
        if country and country != "Unknown":
            today_counts[category][country] += 1
    
    spikes = []
    
    for category, countries in today_counts.items():
        for country, count in countries.items():
            baseline = calculate_baseline(history, category, country)
            
            if baseline > 0 and count >= baseline * SPIKE_MULTIPLIER:
                spike_ratio = count / baseline
                priority = calculate_priority(category, count, spike_ratio)
                
                spikes.append({
                    "category": category,
                    "country": country,
                    "today_count": count,
                    "baseline": round(baseline, 1),
                    "spike_ratio": round(spike_ratio, 1),
                    "priority": priority,
                    "detected_at": datetime.now().isoformat()
                })
    
    spikes.sort(key=lambda x: x["priority"], reverse=True)
    return spikes


def calculate_priority(category: str, count: int, ratio: float) -> int:
    """Calculate spike priority score"""
    priority = 0
    
    if category == "military_activity":
        priority += 4
    elif category == "nuclear_activity":
        priority += 5
    elif category == "economic_warfare":
        priority += 2
    elif category == "civil_unrest":
        priority += 2
    elif category == "diplomatic_tension":
        priority += 1
    
    priority += int(ratio)
    priority += min(count, 3)
    
    return priority


def update_signal_history(events: List[Dict], history: Dict) -> Dict:
    """Update signal history with today's events"""
    today_counts = defaultdict(lambda: defaultdict(int))
    
    for event in events:
        category, country = classify_signal(event)
        if country and country != "Unknown":
            today_counts[category][country] += 1
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    for category, countries in today_counts.items():
        if category not in history:
            history[category] = {}
        
        for country, count in countries.items():
            if country not in history[category]:
                history[category][country] = []
            
            history[category][country].append(count)
            
            if len(history[category][country]) > BASELINE_DAYS:
                history[category][country] = history[category][country][-BASELINE_DAYS:]
    
    return history


class SignalDetectionAgent:
    """Detects early warning signal spikes"""
    
    def __init__(self):
        self.history = load_signal_history()
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute signal spike detection"""
        events = state.get("events", [])
        
        if not events:
            logger.info("No events for signal detection")
            skip_stage(state, "no_events")
            state["signal_spikes"] = []
            state["signal_history"] = self.history
            return state
        
        spikes = detect_spikes(events, self.history)
        
        self.history = update_signal_history(events, self.history)
        save_signal_history(self.history)
        
        high_priority = [s for s in spikes if s["priority"] >= 4]
        
        state["signal_spikes"] = spikes
        state["signal_alerts"] = high_priority
        state["signal_history"] = self.history
        
        if spikes:
            logger.info(f"Signal detection: {len(spikes)} spikes, {len(high_priority)} high-priority")
        
        state["status"] = "signals_detected"
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = SignalDetectionAgent()
    return agent.run(state)
