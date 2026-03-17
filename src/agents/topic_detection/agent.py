# LAGIS - Topic Detection Agent
# Groups events into geopolitical topics/narratives

import json
import logging
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime

from src.core.llm.engine import get_llm
from src.orchestration.utils import add_llm_call, skip_stage
from src.orchestration.utils import add_llm_call

logger = logging.getLogger("LAGIS.TopicDetection")


TOPIC_KEYWORDS = {
    "iran_nuclear": ["iran", "nuclear", "uranium", "enrichment", "iaea", "tehran", "khamenei"],
    "ukraine_war": ["ukraine", "russia", "kremlin", "kyiv", "moscow", "putin", "invasion", "frontline"],
    "china_taiwan": ["china", "taiwan", "beijing", "xi", "cross-strait", "military drills"],
    "red_sea": ["red sea", "houthi", "yemen", "shipping", "suez", "maritime", "cargo ship"],
    "balkan_security": ["kosovo", "serbia", "balkans", "pristina", "belgrade", "nato expansion"],
    "nato_europe": ["nato", "alliance", "europe", "defense", "stockholm", "summit"],
    "middle_east": ["israel", "gaza", "hamas", "palestine", "netanyahu", "ceasefire"],
    "us_china": ["united states", "china", "washington", "beijing", "trade war", "tariff"],
    "arctic": ["arctic", "north pole", "icebreaker", "russia", "resources"],
    "africa": ["africa", "coup", "sahel", "mali", "niger", "military"]
}


class TopicDetectionAgent:
    """Groups events into geopolitical topics"""
    
    def __init__(self):
        self.llm = get_llm()
    
    def _classify_event(self, event: Dict[str, Any]) -> List[str]:
        """Classify event into topics based on keywords"""
        text = (event.get("event_title", "") + " " + event.get("summary", "")).lower()
        
        topics = []
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                topics.append(topic)
        
        if not topics:
            topics = ["general"]
        
        return topics
    
    def _detect_topics_llm(self, events: List[Dict]) -> List[str]:
        """Use LLM to detect more nuanced topics"""
        events_text = "\n".join([
            f"- {e.get('event_title', '')}" for e in events[:10]
        ])
        
        prompt = f"""Identify the main geopolitical topics/narratives from these events.

EVENTS:
{events_text}

Return a JSON list of topic names (e.g., ["iran_nuclear", "ukraine_war", "red_sea_crisis"]).
Focus on distinct storylines that span multiple events."""
        
        try:
            result = self.llm.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=128,
                system="You identify geopolitical topics and narratives."
            )
            
            topics = json.loads(result) if result.startswith('[') else []
            return topics
        except Exception as e:
            logger.warning(f"LLM topic detection failed: {e}")
            return []
    
    def _group_by_topic(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """Group events by topic"""
        topic_groups = defaultdict(list)
        
        for event in events:
            topics = self._classify_event(event)
            for topic in topics:
                topic_groups[topic].append(event)
        
        return dict(topic_groups)
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute topic detection"""
        events = state.get("events", [])
        
        if not events:
            logger.info("No events for topic detection")
            skip_stage(state, "no_events")
            state["topic_groups"] = {}
            state["detected_topics"] = []
            return state
        
        keyword_topics = self._group_by_topic(events)
        
        llm_topics = self._detect_topics_llm(events)
        
        add_llm_call(state, tokens=100)
        
        all_topics = list(set(list(keyword_topics.keys()) + llm_topics))
        
        topic_summary = []
        for topic, evts in keyword_topics.items():
            severity = sum(e.get('severity_score', 0) for e in evts) / len(evts)
            topic_summary.append({
                "topic": topic,
                "event_count": len(evts),
                "avg_severity": round(severity, 1)
            })
        
        topic_summary.sort(key=lambda x: x["avg_severity"], reverse=True)
        
        state["topic_groups"] = keyword_topics
        state["detected_topics"] = all_topics
        state["topic_summary"] = topic_summary[:10]
        
        logger.info(f"Detected {len(all_topics)} topics: {all_topics}")
        state["status"] = "topics_detected"
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = TopicDetectionAgent()
    return agent.run(state)
