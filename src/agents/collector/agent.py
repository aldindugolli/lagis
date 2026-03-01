# LAGIS - Collector Agent
# Collects news from RSS feeds

import json
import hashlib
import logging
import feedparser
from pathlib import Path
from typing import Dict, Any, List

from src.core.memory.memory import get_memory

logger = logging.getLogger("LAGIS.Collector")

CONFIG_PATH = Path("config/settings.json")


def load_feeds() -> List[Dict[str, str]]:
    """Load RSS feeds from config"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
            return config.get("rss_feeds", [])
    except Exception as e:
        logger.warning(f"Could not load config: {e}, using defaults")
        return [
            {"name": "Reuters World", "url": "https://www.reutersagency.com/feed/?best-regions=world&post_type=best"},
            {"name": "BBC World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
            {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
        ]


class CollectorAgent:
    """Collects news articles from RSS feeds"""
    
    def __init__(self):
        self.memory = get_memory()
        self.feeds = load_feeds()
        logger.info(f"Collector initialized with {len(self.feeds)} feeds")
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute collection - takes state, returns updated state"""
        articles = []
        seen_hashes = set()
        
        for feed in self.feeds:
            try:
                logger.info(f"Fetching: {feed['name']}")
                parsed = feedparser.parse(feed["url"])
                
                for entry in parsed.entries[:10]:  # Reduced for speed
                    article_hash = hashlib.md5(
                        (entry.get("title", "") + entry.get("link", "")).encode()
                    ).hexdigest()
                    
                    if article_hash not in seen_hashes:
                        seen_hashes.add(article_hash)
                        article = {
                            "title": entry.get("title", ""),
                            "url": entry.get("link", ""),
                            "source": feed["name"],
                            "content": entry.get("summary", ""),
                            "published": entry.get("published", "")
                        }
                        articles.append(article)
                        self.memory.store_article(article)
                        
            except Exception as e:
                logger.error(f"Error fetching {feed['name']}: {e}")
                errors = state.get("errors", [])
                errors.append(f"Collector error ({feed['name']}): {str(e)}")
                state["errors"] = errors
        
        logger.info(f"Collected {len(articles)} unique articles")
        state["articles"] = articles
        state["status"] = "collected"
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = CollectorAgent()
    return agent.run(state)
