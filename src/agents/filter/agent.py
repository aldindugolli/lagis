# LAGIS - Article Filter Agent
# Three-layer geopolitical relevance filter

import logging
import re
from typing import Dict, Any, List, Tuple

logger = logging.getLogger("LAGIS.Filter")

GEOPOLITICAL_KEYWORDS = {
    "military_conflict": [
        "war", "military", "troops", "invasion", "strike", "missile", "bombing",
        "artillery", "drone", "airstrike", "naval", "battle", "mobilization",
        "clashes", "frontline", "defense system", "military buildup", "combat",
        "offensive", "defensive", "armed", "attack", "hostilities"
    ],
    "nuclear_strategic": [
        "nuclear", "uranium", "ballistic missile", "warhead", "deterrence",
        "ICBM", "nuclear test", "proliferation", "arms control", "strategic arsenal",
        "enrichment", "fissile", "atomic", "radiation", "nuclear program"
    ],
    "political_instability": [
        "coup", "protest", "uprising", "martial law", "regime change", "dictatorship",
        "state of emergency", "crackdown", "political crisis", "rebellion",
        "revolution", "unrest", "arrest", "detention"
    ],
    "economic_warfare": [
        "sanctions", "trade war", "tariffs", "economic blockade", "export controls",
        "financial restrictions", "currency collapse", "embargo", "punitive measures",
        "trade restrictions"
    ],
    "strategic_infrastructure": [
        "pipeline", "energy supply", "rare earth", "semiconductors", "critical minerals",
        "shipping lane", "strait", "port blockade", "oil", "gas", "energy crisis",
        "supply chain", "infrastructure"
    ],
    "alliance_diplomacy": [
        "NATO", "alliance", "defense pact", "military agreement", "security cooperation",
        "summit", "treaty", "strategic partnership", "EU", "UN", "security council",
        "diplomatic", "negotiations", "peace talks"
    ]
}

COUNTRIES_REGIONS = {
    "usa": ["united states", "america", "us ", "u.s.", "washington"],
    "china": ["china", "chinese", "beijing", "xi jinping"],
    "russia": ["russia", "russian", "moscow", "kremlin", "putin"],
    "iran": ["iran", "iranian", "tehran", "khamenei"],
    "israel": ["israel", "israeli", "tel aviv", "netanyahu"],
    "ukraine": ["ukraine", "ukrainian", "kyiv", "kiev"],
    "north_korea": ["north korea", "pyongyang", "kim jong"],
    "south_korea": ["south korea", "seoul"],
    "taiwan": ["taiwan", "taipei"],
    "india": ["india", "indian", "new delhi"],
    "pakistan": ["pakistan", "pakistani", "islamabad"],
    "saudi_arabia": ["saudi", "riyadh"],
    "turkey": ["turkey", "turkish", "ankara", "erdogan"],
    "germany": ["germany", "german", "berlin"],
    "france": ["france", "french", "paris"],
    "uk": ["britain", "british", "uk ", "london", "england"],
    "poland": ["poland", "polish", "warsaw"],
    "japan": ["japan", "japanese", "tokyo"],
    "australia": ["australia", "australian", "canberra"],
    "brazil": ["brazil", "brazilian", "brasilia"],
    "south_africa": ["south africa", "pretoria"],
    "kosovo": ["kosovo", "pristina", "serbia", "belgrade"],
    "nato": ["nato", "north atlantic"],
    "eu": ["european union", "european commission"],
    "syria": ["syria", "syrian", "damascus"],
    "yemen": ["yemen", "yemeni", "sanaa"],
    "afghanistan": ["afghanistan", "afghan", "kabul"]
}


def calculate_relevance_score(article: Dict[str, str]) -> Tuple[int, Dict[str, int]]:
    """Calculate geopolitical relevance score for an article"""
    text = (article.get("title", "") + " " + article.get("content", "")).lower()
    
    scores = {}
    total_score = 0
    
    for category, keywords in GEOPOLITICAL_KEYWORDS.items():
        category_score = 0
        for keyword in keywords:
            if keyword in text:
                if category == "military_conflict":
                    category_score = 3
                elif category == "nuclear_strategic":
                    category_score = 4
                elif category in ["political_instability", "economic_warfare"]:
                    category_score = 2
                elif category == "strategic_infrastructure":
                    category_score = 2
                elif category == "alliance_diplomacy":
                    category_score = 2
                break
        
        if category_score > 0:
            scores[category] = category_score
            total_score += category_score
    
    country_count = 0
    mentioned_countries = []
    for country, patterns in COUNTRIES_REGIONS.items():
        for pattern in patterns:
            if pattern in text:
                country_count += 1
                mentioned_countries.append(country)
                break
    
    if country_count >= 2:
        total_score += 2
        scores["multiple_countries"] = 2
    elif country_count >= 1:
        total_score += 1
        scores["country_mention"] = 1
    
    scores["country_count"] = country_count
    scores["mentioned_countries"] = list(set(mentioned_countries))
    
    return total_score, scores


def filter_articles(articles: List[Dict[str, Any]], threshold: int = 4) -> Tuple[List[Dict], List[Dict]]:
    """Filter articles by geopolitical relevance score"""
    relevant = []
    filtered = []
    
    for article in articles:
        score, details = calculate_relevance_score(article)
        article["relevance_score"] = score
        article["relevance_details"] = details
        
        if score >= threshold:
            relevant.append(article)
        else:
            filtered.append(article)
    
    logger.info(f"Article filter: {len(relevant)} relevant (score >= {threshold}), {len(filtered)} filtered out")
    
    return relevant, filtered


def score_event_importance(event: Dict[str, Any]) -> int:
    """Calculate importance score for extracted event"""
    text = (event.get("event_title", "") + " " + event.get("summary", "")).lower()
    
    score = 0
    
    if any(kw in text for kw in ["military strike", "missile", "bombing", "attack", "invasion"]):
        score += 3
    elif any(kw in text for kw in ["war", "combat", "clashes"]):
        score += 2
    
    if any(kw in text for kw in ["nuclear", "warhead", "missile launch"]):
        score += 4
    
    if any(kw in text for kw in ["sanctions", "tariff", "trade war"]):
        score += 2
    
    if any(kw in text for kw in ["alliance", "nato", "treaty", "summit"]):
        score += 2
    
    if any(kw in text for kw in ["protest", "coup", "uprising", "crackdown"]):
        score += 1
    
    severity = event.get("severity_score", 0)
    if severity >= 7:
        score += 2
    elif severity >= 5:
        score += 1
    
    return score


def filter_events_by_importance(events: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Filter events by importance score"""
    high_priority = []
    archive_only = []
    
    for event in events:
        importance = score_event_importance(event)
        event["importance_score"] = importance
        
        if importance >= 3:
            high_priority.append(event)
        else:
            archive_only.append(event)
    
    logger.info(f"Event importance: {len(high_priority)} high-priority, {len(archive_only)} archive-only")
    
    return high_priority, archive_only


class ArticleFilterAgent:
    """Filters articles by geopolitical relevance"""
    
    def __init__(self, threshold: int = 4):
        self.threshold = threshold
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        articles = state.get("articles", [])
        
        if not articles:
            state["relevant_articles"] = []
            state["filtered_articles"] = []
            state["status"] = "filtered"
            return state
        
        relevant, filtered = filter_articles(articles, self.threshold)
        
        state["relevant_articles"] = relevant
        state["filtered_articles"] = filtered
        state["filter_stats"] = {
            "total": len(articles),
            "relevant": len(relevant),
            "filtered": len(filtered)
        }
        state["status"] = "filtered"
        
        logger.info(f"Filtered {len(articles)} articles -> {len(relevant)} relevant")
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = ArticleFilterAgent()
    return agent.run(state)
