# LAGIS - Topic Discovery Agent
# Detects emerging geopolitical themes over time

import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.core.llm.engine import get_llm
from src.core.memory.memory import get_memory
from src.orchestration.utils import add_llm_call

logger = logging.getLogger("LAGIS.TopicDiscovery")


EMERGING_KEYWORDS = [
    "new", "emerging", "rising", "increasing", "growing",
    "shift", "changing", "evolving", "newly", "novel"
]


class TopicDiscoveryAgent:
    """Detects emerging geopolitical themes"""
    
    def __init__(self):
        self.llm = get_llm()
        self.memory = get_memory()
    
    def _get_past_topics(self, days: int = 30) -> List[str]:
        """Get topics detected in past days"""
        import sqlite3
        conn = sqlite3.connect(str(self.memory.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT topic 
                FROM events 
                WHERE created_at >= datetime('now', '-' || ? || ' days')
            """, (days,))
            results = [row[0] for row in cursor.fetchall()]
        except:
            results = []
        finally:
            conn.close()
        
        return results
    
    def _find_new_keywords(self, articles: List[Dict]) -> List[str]:
        """Find emerging keywords in recent articles"""
        all_text = " ".join([
            a.get("title", "") + " " + a.get("content", "")
            for a in articles
        ]).lower()
        
        emerging = []
        for kw in EMERGING_KEYWORDS:
            if kw in all_text:
                emerging.append(kw)
        
        return emerging
    
    def _analyze_topic_evolution(self, topic: str) -> Dict[str, Any]:
        """Analyze how a topic has evolved"""
        import sqlite3
        conn = sqlite3.connect(str(self.memory.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as count,
                AVG(severity_score) as avg_severity,
                MIN(created_at) as first_seen,
                MAX(created_at) as last_seen
            FROM events
            WHERE event_title LIKE ? OR summary LIKE ?
        """, (f"%{topic}%", f"%{topic}%"))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row["count"]:
            return {
                "topic": topic,
                "event_count": row["count"],
                "avg_severity": round(row["avg_severity"] or 0, 1),
                "first_seen": row["first_seen"],
                "last_seen": row["last_seen"]
            }
        return {}
    
    def _generate_new_themes(self, articles: List[Dict]) -> List[str]:
        """Use LLM to identify potentially new themes"""
        articles_text = "\n".join([
            f"- {a.get('title', '')}" for a in articles[:15]
        ])
        
        prompt = f"""Analyze these recent headlines for EMERGING geopolitical themes or storylines that weren't prominent before.

HEADLINES:
{articles_text}

Identify 3-5 emerging themes. Format as JSON array of theme names (e.g., ["arctic_militarization", "african_coup_trend", "semiconductor_war"])."""
        
        try:
            result = self.llm.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=128,
                system="You identify emerging geopolitical trends and themes."
            )
            
            themes = json.loads(result) if result.startswith('[') else []
            return themes
        except Exception as e:
            logger.warning(f"LLM theme detection failed: {e}")
            return []
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute topic discovery"""
        articles = state.get("articles", [])
        events = state.get("events", [])
        
        if not articles and not events:
            logger.info("No data for topic discovery")
            state["emerging_themes"] = []
            state["topic_evolution"] = []
            return state
        
        emerging_themes = self._generate_new_themes(articles)
        
        add_llm_call(state, tokens=80)
        
        topic_evolution = []
        current_topics = state.get("detected_topics", [])
        
        for topic in current_topics[:5]:
            evolution = self._analyze_topic_evolution(topic)
            if evolution:
                topic_evolution.append(evolution)
        
        topic_evolution = [t for t in topic_evolution if t]  # Filter empty dicts
        
        topic_evolution.sort(key=lambda x: x.get("event_count", 0), reverse=True)
        
        state["emerging_themes"] = emerging_themes
        state["topic_evolution"] = topic_evolution
        
        logger.info(f"Discovered {len(emerging_themes)} emerging themes: {emerging_themes}")
        state["status"] = "topics_discovered"
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = TopicDiscoveryAgent()
    return agent.run(state)
