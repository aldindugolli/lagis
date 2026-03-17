# LAGIS - Alert Monitor Agent
# Continuously computes escalation index and triggers alerts

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.core.llm.engine import get_llm
from src.core.world_model.engine import get_world_model
from src.interfaces.telegram_sender import get_telegram

logger = logging.getLogger("LAGIS.Alerts")


class AlertMonitorAgent:
    """Monitors escalation thresholds and triggers alerts"""
    
    def __init__(self):
        self.llm = get_llm()
        self.world_model = get_world_model()
        
        self.escalation_thresholds = {
            "critical": 8.0,
            "high": 6.5,
            "medium": 5.0,
            "low": 3.5
        }
    
    def _calculate_escalation_index(self, risk_scores: Dict, events: List[Dict]) -> float:
        """Calculate global escalation index (0-10)"""
        if not risk_scores:
            return 0.0
        
        country_risks = [r.get('overall_risk_score', 0) for r in risk_scores.values()]
        avg_risk = sum(country_risks) / len(country_risks)
        
        severe_events = [e for e in events if e.get('severity_score', 0) >= 7]
        event_factor = min(len(severe_events) * 0.3, 1.5)
        
        high_risk_countries = len([r for r in country_risks if r >= 6])
        concentration_factor = high_risk_countries * 0.15
        
        escalation_index = (avg_risk * 0.6) + event_factor + concentration_factor
        
        return min(escalation_index, 10.0)
    
    def _determine_alert_level(self, index: float) -> str:
        """Determine alert level from index"""
        if index >= self.escalation_thresholds["critical"]:
            return "critical"
        elif index >= self.escalation_thresholds["high"]:
            return "high"
        elif index >= self.escalation_thresholds["medium"]:
            return "medium"
        else:
            return "low"
    
    def _generate_alert_message(self, index: float, level: str, risk_scores: Dict, events: List[Dict]) -> str:
        """Generate alert message"""
        severe_events = [e for e in events if e.get('severity_score', 0) >= 7]
        
        message = f"""[ALERT] LAGIS ESCALATION NOTIFICATION

Level: {level.upper()}
Index: {index:.1f}/10

Severe Events: {len(severe_events)}
High-Risk Countries: {len([r for r in risk_scores.values() if r.get('overall_risk_score', 0) >= 6])}

Top Concerns:"""

        sorted_risks = sorted(
            risk_scores.items(),
            key=lambda x: x[1].get('overall_risk_score', 0),
            reverse=True
        )
        
        for country, risk in sorted_risks[:5]:
            score = risk.get('overall_risk_score', 0)
            message += f"\n• {country}: {score:.1f}/10"
        
        if severe_events:
            message += "\n\nCritical Events:"
            for e in severe_events[:3]:
                message += f"\n• {e.get('event_title', 'Unknown')[:60]}"
        
        return message
    
    def _send_telegram_alert(self, message: str) -> bool:
        """Send alert via Telegram"""
        try:
            telegram = get_telegram()
            if telegram.enabled:
                telegram.send_message(message)
                return True
        except Exception as e:
            logger.warning(f"Telegram alert failed: {e}")
        return False
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute alert monitoring"""
        risk_scores = state.get("risk_scores", {})
        events = state.get("events", [])
        
        escalation_index = self._calculate_escalation_index(risk_scores, events)
        alert_level = self._determine_alert_level(escalation_index)
        
        alert_result = {
            "escalation_index": escalation_index,
            "alert_level": alert_level,
            "thresholds": self.escalation_thresholds,
            "alert_sent": False
        }
        
        if alert_level in ["critical", "high"]:
            alert_message = self._generate_alert_message(
                escalation_index, alert_level, risk_scores, events
            )
            
            alert_result["alert_message"] = alert_message
            
            if self._send_telegram_alert(alert_message):
                alert_result["alert_sent"] = True
                logger.warning(f"ALERT SENT: {alert_level} - Index {escalation_index:.1f}")
        
        state["alert_result"] = alert_result
        state["status"] = "alerts_computed"
        
        logger.info(f"Escalation index: {escalation_index:.1f} ({alert_level})")
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = AlertMonitorAgent()
    return agent.run(state)
