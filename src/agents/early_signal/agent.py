# LAGIS - Early Signal Detection System
# Predictive intelligence engine - converts signals into real-world meaning
# NO LLM calls - fully rule-based + statistical

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.core.config import DATA_DIR

logger = logging.getLogger("LAGIS.EarlySignal")

SIGNAL_CATEGORIES = {
    "military": ["troops", "missile", "drill", "exercise", "deployment", "military", "army"],
    "conflict": ["attack", "airstrike", "clash", "offensive", "strike", "war", "invasion"],
    "economic": ["sanctions", "tariff", "oil", "gas", "trade", "embargo", "economic"],
    "political": ["warning", "threat", "tensions", "ultimatum", "diplomatic", "negotiations"],
    "nuclear": ["nuclear", "uranium", "enrichment", "atomic", "radiation", "warhead"]
}

COUNTRIES = ["iran", "israel", "china", "russia", "taiwan", "ukraine", "usa", "north korea"]

HISTORY_FILE = DATA_DIR / "signals_history.json"
MAX_HISTORY_DAYS = 7
SPIKE_THRESHOLD = 1.8
MIN_SPIKE_COUNT = 5
ELEVATED_THRESHOLD = 15


class SignalInterpreter:
    """Converts raw signals into geopolitical narratives"""
    
    COUNTRY_INTERPRETATIONS = {
        "iran": {
            "military": "Potential military escalation involving Iran",
            "conflict": "Increasing likelihood of confrontation with Iran",
            "economic": "Intensifying economic pressure on Iran",
            "nuclear": "Nuclear-related activity involving Iran raises concern",
            "political": "Rising political tensions involving Iran"
        },
        "israel": {
            "military": "Military activity linked to Israel",
            "conflict": "Escalation indicators in Israel-related tensions",
            "economic": "Economic dimensions of Israel-related conflict",
            "nuclear": "Strategic concerns involving Israel",
            "political": "Political developments affecting Israel"
        },
        "china": {
            "military": "Military activity linked to China",
            "conflict": "Tension indicators involving China",
            "economic": "Economic signals from China-related activity",
            "nuclear": "Strategic positioning involving China",
            "political": "Political developments concerning China"
        },
        "russia": {
            "military": "Military activity involving Russia",
            "conflict": "Conflict indicators in Russia-related tensions",
            "economic": "Economic pressure or activity involving Russia",
            "nuclear": "Nuclear dimensions of Russia-related activity",
            "political": "Political tensions involving Russia"
        },
        "taiwan": {
            "military": "Military activity near Taiwan",
            "conflict": "Rising tensions in Taiwan Strait",
            "economic": "Economic implications of Taiwan developments",
            "nuclear": "Strategic implications for Taiwan",
            "political": "Political situation in Taiwan Strait"
        },
        "ukraine": {
            "military": "Military developments in Ukraine conflict",
            "conflict": "Escalation indicators in Ukraine",
            "economic": "Economic dimensions of Ukraine situation",
            "nuclear": "Nuclear risk factors in Ukraine",
            "political": "Political developments in Ukraine conflict"
        },
        "usa": {
            "military": "US military activity",
            "conflict": "US involvement in escalating tensions",
            "economic": "US economic actions affecting stability",
            "nuclear": "US strategic positioning",
            "political": "US diplomatic activity"
        },
        "north korea": {
            "military": "North Korean military activity",
            "conflict": "Indicators of North Korean escalation",
            "nuclear": "Nuclear activity in North Korea"
        }
    }
    
    GLOBAL_INTERPRETATIONS = {
        "military": "Elevated military activity detected globally",
        "conflict": "Increased conflict-related signals globally",
        "economic": "Heightened economic tensions detected",
        "political": "Rising political instability signals",
        "nuclear": "Nuclear-related activity raises strategic concern"
    }
    
    def interpret_country_signal(self, country: str, category: str) -> str:
        """Get interpretive message for country + category signal"""
        if country in self.COUNTRY_INTERPRETATIONS:
            if category in self.COUNTRY_INTERPRETATIONS[country]:
                return self.COUNTRY_INTERPRETATIONS[country][category]
        return f"Activity detected in {country.title()} region"
    
    def interpret_global_signal(self, category: str) -> str:
        """Get interpretive message for global category signal"""
        return self.GLOBAL_INTERPRETATIONS.get(category, f"Global {category} signals elevated")
    
    def calculate_confidence(self, spike_ratio: float, count: int, history_len: int) -> tuple:
        """Calculate confidence level based on spike strength and data quality"""
        if history_len < 3:
            base = "low"
        elif history_len >= 5:
            base = "medium" if spike_ratio < 2.5 else "high"
        else:
            base = "low" if spike_ratio < 2.0 else "medium"
        
        if count >= 30:
            modifier = "high"
        elif count >= 15:
            modifier = "medium"
        else:
            modifier = "low"
        
        if modifier == "high" and base in ["medium", "high"]:
            final = "high"
        elif modifier == "low" and base == "low":
            final = "low"
        else:
            final = base
        
        return final, f"{final.capitalize()} confidence based on {'sustained' if history_len >= 5 else 'limited'} data"
    
    def generate_prediction(self, signal_type: str, country: Optional[str], confidence: str) -> str:
        """Generate forward-looking prediction based on signal"""
        if confidence == "low":
            return None
        
        if country:
            country_title = country.title()
        else:
            country_title = "region"
        
        predictions = {
            "high": f"High probability of near-term developments in {country_title}",
            "medium": f"Elevated probability of escalation in {country_title}",
            "low": f"Monitor for potential developments in {country_title}"
        }
        
        return predictions.get(confidence)


class EarlySignalDetector:
    """Lightweight early signal detection using statistical analysis"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.history_file = HISTORY_FILE
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.interpreter = SignalInterpreter()
    
    def _load_history(self) -> Dict:
        """Load signal history"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
                    if "timestamp" not in history:
                        return self._create_empty_history()
                    return history
            except:
                pass
        return self._create_empty_history()
    
    def _create_empty_history(self) -> Dict:
        """Create empty history structure"""
        history = {"timestamp": [], "categories": {}, "countries": {}}
        for cat in SIGNAL_CATEGORIES:
            history["categories"][cat] = []
        for country in COUNTRIES:
            history["countries"][country] = []
        return history
    
    def _save_history(self, history: Dict):
        """Save signal history"""
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def _cleanup_old_history(self, history: Dict):
        """Keep only last 7 days of data"""
        timestamps = history.get("timestamp", [])
        if not timestamps:
            return
        
        cutoff = datetime.now() - timedelta(days=MAX_HISTORY_DAYS)
        valid_indices = []
        
        for i, ts in enumerate(timestamps):
            try:
                dt = datetime.fromisoformat(ts)
                if dt >= cutoff:
                    valid_indices.append(i)
            except:
                pass
        
        if len(valid_indices) < len(timestamps):
            for cat in history.get("categories", {}):
                history["categories"][cat] = [history["categories"][cat][i] for i in valid_indices if i < len(history["categories"][cat])]
            for country in history.get("countries", {}):
                history["countries"][country] = [history["countries"][country][i] for i in valid_indices if i < len(history["countries"][country])]
            history["timestamp"] = [timestamps[i] for i in valid_indices]
    
    def extract_signals(self, articles: List[Dict]) -> tuple:
        """Extract signal counts from articles"""
        category_counts = {cat: 0 for cat in SIGNAL_CATEGORIES}
        country_counts = {country: 0 for country in COUNTRIES}
        
        for article in articles:
            text = (article.get("title", "") + " " + article.get("content", "")).lower()
            
            for cat, keywords in SIGNAL_CATEGORIES.items():
                if any(kw in text for kw in keywords):
                    category_counts[cat] += 1
            
            for country in COUNTRIES:
                if country in text:
                    country_counts[country] += 1
        
        return category_counts, country_counts
    
    def detect_spike(self, current: int, history: List[int]) -> tuple:
        """Detect if current count is a spike vs historical average, return (is_spike, ratio)"""
        if current < MIN_SPIKE_COUNT:
            return False, 0.0
        
        if not history:
            return current >= 20, current / 5.0 if current > 0 else 0.0
        
        avg = sum(history) / len(history) if history else 0
        if avg == 0:
            return current >= 20, current / 5.0 if current > 0 else 0.0
        
        ratio = current / avg
        return ratio >= SPIKE_THRESHOLD, ratio
    
    def detect_country_spike(self, current: int, history: List[int]) -> tuple:
        """Detect country mention spike"""
        if current < 3:
            return False, 0.0
        
        if not history:
            return current >= 10, current / 5.0 if current > 0 else 0.0
        
        avg = sum(history) / len(history) if history else 0
        if avg == 0:
            return current >= 10, current / 5.0 if current > 0 else 0.0
        
        ratio = current / avg
        return ratio >= 1.5, ratio
    
    def generate_intelligence_signals(self, category_counts: Dict, country_counts: Dict, history: Dict) -> List[Dict]:
        """Generate interpreted intelligence signals"""
        signals = []
        
        for cat in category_counts:
            current = category_counts[cat]
            cat_history = history.get("categories", {}).get(cat, [])
            
            is_spike, ratio = self.detect_spike(current, cat_history)
            
            if is_spike or current >= ELEVATED_THRESHOLD:
                confidence, explanation = self.interpreter.calculate_confidence(
                    ratio, current, len(cat_history)
                )
                
                if confidence == "low" and current < 20:
                    continue
                
                narrative = self.interpreter.interpret_global_signal(cat)
                prediction = self.interpreter.generate_prediction(cat, None, confidence)
                
                signals.append({
                    "type": cat,
                    "narrative": narrative,
                    "confidence": confidence,
                    "explanation": explanation,
                    "prediction": prediction,
                    "count": current,
                    "is_spike": is_spike,
                    "spike_ratio": ratio
                })
        
        for country in country_counts:
            current = country_counts[country]
            country_history = history.get("countries", {}).get(country, [])
            
            is_spike, ratio = self.detect_country_spike(current, country_history)
            
            if is_spike or current >= 10:
                confidence, explanation = self.interpreter.calculate_confidence(
                    ratio, current, len(country_history)
                )
                
                if confidence == "low" and current < 15:
                    continue
                
                narrative = self.interpreter.interpret_country_signal(country, "conflict")
                
                for cat in category_counts:
                    cat_current = category_counts[cat]
                    if cat_current >= 10:
                        narrative = self.interpreter.interpret_country_signal(country, cat)
                        break
                
                prediction = self.interpreter.generate_prediction(None, country, confidence)
                
                signals.append({
                    "type": "country",
                    "country": country,
                    "narrative": narrative,
                    "confidence": confidence,
                    "explanation": explanation,
                    "prediction": prediction,
                    "count": current,
                    "is_spike": is_spike,
                    "spike_ratio": ratio
                })
        
        signals.sort(key=lambda x: (
            {"high": 0, "medium": 1, "low": 2}.get(x["confidence"], 3),
            -x.get("count", 0)
        ))
        
        return signals[:4]
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute early signal detection"""
        articles = state.get("relevant_articles", [])
        
        if not articles:
            state["early_signals"] = []
            state["signal_counts"] = {"categories": {}, "countries": {}}
            return state
        
        category_counts, country_counts = self.extract_signals(articles)
        
        history = self._load_history()
        
        self._cleanup_old_history(history)
        
        timestamp = datetime.now().isoformat()
        history["timestamp"].append(timestamp)
        
        for cat in category_counts:
            if cat in history["categories"]:
                history["categories"][cat].append(category_counts[cat])
        
        for country in country_counts:
            if country in history["countries"]:
                history["countries"][country].append(country_counts[country])
            else:
                history["countries"][country] = [country_counts[country]]
        
        self._save_history(history)
        
        intelligence_signals = self.generate_intelligence_signals(category_counts, country_counts, history)
        
        state["early_signals"] = intelligence_signals
        state["signal_counts"] = {
            "categories": category_counts,
            "countries": country_counts
        }
        
        if intelligence_signals:
            logger.info(f"Intelligence signals generated: {len(intelligence_signals)}")
            for sig in intelligence_signals[:3]:
                logger.info(f"  - {sig.get('narrative', 'unknown')[:60]} ({sig.get('confidence', 'low')})")
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for pipeline"""
    detector = EarlySignalDetector()
    return detector.run(state)
