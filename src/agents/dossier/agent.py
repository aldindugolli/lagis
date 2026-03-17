# LAGIS - Dossier Builder Agent
# Creates long-term intelligence dossiers for countries and topics

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.llm.engine import get_llm
from src.core.memory.memory import get_memory
from src.core.config import DATA_DIR
from src.orchestration.utils import add_llm_call

logger = logging.getLogger("LAGIS.Dossier")


DOSSIER_SCHEMA = {
    "country": {
        "government_system": "string",
        "leader": "string",
        "military_doctrine": "string",
        "alliances": [],
        "economic_dependencies": [],
        "strategic_objectives": [],
        "historical_conflicts": [],
        "current_risk_level": 0,
        "last_updated": "timestamp"
    },
    "topic": {
        "description": "string",
        "key_actors": [],
        "timeline": [],
        "momentum": "string",
        "risk_trajectory": "string",
        "last_updated": "timestamp"
    }
}


class DossierBuilderAgent:
    """Builds and maintains intelligence dossiers"""
    
    def __init__(self):
        self.llm = get_llm()
        self.memory = get_memory()
        self.dossier_dir = DATA_DIR / "dossiers"
        self.dossier_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_country_events(self, country: str, days: int = 90) -> List[Dict]:
        """Get recent events involving a country"""
        import sqlite3
        conn = sqlite3.connect(str(self.memory.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM events
            WHERE countries LIKE ?
            AND created_at >= datetime('now', '-' || ? || ' days')
            ORDER BY severity_score DESC
        """, (f"%{country}%", days))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def _get_country_risk(self, country: str) -> Optional[Dict]:
        """Get latest risk assessment for country"""
        import sqlite3
        conn = sqlite3.connect(str(self.memory.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM risk_scores
            WHERE country = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (country,))
        
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def _get_topic_events(self, topic: str, days: int = 90) -> List[Dict]:
        """Get recent events for a topic"""
        import sqlite3
        conn = sqlite3.connect(str(self.memory.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM events
            WHERE event_title LIKE ? OR summary LIKE ?
            AND created_at >= datetime('now', '-' || ? || ' days')
            ORDER BY severity_score DESC
        """, (f"%{topic}%", f"%{topic}%", days))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def _generate_country_dossier(self, country: str, events: List[Dict]) -> Dict[str, Any]:
        """Generate dossier for a country using LLM"""
        if not events:
            return {"error": "No events for dossier"}
        
        events_text = "\n".join([
            f"[{e.get('created_at', '')[:10]}] ({e.get('severity_score', 0)}) {e.get('event_title', '')}"
            for e in events[:20]
        ])
        
        risk = self._get_country_risk(country)
        
        prompt = f"""Create a concise intelligence dossier for {country.upper()}.

RECENT EVENTS (90 days):
{events_text}

CURRENT RISK: {risk.get('overall_risk_score', 'N/A')}/10 if available

Provide a JSON object with:
{{
    "government_system": "brief description",
    "key_leader": "current leader(s)",
    "military_doctrine": "defensive/offensive posture",
    "major_alliances": ["NATO", "EU", etc],
    "strategic_objectives": ["3-4 main goals"],
    "recent_conflicts": ["list of recent conflicts"],
    "risk_factors": ["key instability drivers"]
}}

Keep each field brief (1-2 sentences or 3-4 items max)."""
        
        try:
            result = self.llm.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=512,
                system="You create concise intelligence dossiers."
            )
            
            dossier = json.loads(result) if result.startswith('{') else {}
            dossier["current_risk"] = risk.get('overall_risk_score') if risk else None
            dossier["last_updated"] = datetime.now().isoformat()
            dossier["event_count_90d"] = len(events)
            
            return dossier
        except Exception as e:
            logger.warning(f"Dossier generation failed: {e}")
            return {"error": str(e)}
    
    def _generate_topic_dossier(self, topic: str, events: List[Dict]) -> Dict[str, Any]:
        """Generate dossier for a topic"""
        if not events:
            return {"error": "No events for dossier"}
        
        events_text = "\n".join([
            f"- {e.get('event_title', '')}" for e in events[:15]
        ])
        
        severity_trend = "increasing" if events[0].get("severity_score", 0) > 5 else "stable"
        
        prompt = f"""Create a concise intelligence dossier for topic: {topic}.

RECENT EVENTS:
{events_text}

Provide JSON:
{{
    "description": "1-2 sentence summary",
    "key_actors": ["list of countries/groups involved"],
    "timeline_summary": "brief evolution of this topic",
    "momentum": "escalating/stable/de-escalating",
    "risk_assessment": "brief risk level and drivers"
}}"""
        
        try:
            result = self.llm.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=256,
                system="You create concise topic dossiers."
            )
            
            dossier = json.loads(result) if result.startswith('{') else {}
            dossier["last_updated"] = datetime.now().isoformat()
            dossier["event_count"] = len(events)
            
            return dossier
        except Exception as e:
            logger.warning(f"Topic dossier failed: {e}")
            return {"error": str(e)}
    
    def _save_dossier(self, dossier_type: str, name: str, data: Dict[str, Any]) -> None:
        """Save dossier to file"""
        filename = self.dossier_dir / f"{dossier_type}_{name.lower().replace(' ', '_')}.json"
        
        existing = {}
        if filename.exists():
            try:
                with open(filename, 'r') as f:
                    existing = json.load(f)
            except:
                pass
        
        existing.update(data)
        
        with open(filename, 'w') as f:
            json.dump(existing, f, indent=2)
        
        logger.info(f"Saved dossier: {filename.name}")
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute dossier building"""
        actors = state.get("actors", {})
        countries = actors.get("countries", [])
        topic_groups = state.get("topic_groups", {})
        
        if not countries and not topic_groups:
            logger.info("No actors/topics for dossier building")
            state["dossiers_created"] = []
            return state
        
        dossiers_created = []
        
        for country in countries[:5]:
            events = self._get_country_events(country)
            if events:
                dossier = self._generate_country_dossier(country, events)
                self._save_dossier("country", country, dossier)
                dossiers_created.append(f"country:{country}")
        
        for topic in list(topic_groups.keys())[:3]:
            events = self._get_topic_events(topic)
            if events:
                dossier = self._generate_topic_dossier(topic, events)
                self._save_dossier("topic", topic, dossier)
                dossiers_created.append(f"topic:{topic}")
        
        add_llm_call(state, tokens=len(dossiers_created) * 150)
        
        state["dossiers_created"] = dossiers_created
        
        logger.info(f"Created {len(dossiers_created)} dossiers: {dossiers_created}")
        state["status"] = "dossiers_built"
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = DossierBuilderAgent()
    return agent.run(state)
