# LAGIS - Research Director Agent
# Generates autonomous intelligence questions and research tasks

import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from src.core.llm.engine import get_llm
from src.core.world_model.engine import get_world_model
from src.orchestration.utils import skip_stage

logger = logging.getLogger("LAGIS.Research")


class ResearchDirectorAgent:
    """Generates autonomous research questions"""
    
    def __init__(self):
        self.llm = get_llm()
        self.world_model = get_world_model()
    
    def _identify_intelligence_gaps(self, events: List[Dict], risks: Dict) -> List[str]:
        """Identify gaps in current intelligence"""
        gaps = []
        
        high_risk_countries = [c for c, r in risks.items() if r.get('overall_risk_score', 0) > 6]
        if high_risk_countries:
            gaps.append(f"What are the underlying drivers of instability in {', '.join(high_risk_countries[:3])}?")
        
        events_by_type = {}
        for e in events:
            t = e.get('event_type', 'unknown')
            events_by_type[t] = events_by_type.get(t, 0) + 1
        
        if events_by_type.get('military', 0) > 3:
            gaps.append("What military buildups or posture changes are anticipated in the next 90 days?")
        
        if events_by_type.get('diplomatic', 0) > 2:
            gaps.append("What diplomatic initiatives could de-escalate current tensions?")
        
        return gaps
    
    def _generate_strategic_questions(self, events: List[Dict], world_summary: str) -> List[str]:
        """Generate strategic research questions"""
        events_text = "\n".join([
            f"- {e.get('event_title', '')}" for e in events[:10]
        ])
        
        prompt = f"""Based on today's events and world state, generate 3-5 strategic intelligence questions that require deeper investigation.

TODAY'S EVENTS:
{events_text}

WORLD STATE:
{world_summary}

Format as JSON array of questions. Focus on:
- Emerging threats
- Strategic opportunities
- Long-term implications
- Intelligence gaps"""

        try:
            result = self.llm.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=512,
                system="You are a research director generating intelligence questions."
            )
            
            questions = json.loads(result) if result.startswith('[') else []
            return questions
        except Exception as e:
            logger.warning(f"Failed to generate questions: {e}")
            return []
    
    def _should_run_research(self, risk_scores: Dict) -> bool:
        """Only run research director when there are high-risk countries"""
        high_risk_count = len([r for r in risk_scores.values() if r.get('overall_risk_score', 0) >= 6])
        return high_risk_count >= 2
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research direction (conditional)"""
        events = state.get("events", [])
        risk_scores = state.get("risk_scores", {})
        
        if not events:
            logger.info("Skipping research: No events")
            state["research_tasks"] = []
            return state
        
        if not self._should_run_research(risk_scores):
            high_risk = len([r for r in risk_scores.values() if r.get('overall_risk_score', 0) >= 6])
            logger.info(f"Skipping research: Only {high_risk} high-risk countries (threshold: 2)")
            skip_stage(state, f"low_risk ({high_risk} countries)")
            state["research_tasks"] = []
            return state
        
        gaps = self._identify_intelligence_gaps(events, risk_scores)
        
        world_summary = self.world_model.get_world_summary()
        
        strategic_questions = self._generate_strategic_questions(events, world_summary)
        
        all_questions = gaps + strategic_questions
        
        research_tasks = []
        for q in all_questions[:5]:
            task_id = self.world_model.add_research_task(q, priority="medium")
            research_tasks.append({"question": q, "task_id": task_id})
        
        state["research_tasks"] = research_tasks
        state["status"] = "research_directed"
        
        logger.info(f"Research Director generated {len(research_tasks)} research questions")
        
        return state


def run(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = ResearchDirectorAgent()
    return agent.run(state)
