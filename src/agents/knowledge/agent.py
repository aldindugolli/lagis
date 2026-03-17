# LAGIS - Knowledge Agent
# Builds and queries the geopolitical knowledge base

import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.core.llm.engine import get_llm
from src.core.config import KNOWLEDGE_DB_PATH

logger = logging.getLogger("LAGIS.Knowledge")


class KnowledgeAgent:
    """Manages geopolitical knowledge base with embeddings"""
    
    def __init__(self):
        self.db_path = KNOWLEDGE_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.llm = get_llm()
        self._init_db()
        logger.info(f"Knowledge base initialized at {self.db_path}")
    
    def _init_db(self):
        """Initialize knowledge database schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT UNIQUE,
                title TEXT,
                source TEXT,
                content TEXT,
                embedding BLOB,
                keywords TEXT,
                entities TEXT,
                archived_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                entity_type TEXT,
                mentions INTEGER DEFAULT 1,
                last_seen TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity1 TEXT,
                entity2 TEXT,
                relation_type TEXT,
                context TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_knowledge_archived_date ON knowledge(archived_date)
        """)
        
        conn.commit()
        conn.close()
    
    def _compute_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Compute cosine similarity between embeddings"""
        dot = sum(a * b for a, b in zip(emb1, emb2))
        norm1 = sum(a * a for a in emb1) ** 0.5
        norm2 = sum(b * b for b in emb2) ** 0.5
        return dot / (norm1 * norm2) if norm1 and norm2 else 0
    
    def store_article(self, article: Dict[str, Any]) -> bool:
        """Store article with embedding in knowledge base"""
        article_id = article.get('id') or article.get('article_id')
        if not article_id:
            return False
        
        content = article.get('content', '')[:2000]
        embedding = None
        
        try:
            emb = self.llm.embed(content)
            embedding = json.dumps(emb)
        except Exception as e:
            logger.warning(f"Failed to generate embedding: {e}")
            return False
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO knowledge 
                (article_id, title, source, content, embedding, archived_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                article_id,
                article.get('title'),
                article.get('source'),
                article.get('content'),
                embedding,
                datetime.now().strftime("%Y-%m-%d")
            ))
            conn.commit()
            stored = cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to store article: {e}")
            stored = False
        finally:
            conn.close()
        
        return stored
    
    def store_articles_batch(self, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """Store multiple articles"""
        stored = 0
        skipped = 0
        
        for article in articles:
            if self.store_article(article):
                stored += 1
            else:
                skipped += 1
        
        logger.info(f"Knowledge: stored {stored}, skipped {skipped}")
        return {"stored": stored, "skipped": skipped}
    
    def search_by_similarity(self, query: str, limit: int = 5) -> List[Dict]:
        """Semantic search in knowledge base"""
        try:
            query_emb = self.llm.embed(query)
        except Exception:
            logger.warning("Failed to embed query")
            return []
        
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT article_id, title, source, content, embedding FROM knowledge")
        results = []
        
        for row in cursor.fetchall():
            try:
                stored_emb = json.loads(row['embedding'])
                similarity = self._compute_similarity(query_emb, stored_emb)
                results.append({
                    'article_id': row['article_id'],
                    'title': row['title'],
                    'source': row['source'],
                    'content': row['content'],
                    'similarity': similarity
                })
            except Exception:
                continue
        
        conn.close()
        
        results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        return results[:limit]
    
    def get_historical_context(self, topic: str, days: int = 30) -> List[Dict]:
        """Get historical articles related to topic"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM knowledge
            WHERE content LIKE ? OR title LIKE ?
            AND archived_date >= ?
            ORDER BY archived_date DESC
        """, (f"%{topic}%", f"%{topic}%", 
              (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_entity_counts(self, days: int = 30) -> List[Dict]:
        """Get most mentioned entities from recent period"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, entity_type, mentions, last_seen
            FROM entities
            WHERE last_seen >= ?
            ORDER BY mentions DESC
            LIMIT 20
        """, ((datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM knowledge")
        total_articles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT archived_date) FROM knowledge")
        total_days = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM entities")
        total_entities = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_articles": total_articles,
            "total_days": total_days,
            "total_entities": total_entities
        }
    
    def store_events_batch(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Store events with embeddings - more targeted than articles"""
        stored = 0
        skipped = 0
        
        for event in events:
            event_id = f"event_{event.get('event_title', '')[:30]}_{event.get('created_at', '')[:10]}"
            
            content = f"{event.get('event_title', '')} {event.get('summary', '')}"[:1500]
            embedding = None
            
            try:
                emb = self.llm.embed(content)
                embedding = json.dumps(emb)
            except Exception:
                pass
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO knowledge 
                    (article_id, title, content, embedding, archived_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    event_id,
                    event.get('event_title', ''),
                    content,
                    embedding,
                    datetime.now().strftime("%Y-%m-%d")
                ))
                conn.commit()
                if cursor.rowcount > 0:
                    stored += 1
                else:
                    skipped += 1
            except Exception:
                skipped += 1
            finally:
                conn.close()
        
        logger.info(f"Knowledge (events): stored {stored}, skipped {skipped}")
        return {"stored": stored, "skipped": skipped}
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge processing - embed events if available, else articles"""
        events = state.get("events", [])
        articles = state.get("articles", [])
        
        if events:
            result = self.store_events_batch(events)
            state["knowledge_result"] = result
            state["status"] = "knowledge_built"
            logger.info(f"Knowledge: embedded {result['stored']} events")
        elif articles:
            result = self.store_articles_batch(articles)
            state["knowledge_result"] = result
            state["status"] = "knowledge_built"
            logger.info(f"Knowledge: embedded {result['stored']} articles")
        else:
            logger.warning("No articles or events to process for knowledge base")
            state["knowledge_result"] = {"stored": 0}
        
        return state
    
    def retrieve_context_for_brief(self, query: str, days: int = 30) -> str:
        """Retrieve historical context for brief generation"""
        recent_articles = self.get_historical_context(query, days)
        
        if not recent_articles:
            return "No historical context available."
        
        context_parts = ["HISTORICAL CONTEXT (Past 30 days):"]
        for i, article in enumerate(recent_articles[:5], 1):
            date = article.get('archived_date', 'Unknown')
            title = article.get('title', 'Untitled')
            content = article.get('content', '')[:300]
            context_parts.append(f"\n{i}. [{date}] {title}")
            context_parts.append(f"   {content}...")
        
        return "\n".join(context_parts)


_knowledge_agent: Optional[KnowledgeAgent] = None


def get_knowledge_agent() -> KnowledgeAgent:
    global _knowledge_agent
    if _knowledge_agent is None:
        _knowledge_agent = KnowledgeAgent()
    return _knowledge_agent


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = get_knowledge_agent()
    return agent.run(state)
