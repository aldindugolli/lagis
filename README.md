# LAGIS - Local AI Geopolitical Intelligence System

A fully local, API-free multi-agent intelligence platform that collects global news, extracts geopolitical events, detects early signals, predicts escalation scenarios, and delivers daily briefs via Telegram.

**Runtime:** ~42 seconds | **No LLM required** | **Pure Python**

---

## Features

- **Real-time News Collection** - RSS feeds from 30+ global sources
- **Early Signal Detection** - Statistical spike detection in geopolitical signals
- **Black Swan Anomaly Detection** - Identifies rare, low-frequency, high-impact anomalies
- **Scenario Generation** - Rule-based probabilistic scenario prediction
- **Geopolitical Memory Graph** - Persistent relationship tracking between actors
- **Self-Learning Loop** - Tracks prediction accuracy and adjusts models
- **Strategic Recommendations** - Actionable intelligence for decision-makers
- **Telegram Delivery** - Daily briefs delivered to mobile

---

## Architecture

```
Pipeline (16 stages, ~42s):
┌─────────────────────────────────────────────────────────────────────────┐
│ collect_feeds → archive → article_filter → early_signal → black_swan   │
│       ↓                                                               │
│ quick_analysis → scenario_engine → signal_detection → context_retrieval │
│       ↓                                                               │
│ embed_events → memory_graph → intelligence_synthesis → kosovo_impact   │
│       ↓                                                               │
│ learning_loop → strategy → generate_brief → Telegram                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Agents

| Agent | Purpose | Runtime |
|-------|---------|---------|
| `collector` | Fetches RSS feeds in parallel | ~8s |
| `archive` | Stores articles for historical analysis | <1s |
| `filter` | Extracts geopolitically relevant articles | <1s |
| `early_signal` | Detects signal spikes vs historical baseline | <1s |
| `black_swan` | Identifies rare anomalies nobody sees | <1s |
| `quick_analysis` | Rule-based event extraction | <1s |
| `scenario_engine` | Generates probabilistic scenarios | <1s |
| `signals` | Signal aggregation | <1s |
| `context` | Retrieves relevant historical context | <1s |
| `knowledge` | Vector embedding storage | ~100ms |
| `memory_graph` | Actor relationship tracking | <1s |
| `synthesis` | Strategic intelligence analysis | <1s |
| `learning_loop` | Prediction tracking & model adjustment | <1s |
| `strategy` | Generates actionable recommendations | <1s |
| `brief` | Formats and sends Telegram message | ~2s |

---

## Data Storage

| File | Purpose |
|------|---------|
| `data/articles.json` | Article archive |
| `data/signals_history.json` | 7-day signal history |
| `data/memory_graph.json` | Actor relationships (nodes/edges) |
| `data/memory_graph.gexf` | Gephi-compatible visualization |
| `data/predictions_history.json` | Prediction tracking |
| `data/system_metrics.json` | Accuracy metrics |
| `data/anomaly_history.json` | Black swan alert history |
| `data/knowledge.db` | Vector embeddings |
| `data/lagis.db` | Events, risks, briefs |

---

## Memory Graph Structure

```json
{
  "nodes": {
    "Iran": {"type": "country", "risk_score": 9, "last_updated": "2026-04-05"},
    "Hezbollah": {"type": "organization", "risk_score": 7}
  },
  "edges": [
    {"from": "Iran", "to": "Hezbollah", "type": "supports", "weight": 0.9,
     "first_seen": "2026-04-01", "last_seen": "2026-04-05", "frequency": 12}
  ]
}
```

**Edge Types:** `conflict`, `allied_with`, `supports`, `sanctions`, `trades_with`, `proxy_of`, `nuclear_risk`, `energy_dependency`

---

## Black Swan Detection Types

| Type | Trigger |
|------|---------|
| **Signal Anomaly** | >2.5x spike in normally low-frequency category |
| **Rare Actor Combination** | Actors with weak edge weight (<0.3) appearing together |
| **Cascading Signals** | 3+ categories spiking simultaneously |
| **Edge Surge** | Conflict intensity >0.8 |
| **Silence Anomaly** | Active region suddenly quiet |
| **Regional Concentration** | >60% events in single theater |

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure Telegram (optional)
cp .env.example .env
# Edit .env with your Telegram bot token and chat ID

# Run pipeline
python main.py run

# Interactive query mode
python main.py -i
```

---

## Configuration

### RSS Feeds
Edit `src/core/config.py` to add/remove feeds:

```python
RSS_FEEDS = [
    {"name": "Reuters World", "url": "https://feeds.reuters.com/reuters/worldnews"},
    {"name": "BBC World", "url": "https.feeds.bbci.co.uk/news/world/rss.xml"},
    # Add more feeds...
]
```

### Telegram
Set environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### Key Thresholds

| Agent | Parameter | Default |
|-------|-----------|---------|
| early_signal | SPIKE_THRESHOLD | 1.8 |
| early_signal | MIN_SPIKE_COUNT | 5 |
| black_swan | signal_spike_ratio | 2.5 |
| black_swan | weak_edge_weight | 0.3 |
| memory_graph | Edge decay | 0.01/day |
| learning | Correct HIGH score | +2 |

---

## Sample Output

```
============================================================
GLOBAL STRATEGIC BRIEFING
Date: 2026-04-05
============================================================

EXECUTIVE SUMMARY
Tensions elevated with 2 significant events. Countries of interest: Iran, Israel.

STRATEGIC IMPLICATIONS
----------------------------------------
  - Regional Conflict: Iran-Israel tensions could spread to Lebanon/Syria
  - Superpower Involvement: US direct involvement raises stakes

RELATIONSHIP INSIGHTS:
  - Iran maintains strong supports relationship with Hezbollah (weight: 0.95)
  - Iran has high-intensity conflict with Israel (weight: 1.0)

ESCALATION OUTLOOK
----------------------------------------
  - Direct Conflict: HIGH
  - Proxy Escalation: HIGH
  - US Involvement: HIGH
  - Energy Supply: LOW

⚠️ BLACK SWAN ALERTS
----------------------------------------
  [HIGH] Silence Anomaly
    Anomalous silence: Iran suddenly inactive despite 27.0 avg signals
    → Possible information suppression or pre-event calm

SCENARIO OUTLOOK
----------------------------------------
  - Iran retaliates via proxy forces
    Probability: HIGH | Timeframe: 24-72h
    Impact: Regional instability increases

🎯 STRATEGIC RECOMMENDATIONS
----------------------------------------
  - IMMEDIATE: Increase surveillance of Iran communications due to abnormal silence
  - URGENT: Monitor Hezbollah activity for indicators of Iran-directed retaliation
  - URGENT: Monitor IRGC positioning and regional force deployments

INTELLIGENCE CONFIDENCE
----------------------------------------
  - Prediction Accuracy: 100%
  - System Confidence: Developing
  - Track Record: 4 predictions (0 pending)

GLOBAL STABILITY INDEX: 5.9/10
Trend: Deteriorating
============================================================
```

---

## Extending LAGIS

### Add New Agent
1. Create `src/agents/<agent_name>/agent.py`
2. Implement `run(state: Dict) -> Dict`:
```python
def run(state: Dict[str, Any]) -> Dict[str, Any]:
    # Process state
    state["new_data"] = process(state.get("input_data"))
    return state
```
3. Add to `src/orchestration/graph.py`:
```python
from src.agents.<agent_name>.agent import run as <name>_run

# Add to nodes list:
("<agent_name>", <name>_run),
```

### Add Relationship Type
Edit `src/agents/memory_graph/agent.py`:
```python
RELATIONSHIP_RULES = {
    "new_type": ["keyword1", "keyword2"],
    # ...
}
```

### Add Scenario Template
Edit `src/agents/scenario_engine/agent.py`:
```python
TEMPLATES = [
    {
        "pattern": ["keyword1", "keyword2"],
        "title": "Scenario title",
        "actors": ["Actor1", "Actor2"],
        "description": "What happens...",
        "impact": ["Impact 1", "Impact 2"]
    },
    # ...
]
```

### Add Black Swan Detection
Edit `src/agents/black_swan/agent.py`:
```python
def _detect_your_anomaly(self, ...) -> Optional[Dict]:
    if condition_met:
        return self._create_anomaly(
            "Your Anomaly Type",
            "Description of the anomaly",
            ["Actor1", "Actor2"],
            rarity=4, magnitude=4, cross_confirm=2
        )
    return None
```

---

## Performance

| Metric | Target | Actual |
|--------|--------|--------|
| Pipeline Runtime | <45s | ~42s |
| Memory Graph Update | <5ms | <1ms |
| Scenario Generation | <5ms | <1ms |
| Prediction Resolution | <5ms | <1ms |

---

## Project Structure

```
GeoIntelOpenCode/
├── main.py                 # Entry point
├── src/
│   ├── agents/             # All pipeline agents
│   │   ├── archive/
│   │   ├── black_swan/
│   │   ├── brief/
│   │   ├── collector/
│   │   ├── context/
│   │   ├── early_signal/
│   │   ├── filter/
│   │   ├── intelligence_synthesis/
│   │   ├── knowledge/
│   │   ├── kosovo/
│   │   ├── learning_loop/
│   │   ├── memory_graph/
│   │   ├── quick_analysis/
│   │   ├── scenario_engine/
│   │   ├── signals/
│   │   └── strategy/
│   ├── core/
│   │   ├── config.py
│   │   ├── memory/
│   │   └── state/
│   ├── interfaces/
│   │   └── telegram_sender.py
│   └── orchestration/
│       └── graph.py        # Pipeline definition
├── data/                   # All persistent data
├── output/
│   └── briefs/             # Generated briefs
└── requirements.txt
```

---

## Docker Deployment

```bash
# Build container
docker build -t lagis .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## Development Status

- [x] Core pipeline (16 stages)
- [x] Memory graph with relationships
- [x] Black swan anomaly detection
- [x] Self-learning prediction loop
- [x] Strategic recommendations
- [x] Telegram delivery
- [x] GEXF export for visualization
- [ ] Web dashboard
- [ ] API endpoint
- [ ] Multi-language support

---

## License

MIT
