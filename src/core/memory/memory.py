# LAGIS - Vector Memory System
# Persistent memory from Day 1

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.core.llm.engine import get_llm
from src.core.config import DATABASE_PATH


class Memory:
    """Persistent vector memory for intelligence data"""
    
    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path) if db_path else DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.llm = get_llm()
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                url TEXT,
                source TEXT,
                content TEXT,
                published TEXT,
                content_hash TEXT UNIQUE,
                embedding BLOB,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_title TEXT,
                countries TEXT,
                event_type TEXT,
                strategic_category TEXT,
                severity_score REAL,
                summary TEXT,
                source_url TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                content TEXT,
                confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES events(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country TEXT,
                overall_risk REAL,
                trend TEXT,
                factors TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS briefs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                content TEXT,
                top_events TEXT,
                risks TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def store_article(self, article: Dict[str, Any]) -> None:
        content_hash = hashlib.md5(
            (article.get("title", "") + article.get("url", "")).encode()
        ).hexdigest()
        
        embedding = None
        try:
            emb = self.llm.embed(article.get("content", "")[:1000])
            embedding = json.dumps(emb)
        except:
            pass
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR IGNORE INTO articles 
            (title, url, source, content, published, content_hash, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            article.get("title"),
            article.get("url"),
            article.get("source"),
            article.get("content"),
            article.get("published"),
            content_hash,
            embedding
        ))
        
        conn.commit()
        conn.close()
    
    def store_event(self, event: Dict[str, Any]) -> None:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO events 
            (event_title, countries, event_type, strategic_category, severity_score, summary, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event.get("event_title"),
            json.dumps(event.get("countries_involved", [])),
            event.get("event_type"),
            event.get("strategic_category"),
            event.get("severity_score"),
            event.get("summary"),
            event.get("source_url")
        ))
        
        conn.commit()
        conn.close()
    
    def store_analysis(self, event_id: int, analysis: Dict[str, Any]) -> None:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO analysis (event_id, content, confidence)
            VALUES (?, ?, ?)
        """, (event_id, json.dumps(analysis), analysis.get("confidence_score", 0)))
        
        conn.commit()
        conn.close()
    
    def store_risk_score(self, country: str, risk: Dict[str, Any]) -> None:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO risk_scores (country, overall_risk, trend, factors)
            VALUES (?, ?, ?, ?)
        """, (
            country,
            risk.get("overall_risk_score"),
            risk.get("trend"),
            json.dumps(risk.get("key_factors", []))
        ))
        
        conn.commit()
        conn.close()
    
    def store_brief(self, brief: Dict[str, Any]) -> None:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO briefs (date, content, top_events, risks)
            VALUES (?, ?, ?, ?)
        """, (
            brief.get("date"),
            brief.get("content"),
            json.dumps(brief.get("top_events", [])),
            json.dumps(brief.get("escalation_risks", []))
        ))
        
        conn.commit()
        conn.close()
    
    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM events ORDER BY created_at DESC LIMIT ?
        """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_risk_trend(self, country: str, days: int = 30) -> List[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM risk_scores
            WHERE country = ? AND created_at >= datetime('now', '-' || ? || ' days')
            ORDER BY created_at ASC
        """, (country, days))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_latest_brief(self) -> Optional[Dict]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM briefs ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None


_memory: Optional[Memory] = None


def get_memory() -> Memory:
    global _memory
    if _memory is None:
        _memory = Memory()
    return _memory
