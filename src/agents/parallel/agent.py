# LAGIS - Parallel Analysis Agent
# Runs multiple intelligence modules in parallel

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
from datetime import datetime

from src.agents.risk.agent import RiskAgent
from src.agents.trend.agent import TrendAgent
from src.agents.market.agent import MarketAgent
from src.agents.intelligence.engine import IntelligenceEngine

logger = logging.getLogger("LAGIS.ParallelAnalysis")

MAX_WORKERS = 4


class ParallelAnalysisAgent:
    """Runs event analysis in parallel for maximum efficiency"""
    
    def __init__(self):
        self.risk_agent = RiskAgent()
        self.trend_agent = TrendAgent()
        self.market_agent = MarketAgent()
        self.intelligence_engine = IntelligenceEngine()
    
    def _run_risk(self, events: List[Dict]) -> Dict:
        """Run risk assessment"""
        state = {"events": events}
        try:
            return self.risk_agent.run(state)
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return {"risk_scores": {}, "error": str(e)}
    
    def _run_trends(self, events: List[Dict]) -> Dict:
        """Run trend tracking"""
        state = {"events": events, "risk_scores": {}}
        try:
            return self.trend_agent.run(state)
        except Exception as e:
            logger.error(f"Trend tracking failed: {e}")
            return {"trend_analysis": {"trends": []}, "error": str(e)}
    
    def _run_market(self, events: List[Dict]) -> Dict:
        """Run market analysis"""
        state = {"events": events}
        try:
            return self.market_agent.run(state)
        except Exception as e:
            logger.error(f"Market analysis failed: {e}")
            return {"market_analysis": {}, "error": str(e)}
    
    def _run_intelligence(self, events: List[Dict], risk_scores: Dict) -> Dict:
        """Run intelligence engine"""
        state = {"events": events, "risk_scores": risk_scores}
        try:
            return self.intelligence_engine.process(state)
        except Exception as e:
            logger.error(f"Intelligence engine failed: {e}")
            return {"intelligence": {}, "error": str(e)}
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parallel analysis"""
        events = state.get("events", [])
        
        if not events:
            logger.warning("No events for parallel analysis")
            state["parallel_results"] = {}
            return state
        
        logger.info(f"Running parallel analysis on {len(events)} events...")
        start_time = datetime.now()
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            risk_future = executor.submit(self._run_risk, events)
            trend_future = executor.submit(self._run_trends, events)
            market_future = executor.submit(self._run_market, events)
            
            risk_result = risk_future.result()
            trend_result = trend_future.result()
            market_result = market_future.result()
            
            risk_scores = risk_result.get("risk_scores", {})
            
            intel_future = executor.submit(self._run_intelligence, events, risk_scores)
            intel_result = intel_future.result()
            
            results = {
                "risk": risk_result,
                "trends": trend_result,
                "market": market_result,
                "intelligence": intel_result.get("intelligence", {})
            }
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Parallel analysis completed in {elapsed:.1f}s")
        
        state["risk_scores"] = results.get("risk", {}).get("risk_scores", {})
        state["trend_analysis"] = results.get("trends", {}).get("trend_analysis", {})
        state["market_analysis"] = results.get("market", {}).get("market_analysis", {})
        state["intelligence"] = results.get("intelligence", {})
        state["parallel_results"] = results
        state["status"] = "parallel_analysis_complete"
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = ParallelAnalysisAgent()
    return agent.run(state)
