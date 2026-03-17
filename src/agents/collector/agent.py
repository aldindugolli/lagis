# LAGIS - Collector Agent
# Collects news from RSS feeds with parallel fetching

import json
import hashlib
import logging
import feedparser
from pathlib import Path
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.core.memory.memory import get_memory

logger = logging.getLogger("LAGIS.Collector")

CONFIG_PATH = Path("config/settings.json")
MAX_WORKERS = 10
ARTICLES_PER_FEED = 8


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


def fetch_feed(feed: Dict[str, str]) -> Tuple[str, List[Dict], str]:
    """Fetch a single RSS feed - returns (name, articles, error)"""
    name = feed["name"]
    url = feed["url"]
    
    try:
        parsed = feedparser.parse(url)
        articles = []
        
        for entry in parsed.entries[:ARTICLES_PER_FEED]:
            article = {
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "source": name,
                "content": entry.get("summary", ""),
                "published": entry.get("published", "")
            }
            articles.append(article)
        
        return (name, articles, "")
    
    except Exception as e:
        return (name, [], str(e))


class CollectorAgent:
    """Collects news articles from RSS feeds in parallel"""
    
    def __init__(self):
        self.memory = get_memory()
        self.feeds = load_feeds()
        logger.info(f"Collector initialized with {len(self.feeds)} feeds")
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parallel collection"""
        articles = []
        seen_hashes = set()
        errors = []
        
        logger.info(f"Fetching {len(self.feeds)} feeds in parallel...")
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(fetch_feed, feed): feed for feed in self.feeds}
            
            for future in as_completed(futures):
                feed = futures[future]
                try:
                    name, feed_articles, error = future.result()
                    
                    if error:
                        logger.warning(f"Error fetching {name}: {error}")
                        errors.append(f"Collector error ({name}): {error}")
                    else:
                        logger.info(f"Fetched {name}: {len(feed_articles)} articles")
                        
                        for article in feed_articles:
                            article_hash = hashlib.md5(
                                (article.get("title", "") + article.get("url", "")).encode()
                            ).hexdigest()
                            
                            if article_hash not in seen_hashes:
                                seen_hashes.add(article_hash)
                                articles.append(article)
                
                except Exception as e:
                    logger.error(f"Future error: {e}")
        
        for article in articles:
            try:
                self.memory.store_article(article)
            except Exception:
                pass
        
        logger.info(f"Collected {len(articles)} unique articles from {len(self.feeds)} feeds")
        
        state["articles"] = articles
        state["errors"] = errors
        state["status"] = "collected"
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = CollectorAgent()
    return agent.run(state)
