# LAGIS — Local Autonomous Geopolitical Intelligence System

## SYSTEM IDENTITY

LAGIS is a fully local, API-free, autonomous geopolitical intelligence platform designed to continuously monitor global events and produce strategic intelligence analysis without reliance on cloud services.

The system operates using locally hosted Large Language Models and autonomous software agents.

Human interaction is supervisory only.

The system must remain operational across sessions, restarts, and context loss.

---

## PRIMARY OBJECTIVE

Transform unstructured global news into structured geopolitical intelligence.

Daily output must provide:

* Major global events
* Strategic geopolitical implications
* Country-level instability signals
* Escalation risks
* Economic and market impact indicators
* Executive decision-ready briefings

---

## DESIGN CONSTRAINTS

MANDATORY REQUIREMENTS:

* Fully local execution
* No paid APIs
* No external LLM providers
* Restart-safe architecture
* Persistent memory
* Autonomous execution capability
* Modular multi-agent design
* Context-window independent operation

---

## CURRENT DEVELOPMENT STAGE

STATUS: FUNCTIONAL PROOF-OF-CONCEPT

### Operational Components

Pipeline: OPERATIONAL
Memory: SQLite persistence enabled
LLM: llama3.1:8b via Ollama
Embeddings: nomic-embed-text
CLI Interface: Functional

---

## SYSTEM ARCHITECTURE

Execution Model:
Sequential multi-agent pipeline using shared state propagation.

Pipeline Flow:

collector_agent
↓
extractor_agent
↓
analyst_agent
↓
risk_agent
↓
executive_agent

Each agent receives structured state input and produces enriched output for the next agent.

---

## AGENT RESPONSIBILITIES

### 1. Collector Agent

Sources geopolitical news via RSS feeds.

Responsibilities:

* Poll trusted global news feeds
* Normalize article metadata
* Store raw articles

Current Sources:
Reuters
BBC
Al Jazeera

Future Target:
20+ global sources.

---

### 2. Extractor Agent

Transforms articles into structured geopolitical events.

Outputs:

* Countries involved
* Actors
* Event category
* Timestamp
* Confidence score

---

### 3. Analyst Agent

Evaluates strategic implications.

Tasks:

* Identify geopolitical consequences
* Detect alliance shifts
* Assess escalation signals
* Determine regional impact

---

### 4. Risk Agent

Calculates country-level instability metrics.

Example dimensions:

* Political instability
* Military escalation risk
* Economic stress
* Diplomatic tension

Produces daily risk scores.

---

### 5. Executive Agent

Generates executive intelligence brief.

Output format:
GLOBAL STRATEGIC BRIEF

* Top Events
* Escalation Risks
* Market Implications
* Strategic Outlook
* Confidence Assessment

---

## LLM ACCESS LAYER

All model interaction occurs through:

src/core/llm/engine.py

This file acts as the single abstraction layer for:

* text generation
* summarization
* analysis
* embedding creation

No agent may directly call the LLM outside this layer.

---

## MEMORY SYSTEM

Persistent storage:

SQLite database.

Stored Data:

* Articles
* Extracted events
* Risk scores
* Generated briefs
* Embeddings

Vector similarity enables historical recall.

---

## USER INTERFACE

CLI Commands:

python main.py run
Executes full intelligence pipeline.

python main.py brief
Displays latest executive brief.

python main.py -i
Interactive intelligence mode.

---

## AUTONOMY TARGET STATE

LAGIS must evolve toward:

* Scheduled daily execution
* Continuous ingestion
* Self-monitoring health checks
* Automated logging
* Failure recovery
* Minimal human operation

---

## NEXT DEVELOPMENT PRIORITIES

1. Scheduler for autonomous daily execution
2. System-wide logging framework
3. Expand RSS ingestion sources
4. Market Correlation Agent
5. Context self-management layer
6. Long-term trend analysis

---

## ENGINEERING RULES FOR FUTURE AI AGENTS

Any AI modifying this system must:

* Preserve modular agent boundaries
* Maintain local-first philosophy
* Avoid unnecessary dependencies
* Update documentation after changes
* Ensure restart continuity
* Prefer incremental evolution over rewrites

---

## SUCCESS CONDITION

LAGIS operates continuously and autonomously, producing daily geopolitical intelligence briefs with improving analytical quality over time.

System development must remain sustainable beyond individual AI sessions or context limits.
