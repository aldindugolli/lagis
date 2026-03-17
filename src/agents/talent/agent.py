# LAGIS - Talent Intelligence Agent
# Detects hiring signals, defense expansion, AI investment, workforce movement

import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from src.core.llm.engine import get_llm

logger = logging.getLogger("LAGIS.Talent")


class TalentIntelAgent:
    """Detects strategic workforce and investment signals"""
    
    def __init__(self):
        self.llm = get_llm()
        
        self.signal_keywords = [
            "hiring", "recruitment", "job posting", "open positions",
            "defense contract", "military procurement", "weapons",
            "AI investment", "tech hiring", "expansion",
            "semiconductor", "supply chain", "critical minerals"
        ]
    
    def _extract_talent_signals(self, articles: List[Dict]) -> List[Dict]:
        """Extract talent and investment signals from articles"""
        signals = []
        
        for article in articles:
            content = (article.get('title', '') + ' ' + article.get('content', '')).lower()
            
            for keyword in self.signal_keywords:
                if keyword in content:
                    signals.append({
                        "title": article.get('title', ''),
                        "source": article.get('source', ''),
                        "signal_type": self._classify_signal(keyword),
                        "keyword": keyword,
                        "url": article.get('url', '')
                    })
                    break
        
        return signals[:10]
    
    def _classify_signal(self, keyword: str) -> str:
        """Classify the type of signal"""
        defense_keywords = ["defense", "military", "weapons", "procurement"]
        ai_keywords = ["AI", "artificial intelligence", "tech"]
        economic_keywords = ["investment", "expansion", "supply chain", "semiconductor"]
        
        if keyword in defense_keywords:
            return "defense_expansion"
        elif keyword in ai_keywords:
            return "ai_investment"
        elif keyword in economic_keywords:
            return "economic_strategic"
        else:
            return "workforce"
    
    def _analyze_signals(self, signals: List[Dict]) -> Dict[str, Any]:
        """Analyze extracted signals"""
        if not signals:
            return {"summary": "No strategic signals detected."}
        
        signal_types = {}
        for s in signals:
            t = s['signal_type']
            signal_types[t] = signal_types.get(t, 0) + 1
        
        analysis = f"""TALENT & INVESTMENT INTELLIGENCE

Signals Detected: {len(signals)}

By Category:"""
        
        for stype, count in signal_types.items():
            analysis += f"\n• {stype.replace('_', ' ').title()}: {count}"
        
        analysis += "\n\nKey Developments:"
        
        defense_signals = [s for s in signals if s['signal_type'] == 'defense_expansion']
        if defense_signals:
            analysis += "\n[DEFENSE]"
            for s in defense_signals[:3]:
                analysis += f"\n• {s['title'][:80]}"
        
        ai_signals = [s for s in signals if s['signal_type'] == 'ai_investment']
        if ai_signals:
            analysis += "\n[AI/TECH]"
            for s in ai_signals[:3]:
                analysis += f"\n• {s['title'][:80]}"
        
        return {
            "summary": analysis,
            "signal_count": len(signals),
            "signal_types": signal_types
        }
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute talent intelligence analysis"""
        articles = state.get("articles", [])
        
        if not articles:
            logger.warning("No articles for talent intelligence")
            state["talent_intel"] = {"summary": "No articles available"}
            return state
        
        signals = self._extract_talent_signals(articles)
        analysis = self._analyze_signals(signals)
        
        state["talent_intel"] = analysis
        state["status"] = "talent_analyzed"
        
        logger.info(f"Talent intel: {analysis.get('signal_count', 0)} signals detected")
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = TalentIntelAgent()
    return agent.run(state)
