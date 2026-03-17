# LAGIS - World Model Engine
# Maintains structured representation of global geopolitical state

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.core.config import DATA_DIR
from src.core.llm.engine import get_llm

logger = logging.getLogger("LAGIS.WorldModel")


class WorldModelEngine:
    """Maintains structured world state - countries, alliances, conflicts, economics"""
    
    def __init__(self):
        self.db_path = DATA_DIR / "world_state.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.llm = get_llm()
        self._init_db()
        logger.info(f"World Model initialized at {self.db_path}")
    
    def _init_db(self):
        """Initialize world state database schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS countries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                region TEXT,
                stability_score REAL DEFAULT 5.0,
                economic_health REAL DEFAULT 5.0,
                military_posture TEXT DEFAULT 'normal',
                alliances TEXT,
                conflicts TEXT,
                last_updated TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alliances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                member_countries TEXT,
                purpose TEXT,
                activity_level TEXT DEFAULT 'stable',
                last_updated TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                parties TEXT,
                intensity REAL DEFAULT 0.0,
                status TEXT DEFAULT 'active',
                region TEXT,
                trend TEXT,
                last_updated TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS narratives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                actors TEXT,
                timeline TEXT,
                momentum TEXT,
                risk_trajectory TEXT,
                last_updated TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                forecast_type TEXT,
                subject TEXT,
                prediction TEXT,
                probability REAL,
                timeframe TEXT,
                confidence REAL,
                actual_outcome TEXT,
                accuracy_score REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                findings TEXT,
                sources TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_countries_name ON countries(name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_narratives_name ON narratives(name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_forecasts_subject ON forecasts(subject)
        """)
        
        conn.commit()
        conn.close()
    
    def update_country(self, country: str, updates: Dict[str, Any]) -> None:
        """Update country state"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO countries (name, stability_score, economic_health, military_posture, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                stability_score = COALESCE(?, stability_score),
                economic_health = COALESCE(?, economic_health),
                military_posture = COALESCE(?, military_posture),
                last_updated = ?
        """, (
            country,
            updates.get('stability_score', 5.0),
            updates.get('economic_health', 5.0),
            updates.get('military_posture', 'normal'),
            updates.get('stability_score', 5.0),
            updates.get('economic_health', 5.0),
            updates.get('military_posture', 'normal'),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def update_countries_from_risks(self, risk_scores: Dict[str, Dict]) -> None:
        """Bulk update countries from risk assessment"""
        for country, risk_data in risk_scores.items():
            self.update_country(country, {
                'stability_score': 10 - risk_data.get('overall_risk_score', 5),
                'economic_health': risk_data.get('economic_factors', {}).get('economic_stability', 5),
            })
    
    def get_country(self, country: str) -> Optional[Dict]:
        """Get country state"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM countries WHERE name = ?", (country,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_all_countries(self) -> List[Dict]:
        """Get all countries"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM countries ORDER BY stability_score ASC")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def add_narrative(self, name: str, actors: List[str], description: str = "") -> None:
        """Add or update a geopolitical narrative"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO narratives (name, actors, description, last_updated)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                actors = ?,
                description = ?,
                last_updated = ?
        """, (
            name, json.dumps(actors), description, datetime.now().isoformat(),
            json.dumps(actors), description, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def update_narrative_momentum(self, name: str, momentum: str, trajectory: str) -> None:
        """Update narrative momentum and trajectory"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE narratives SET momentum = ?, risk_trajectory = ?, last_updated = ?
            WHERE name = ?
        """, (momentum, trajectory, datetime.now().isoformat(), name))
        
        conn.commit()
        conn.close()
    
    def get_narratives(self) -> List[Dict]:
        """Get all tracked narratives"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM narratives ORDER BY last_updated DESC")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def add_forecast(self, forecast_type: str, subject: str, prediction: str, 
                    probability: float, timeframe: str, confidence: float) -> int:
        """Add a new forecast"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO forecasts (forecast_type, subject, prediction, probability, timeframe, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (forecast_type, subject, prediction, probability, timeframe, confidence))
        
        forecast_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return forecast_id
    
    def evaluate_forecast(self, forecast_id: int, actual_outcome: str, accuracy: float) -> None:
        """Record actual outcome and accuracy"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE forecasts SET actual_outcome = ?, accuracy_score = ?
            WHERE id = ?
        """, (actual_outcome, accuracy, forecast_id))
        
        conn.commit()
        conn.close()
    
    def get_forecasts(self, subject: str = None) -> List[Dict]:
        """Get forecasts, optionally filtered by subject"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if subject:
            cursor.execute("SELECT * FROM forecasts WHERE subject = ? ORDER BY created_at DESC", (subject,))
        else:
            cursor.execute("SELECT * FROM forecasts ORDER BY created_at DESC LIMIT 50")
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def add_research_task(self, question: str, priority: str = "medium") -> int:
        """Add a research task"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO research_tasks (question, priority)
            VALUES (?, ?)
        """, (question, priority))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return task_id
    
    def complete_research_task(self, task_id: int, findings: str) -> None:
        """Mark research task as complete"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE research_tasks SET status = 'completed', findings = ?, completed_at = ?
            WHERE id = ?
        """, (findings, datetime.now().isoformat(), task_id))
        
        conn.commit()
        conn.close()
    
    def get_pending_research(self) -> List[Dict]:
        """Get pending research tasks"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM research_tasks 
            WHERE status = 'pending' 
            ORDER BY 
                CASE priority 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    ELSE 3 
                END,
                created_at ASC
        """)
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_world_summary(self) -> str:
        """Generate a text summary of current world state"""
        countries = self.get_all_countries()
        narratives = self.get_narratives()
        
        summary_parts = ["WORLD STATE SUMMARY", "=" * 40]
        
        unstable = [c for c in countries if c.get('stability_score', 5) < 4]
        if unstable:
            summary_parts.append("\n[WARNING] UNSTABLE REGIONS:")
            for c in unstable[:5]:
                summary_parts.append(f"  - {c['name']}: Stability {c.get('stability_score', 0):.1f}/10")
        
        if narratives:
            summary_parts.append(f"\n[STATUS] ACTIVE NARRATIVES ({len(narratives)}):")
            for n in narratives[:5]:
                traj = n.get('risk_trajectory', 'unknown')
                summary_parts.append(f"  - {n['name']}: {traj}")
        
        return "\n".join(summary_parts)


_world_model: Optional[WorldModelEngine] = None


def get_world_model() -> WorldModelEngine:
    global _world_model
    if _world_model is None:
        _world_model = WorldModelEngine()
    return _world_model
