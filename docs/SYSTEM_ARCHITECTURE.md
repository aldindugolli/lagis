# LAGIS - Local Autonomous Geopolitical Intelligence System

## System Architecture

### Overview
LAGIS is a fully local, autonomous multi-agent intelligence system that:
- Collects global news from RSS feeds
- Extracts structured geopolitical events
- Analyzes strategic implications
- Assesses country-level risk
- Generates executive intelligence briefs

### Core Components

```
src/
├── core/
│   ├── llm/engine.py       # Unified Ollama LLM wrapper
│   ├── memory/memory.py    # SQLite persistent memory
│   ├── scheduler/scheduler.py  # Daily execution scheduler
│   └── state/state.py      # Unified state object
├── agents/
│   ├── collector/          # RSS news collection
│   ├── extractor/          # Event extraction
│   ├── analyst/            # Strategic analysis
│   ├── risk/               # Country risk scoring
│   └── executive/          # Briefing generation
├── orchestration/graph.py   # LangGraph-style pipeline
└── interfaces/cli/          # Interactive CLI
```

### Agent Contract
Every agent exposes: `run(state: dict) -> dict`

### State Object
```python
{
    "date": "YYYY-MM-DD",
    "articles": [],
    "events": [],
    "analysis": [],
    "risk_scores": {},
    "brief": ""
}
```

### Models Used
- Reasoning: llama3.1:8b
- Embedding: nomic-embed-text

### Execution Flow
1. collect → extract → analyze → assess_risk → generate_brief

### Memory System
- SQLite database for persistent storage
- Stores articles, events, analysis, risk scores, briefs
- Enables historical queries and trend analysis
