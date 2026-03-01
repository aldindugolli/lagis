# LAGIS - LangGraph Orchestration
# Agent pipeline execution

import logging
from datetime import datetime
from typing import Dict, Any, List, Callable

from src.core.state.state import create_initial_state
from src.agents.collector.agent import run as collector_run
from src.agents.archive.agent import run as archive_run
from src.agents.knowledge.agent import run as knowledge_run
from src.agents.context.agent import run as context_run
from src.agents.extractor.agent import run as extractor_run
from src.agents.analyst.agent import run as analyst_run
from src.agents.risk.agent import run as risk_run
from src.agents.market.agent import run as market_run
from src.agents.kosovo.agent import run as kosovo_run
from src.agents.executive.agent import run as executive_run

logger = logging.getLogger("LAGIS.Graph")


class IntelligenceGraph:
    """LangGraph-style orchestration of agents"""
    
    def __init__(self):
        self.nodes: List[tuple[str, Callable]] = [
            ("collect", collector_run),
            ("archive", archive_run),
            ("embed_memory", knowledge_run),
            ("retrieve_context", context_run),
            ("extract", extractor_run),
            ("analyze", analyst_run),
            ("assess_risk", risk_run),
            ("market", market_run),
            ("kosovo", kosovo_run),
            ("generate_brief", executive_run),
        ]
    
    def run(self, state: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the full pipeline"""
        if state is None:
            state = create_initial_state()
        
        logger.info("=" * 50)
        logger.info("Starting LAGIS Intelligence Pipeline")
        ts = datetime.now().isoformat()
        logger.info(f"Timestamp: {ts}")
        logger.info("=" * 50)
        
        for name, agent_func in self.nodes:
            logger.info(f">>> Running: {name}")
            try:
                state = agent_func(state)
                logger.info(f"<<< Completed: {name}")
            except Exception as e:
                logger.error(f"Error in {name}: {e}")
                state["errors"] = state.get("errors", []) + [str(e)]
        
        state["completed_at"] = datetime.now().isoformat()
        
        logger.info("=" * 50)
        logger.info("Pipeline Complete")
        logger.info(f"Final status: {state.get('status', 'unknown')}")
        logger.info("=" * 50)
        
        return state


def run_pipeline() -> Dict[str, Any]:
    """Run the full daily pipeline"""
    graph = IntelligenceGraph()
    return graph.run()


def run_to(agent_name: str) -> Dict[str, Any]:
    """Run pipeline up to a specific agent"""
    graph = IntelligenceGraph()
    state = create_initial_state()
    
    for name, agent_func in graph.nodes:
        if name == agent_name:
            break
        state = agent_func(state)
    
    return state
