# LAGIS - Archive Agent
# Permanently archives scraped articles to JSON

import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from src.core.config import ARCHIVE_DIR

logger = logging.getLogger("LAGIS.Archive")


def generate_article_id(article: Dict[str, str]) -> str:
    """Generate unique hash ID for article"""
    content = f"{article.get('title', '')}:{article.get('url', '')}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


class ArchiveAgent:
    """Archives articles to JSON for permanent storage"""
    
    def __init__(self):
        self.archive_dir = ARCHIVE_DIR
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.processed_ids = self._load_existing_ids()
        logger.info(f"Archive initialized - {len(self.processed_ids)} articles already archived")
    
    def _load_existing_ids(self) -> set:
        """Load all existing article IDs to prevent duplicates"""
        existing = set()
        for json_file in self.archive_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'articles' in data:
                        for article in data['articles']:
                            if 'id' in article:
                                existing.add(article['id'])
            except Exception:
                pass
        return existing
    
    def _get_archive_file(self, date: str = None) -> Path:
        """Get archive file path for given date"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return self.archive_dir / f"articles_{date}.json"
    
    def archive_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Archive list of articles to JSON"""
        today = datetime.now().strftime("%Y-%m-%d")
        archive_file = self._get_archive_file(today)
        
        existing_articles = []
        if archive_file.exists():
            try:
                with open(archive_file, 'r') as f:
                    existing_articles = json.load(f).get('articles', [])
            except Exception:
                pass
        
        new_articles = []
        for article in articles:
            article_id = generate_article_id(article)
            if article_id not in self.processed_ids:
                self.processed_ids.add(article_id)
                article['id'] = article_id
                article['archived_at'] = datetime.now().isoformat()
                new_articles.append(article)
        
        all_articles = existing_articles + new_articles
        
        archive_data = {
            "date": today,
            "total_articles": len(all_articles),
            "new_articles": len(new_articles),
            "articles": all_articles
        }
        
        with open(archive_file, 'w') as f:
            json.dump(archive_data, f, indent=2)
        
        logger.info(f"Archived {len(new_articles)} new articles ({len(all_articles)} total today)")
        
        return {
            "archived_count": len(new_articles),
            "total_archived": len(all_articles),
            "archive_file": str(archive_file)
        }
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute archiving - takes state, returns updated state"""
        articles = state.get("articles", [])
        filtered = state.get("filtered_articles", [])
        
        if not articles and not filtered:
            logger.warning("No articles to archive")
            state["archive_result"] = {"archived_count": 0}
            return state
        
        all_to_archive = articles + filtered
        
        result = self.archive_articles(all_to_archive)
        state["archive_result"] = result
        state["status"] = "archived"
        
        logger.info(f"Archive complete: {result['archived_count']} new articles saved")
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = ArchiveAgent()
    return agent.run(state)
