# LAGIS - Trend Tracking Agent
# Detects long-term directional changes using historical comparison

import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.core.llm.engine import get_llm
from src.core.memory.memory import get_memory
from src.core.world_model.engine import get_world_model
from src.orchestration.utils import skip_stage

logger = logging.getLogger("LAGIS.Trends")


class TrendAgent:
    """Detects long-term directional changes"""
    
    def __init__(self):
        self.llm = get_llm()
        self.memory = get_memory()
        self.world_model = get_world_model()
    
    def _get_historical_events(self, topic: str, days: int = 90) -> List[Dict]:
        """Get events from historical period"""
        conn = self.memory.db_path
        import sqlite3
        conn = sqlite3.connect(str(conn))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM events
            WHERE event_title LIKE ? OR summary LIKE ?
            AND created_at >= datetime('now', '-' || ? || ' days')
            ORDER BY created_at DESC
        """, (f"%{topic}%", f"%{topic}%", days))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def _calculate_trend(self, historical_data: List[Dict], current_data: List[Dict]) -> Dict[str, Any]:
        """Calculate trend direction and velocity"""
        current_severity = sum(e.get('severity_score', 0) for e in current_data) / max(len(current_data), 1)
        historical_severity = sum(e.get('severity_score', 0) for e in historical_data) / max(len(historical_data), 1)
        
        change = current_severity - historical_severity
        
        if change > 1.0:
            direction = "escalating"
            trend_emoji = "[ESCALATING]"
        elif change < -1.0:
            direction = "de-escalating"
            trend_emoji = "[DEESCALATING]"
        else:
            direction = "stable"
            trend_emoji = "[STABLE]"
        
        return {
            "direction": direction,
            "change_magnitude": abs(change),
            "current_avg_severity": current_severity,
            "historical_avg_severity": historical_severity,
            "event_count_change": len(current_data) - len(historical_data),
            "emoji": trend_emoji
        }
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trend analysis"""
        events = state.get("events", [])
        risk_scores = state.get("risk_scores", {})
        
        if not events:
            logger.warning("No events for trend analysis")
            skip_stage(state, "no_events")
            state["trend_analysis"] = {"trends": []}
            return state
        
        topics = ["Russia", "Ukraine", "Iran", "China", "NATO", "Kosovo", "Middle East", "Europe"]
        
        trends = []
        
        for topic in topics:
            recent = self._get_historical_events(topic, days=30)
            older = self._get_historical_events(topic, days=90)
            older = [e for e in older if e not in recent]
            
            if recent or older:
                trend = self._calculate_trend(older[:10], recent[:10])
                if abs(trend["change_magnitude"]) > 0.5 or trend["event_count_change"] != 0:
                    trends.append({
                        "topic": topic,
                        **trend
                    })
        
        state["trend_analysis"] = {
            "trends": trends,
            "analyzed_at": datetime.now().isoformat()
        }
        state["status"] = "trends_analyzed"
        
        for t in trends:
            logger.info(f"  {t['emoji']} {t['topic']}: {t['direction']} (change: {t['change_magnitude']:.1f})")
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = TrendAgent()
    return agent.run(state)
