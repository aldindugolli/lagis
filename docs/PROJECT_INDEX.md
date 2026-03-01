# Project Index

## Core Files
- main.py - Entry point
- config/settings.json - Configuration

## Source Code
- src/core/llm/engine.py - LLM wrapper
- src/core/memory/memory.py - SQLite memory
- src/core/state/state.py - State management
- src/core/scheduler/scheduler.py - Daily scheduler
- src/orchestration/graph.py - Pipeline orchestration
- src/interfaces/cli/cli.py - CLI interface

## Agents
- src/agents/collector/agent.py - News collection
- src/agents/extractor/agent.py - Event extraction
- src/agents/analyst/agent.py - Strategic analysis
- src/agents/risk/agent.py - Risk assessment
- src/agents/executive/agent.py - Brief generation

## Data
- data/lagis.db - SQLite database
- output/briefs/ - Generated briefings

## Documentation
- docs/SYSTEM_ARCHITECTURE.md
- docs/CURRENT_STATE.md
- docs/DECISIONS_LOG.md
- docs/NEXT_TASK.md

## Commands
```bash
python main.py run         # Execute pipeline
python main.py brief       # Show latest brief
python main.py -i         # Interactive mode
```
