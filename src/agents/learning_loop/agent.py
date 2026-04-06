# LAGIS - Learning Loop Agent
# Self-evaluating intelligence system with prediction tracking
# NO LLM calls - Pure rule-based matching

import json
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from difflib import SequenceMatcher

from src.core.config import DATA_DIR

logger = logging.getLogger("LAGIS.LearningLoop")

PREDICTIONS_FILE = DATA_DIR / "predictions_history.json"
METRICS_FILE = DATA_DIR / "system_metrics.json"
GRAPH_FILE = DATA_DIR / "memory_graph.json"

TIMEFRAME_DAYS = {"24-72h": 3, "3-7 days": 7, "1-2 weeks": 14}

MATCH_KEYWORDS = {
    "iran_hezbollah": ["hezbollah", "lebanon", "rockets", "missile", "attack", "israel border"],
    "iran_direct": ["iran", "missile strike", "airstrike", "attack"],
    "israel_escalation": ["israel", "airstrike", "gaza", "lebanon", "operation"],
    "nuclear": ["nuclear", "uranium", "enrichment"],
    "energy": ["oil", "energy", "facility", "strait of hormuz"],
    "sanctions": ["sanctions", "embargo", "economic"],
    "troops": ["troops", "deployment", "military", "mobilization"],
    "ukraine": ["ukraine", "russia", "donbass", "offensive"],
    "taiwan": ["taiwan", "china", "strait", "military"],
    "general_conflict": ["attack", "strike", "war", "conflict", "clashes"]
}

ACTOR_PAIRS = [
    ("Iran", "Hezbollah"),
    ("Iran", "Israel"),
    ("Iran", "United States"),
    ("Israel", "Hezbollah"),
    ("Russia", "Ukraine"),
    ("China", "Taiwan"),
    ("US", "Iran")
]


class PredictionTracker:
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.predictions_file = PREDICTIONS_FILE
        self.metrics_file = METRICS_FILE
        self.graph_file = GRAPH_FILE
        self.predictions = self._load_predictions()
        self.metrics = self._load_metrics()
    
    def _load_predictions(self) -> Dict:
        if self.predictions_file.exists():
            try:
                with open(self.predictions_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"predictions": [], "last_updated": datetime.now().isoformat()[:10]}
    
    def _save_predictions(self):
        self.predictions["last_updated"] = datetime.now().isoformat()[:10]
        with open(self.predictions_file, 'w') as f:
            json.dump(self.predictions, f, indent=2)
    
    def _load_metrics(self) -> Dict:
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "total_predictions": 0,
            "correct_predictions": 0,
            "incorrect_predictions": 0,
            "pending_predictions": 0,
            "accuracy_rate": 0.0,
            "actor_accuracy": {},
            "last_updated": datetime.now().isoformat()[:10]
        }
    
    def _save_metrics(self):
        self.metrics["last_updated"] = datetime.now().isoformat()[:10]
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def _load_graph(self) -> Optional[Dict]:
        if self.graph_file.exists():
            try:
                with open(self.graph_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def _save_graph(self, graph: Dict):
        with open(self.graph_file, 'w') as f:
            json.dump(graph, f, indent=2)
    
    def store_predictions(self, scenarios: List[Dict]) -> int:
        stored = 0
        for scenario in scenarios:
            pred_id = str(uuid.uuid4())[:8]
            timeframe = scenario.get("timeframe", "1-2 weeks")
            days = TIMEFRAME_DAYS.get(timeframe, 7)
            expires = (datetime.now() + timedelta(days=days)).isoformat()[:10]
            
            prediction = {
                "id": pred_id,
                "timestamp": datetime.now().isoformat()[:10],
                "scenario": scenario.get("title", ""),
                "actors": scenario.get("actors", []),
                "probability": scenario.get("probability", "MEDIUM"),
                "timeframe": timeframe,
                "expires": expires,
                "resolved": False,
                "outcome": None,
                "confidence_score": 0.0,
                "keywords": self._extract_keywords(scenario.get("title", ""))
            }
            
            self.predictions["predictions"].append(prediction)
            stored += 1
        
        if stored > 0:
            self._save_predictions()
            logger.info(f"Stored {stored} predictions")
        
        return stored
    
    def _extract_keywords(self, title: str) -> List[str]:
        title_lower = title.lower()
        keywords = []
        for category, kws in MATCH_KEYWORDS.items():
            if any(kw in title_lower for kw in kws):
                keywords.append(category)
        return keywords if keywords else ["general_conflict"]
    
    def _actors_match(self, event_text: str, prediction_actors: List[str]) -> bool:
        event_lower = event_text.lower()
        for actor in prediction_actors:
            if actor.lower() in event_lower:
                return True
        return False
    
    def _keywords_match(self, event_text: str, pred_keywords: List[str]) -> bool:
        event_lower = event_text.lower()
        for category in pred_keywords:
            if category in MATCH_KEYWORDS:
                if any(kw in event_lower for kw in MATCH_KEYWORDS[category]):
                    return True
        return False
    
    def _is_match(self, event: Dict, prediction: Dict) -> bool:
        title = event.get("title", "")
        text = title.lower()
        
        if isinstance(event.get("countries"), list):
            text += " " + " ".join(event.get("countries", [])).lower()
        
        actors_match = self._actors_match(text, prediction.get("actors", []))
        
        keywords = prediction.get("keywords", ["general_conflict"])
        keywords_match = self._keywords_match(text, keywords)
        
        return actors_match and keywords_match
    
    def resolve_predictions(self, events: List[Dict]) -> Dict:
        results = {"resolved": 0, "correct": 0, "incorrect": 0, "updated": []}
        today = datetime.now().date()
        
        for prediction in self.predictions["predictions"]:
            if prediction.get("resolved", False):
                continue
            
            matched = False
            for event in events:
                if self._is_match(event, prediction):
                    matched = True
                    break
            
            if matched:
                prediction["resolved"] = True
                prediction["outcome"] = "correct"
                prediction["resolved_date"] = datetime.now().isoformat()[:10]
                results["correct"] += 1
                results["resolved"] += 1
                results["updated"].append(prediction["id"])
                logger.info(f"Prediction confirmed: {prediction['scenario'][:50]}")
            
            else:
                try:
                    expires = datetime.fromisoformat(prediction.get("expires", "")).date()
                    if today > expires:
                        prediction["resolved"] = True
                        prediction["outcome"] = "incorrect"
                        prediction["resolved_date"] = datetime.now().isoformat()[:10]
                        results["incorrect"] += 1
                        results["resolved"] += 1
                        results["updated"].append(prediction["id"])
                        logger.info(f"Prediction expired (incorrect): {prediction['scenario'][:50]}")
                except:
                    pass
        
        if results["resolved"] > 0:
            self._update_scores(results)
            self._save_predictions()
        
        return results
    
    def _update_scores(self, results: Dict):
        for prediction in self.predictions["predictions"]:
            if prediction.get("outcome") == "correct":
                prob = prediction.get("probability", "MEDIUM")
                score = {"HIGH": 2, "MEDIUM": 1, "LOW": 0.5}.get(prob, 1)
                prediction["confidence_score"] = score
            elif prediction.get("outcome") == "incorrect":
                prob = prediction.get("probability", "MEDIUM")
                score = {"HIGH": -2, "MEDIUM": -1, "LOW": -0.5}.get(prob, -1)
                prediction["confidence_score"] = score
    
    def update_graph_weights(self) -> int:
        graph = self._load_graph()
        if not graph or "edges" not in graph:
            return 0
        
        updated = 0
        recent_correct = []
        recent_incorrect = []
        
        for pred in self.predictions["predictions"]:
            if pred.get("resolved") and pred.get("resolved_date"):
                try:
                    resolved_date = datetime.fromisoformat(pred["resolved_date"]).date()
                    days_ago = (datetime.now().date() - resolved_date).days
                    if days_ago <= 7:
                        if pred.get("outcome") == "correct":
                            recent_correct.append(pred)
                        elif pred.get("outcome") == "incorrect":
                            recent_incorrect.append(pred)
                except:
                    pass
        
        for pred in recent_correct:
            for actor1 in pred.get("actors", []):
                for actor2 in pred.get("actors", []):
                    if actor1 == actor2:
                        continue
                    for edge in graph["edges"]:
                        if (edge["from"] == actor1 and edge["to"] == actor2) or \
                           (edge["from"] == actor2 and edge["to"] == actor1):
                            edge["weight"] = min(1.0, edge["weight"] + 0.05)
                            edge["last_seen"] = datetime.now().isoformat()[:10]
                            updated += 1
        
        for pred in recent_incorrect:
            for actor1 in pred.get("actors", []):
                for actor2 in pred.get("actors", []):
                    if actor1 == actor2:
                        continue
                    for edge in graph["edges"]:
                        if (edge["from"] == actor1 and edge["to"] == actor2) or \
                           (edge["from"] == actor2 and edge["to"] == actor1):
                            edge["weight"] = max(0.1, edge["weight"] - 0.05)
                            edge["last_seen"] = datetime.now().isoformat()[:10]
                            updated += 1
        
        if updated > 0:
            self._save_graph(graph)
            logger.info(f"Updated {updated} graph edge weights based on prediction outcomes")
        
        return updated
    
    def get_actor_accuracy(self, actor: str) -> float:
        actor_preds = [p for p in self.predictions["predictions"] 
                      if actor in p.get("actors", []) and p.get("resolved")]
        
        if not actor_preds:
            return 0.5
        
        correct = sum(1 for p in actor_preds if p.get("outcome") == "correct")
        return round(correct / len(actor_preds), 2)
    
    def calculate_accuracy(self) -> float:
        resolved = [p for p in self.predictions["predictions"] if p.get("resolved")]
        if not resolved:
            return 0.5
        
        correct = sum(1 for p in resolved if p.get("outcome") == "correct")
        return round(correct / len(resolved), 2)
    
    def update_metrics(self) -> Dict:
        all_preds = self.predictions["predictions"]
        resolved = [p for p in all_preds if p.get("resolved")]
        correct = [p for p in resolved if p.get("outcome") == "correct"]
        incorrect = [p for p in resolved if p.get("outcome") == "incorrect"]
        pending = [p for p in all_preds if not p.get("resolved")]
        
        self.metrics["total_predictions"] = len(all_preds)
        self.metrics["correct_predictions"] = len(correct)
        self.metrics["incorrect_predictions"] = len(incorrect)
        self.metrics["pending_predictions"] = len(pending)
        self.metrics["accuracy_rate"] = self.calculate_accuracy()
        
        actor_acc = {}
        all_actors = set()
        for p in all_preds:
            all_actors.update(p.get("actors", []))
        
        for actor in all_actors:
            actor_acc[actor] = self.get_actor_accuracy(actor)
        
        self.metrics["actor_accuracy"] = actor_acc
        self._save_metrics()
        
        return self.metrics
    
    def get_historical_accuracy(self, actor_pair: tuple) -> float:
        actor1, actor2 = actor_pair
        pair_preds = [p for p in self.predictions["predictions"] 
                     if (actor1 in p.get("actors", []) and actor2 in p.get("actors", []))
                     and p.get("resolved")]
        
        if not pair_preds:
            return 0.5
        
        correct = sum(1 for p in pair_preds if p.get("outcome") == "correct")
        return round(correct / len(pair_preds), 2)
    
    def get_confidence_level(self) -> str:
        accuracy = self.metrics.get("accuracy_rate", 0.5)
        total = self.metrics.get("total_predictions", 0)
        
        if total < 5:
            return "Developing"
        elif accuracy >= 0.7:
            return "High"
        elif accuracy >= 0.5:
            return "Moderate"
        else:
            return "Low"
    
    def get_pending_predictions(self) -> List[Dict]:
        return [p for p in self.predictions["predictions"] if not p.get("resolved")][:5]
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            scenarios = state.get("scenarios", [])
            events = state.get("deduplicated_events", []) or state.get("events", [])
            
            if scenarios:
                stored = self.store_predictions(scenarios)
                state["predictions_stored"] = stored
            
            if events:
                results = self.resolve_predictions(events)
                state["prediction_resolution"] = results
                
                if results["resolved"] > 0:
                    graph_updates = self.update_graph_weights()
                    state["graph_weights_updated"] = graph_updates
            
            metrics = self.update_metrics()
            state["learning_metrics"] = {
                "accuracy_rate": metrics.get("accuracy_rate", 0.5),
                "total_predictions": metrics.get("total_predictions", 0),
                "pending": metrics.get("pending_predictions", 0),
                "confidence": self.get_confidence_level()
            }
            
            pending = self.get_pending_predictions()
            if pending:
                state["pending_predictions"] = pending
            
            logger.info(f"Learning: accuracy={metrics.get('accuracy_rate', 0):.0%}, "
                       f"total={metrics.get('total_predictions', 0)}, "
                       f"confidence={self.get_confidence_level()}")
            
        except Exception as e:
            logger.error(f"Error in learning_loop: {e}")
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    tracker = PredictionTracker()
    return tracker.run(state)
