# LAGIS - Ultra-Optimized Parallel Intelligence Pipeline
# Target runtime: 45-60 seconds

import logging
from datetime import datetime
from typing import Dict, Any, List, Callable

from src.core.state.state import create_initial_state
from src.agents.collector.agent import run as collector_run
from src.agents.archive.agent import run as archive_run
from src.agents.filter.agent import run as filter_run
from src.agents.quick_analysis.agent import run as quick_analysis_run
from src.agents.signals.agent import run as signals_run
from src.agents.context.agent import run as context_run
from src.agents.knowledge.agent import run as knowledge_run
from src.agents.intelligence_synthesis.agent import run as synthesis_run
from src.agents.memory_graph.agent import run as memory_graph_run
from src.agents.kosovo.agent import run as kosovo_run
from src.agents.brief.agent import run as brief_run

logger = logging.getLogger("LAGIS.Graph")


class IntelligenceGraph:
    """Ultra-optimized parallel intelligence pipeline"""
    
    def __init__(self):
        self.nodes: List[tuple[str, Callable]] = [
            ("collect_feeds", collector_run),
            ("archive", archive_run),
            ("article_filter", filter_run),
            ("quick_analysis", quick_analysis_run),
            ("signal_detection", signals_run),
            ("context_retrieval", context_run),
            ("embed_events", knowledge_run),
            ("memory_graph", memory_graph_run),
            ("intelligence_synthesis", synthesis_run),
            ("kosovo_impact", kosovo_run),
            ("generate_brief", brief_run),
        ]
    
    def run(self, state: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute optimized pipeline"""
        if state is None:
            state = create_initial_state()
        
        state["_efficiency"] = {
            "stages_run": 0,
            "stages_skipped": 0,
            "llm_calls": 0,
            "start_time": datetime.now().isoformat()
        }
        
        logger.info("=" * 50)
        logger.info("Starting LAGIS Ultra-Optimized Pipeline")
        ts = datetime.now().isoformat()
        logger.info(f"Timestamp: {ts}")
        logger.info("=" * 50)
        
        early_exit = False
        for name, agent_func in self.nodes:
            if early_exit:
                state["_efficiency"]["stages_skipped"] += 1
                logger.info(f"<<< Skipped: {name} (early exit)")
                continue
            
            logger.info(f">>> Running: {name}")
            try:
                state = agent_func(state)
                
                skipped = state.get("_stage_skipped", False)
                if skipped:
                    state["_efficiency"]["stages_skipped"] += 1
                    logger.info(f"<<< Skipped: {name} ({skipped})")
                else:
                    state["_efficiency"]["stages_run"] += 1
                    logger.info(f"<<< Completed: {name}")
                
                state["_stage_skipped"] = False
                
                if name == "collect_feeds" and not state.get("articles"):
                    logger.warning("No articles - early exit")
                    early_exit = True
                
                if name == "article_filter" and not state.get("relevant_articles"):
                    logger.warning("No relevant articles - early exit")
                    state["_stage_skipped"] = "no_relevant_articles"
                
            except Exception as e:
                logger.error(f"Error in {name}: {e}")
                state["errors"] = state.get("errors", []) + [str(e)]
        
        state["completed_at"] = datetime.now().isoformat()
        
        start = datetime.fromisoformat(state["_efficiency"]["start_time"])
        duration = (datetime.now() - start).total_seconds()
        
        logger.info("=" * 50)
        logger.info("Pipeline Complete")
        logger.info(f"Final status: {state.get('status', 'unknown')}")
        logger.info(f"Efficiency: {state['_efficiency']['stages_run']} run, {state['_efficiency']['stages_skipped']} skipped, {duration:.1f}s")
        logger.info("=" * 50)
        
        return state


def run_pipeline() -> Dict[str, Any]:
    """Run the optimized pipeline"""
    graph = IntelligenceGraph()
    return graph.run()


def run_to(agent_name: str) -> Dict[str, Any]:
    """Run pipeline up to specific agent"""
    graph = IntelligenceGraph()
    state = create_initial_state()
    
    for name, agent_func in graph.nodes:
        if name == agent_name:
            break
        state = agent_func(state)
    
    return state
