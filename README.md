# LAGIS - Local Autonomous Geopolitical Intelligence System

A fully local, API-free multi-agent intelligence platform for geopolitical analysis with focus on Kosovo.

## Features

- **News Collection**: Aggregates global news from RSS feeds
- **Event Extraction**: Identifies and extracts geopolitical events
- **Risk Assessment**: Analyzes country risk levels
- **Kosovo Analysis**: Specialized analysis of Kosovo-related developments
- **Daily Briefs**: Automated daily intelligence briefings
- **Telegram Delivery**: Delivers briefs directly to Telegram
- **Interactive Query**: Natural language queries via CLI
- **Autonomous Scheduling**: Runs daily at 06:00 automatically
- **Docker Support**: Containerized deployment ready

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your Telegram credentials

# Run pipeline
python main.py run

# Interactive mode
python main.py -i

# Schedule daily execution
python main.py --schedule
```

## Configuration

Edit `.env` to configure:

| Variable | Description | Default |
|----------|-------------|---------|
| TG_TOKEN | Telegram bot token | - |
| TG_CHAT | Telegram chat ID | - |
| OLLAMA_URL | Ollama API URL | http://localhost:11434 |
| SCHEDULER_HOUR | Daily run hour (24h) | 6 |
| SCHEDULER_MINUTE | Daily run minute | 0 |
| MAX_ARTICLES | Articles to process | 10 |
| MAX_EVENTS | Events to extract | 5 |

## Docker Deployment

```bash
# Build container
docker build -t lagis .

# Run with docker-compose (recommended)
docker-compose up -d

# View logs
docker-compose logs -f
```

For Railway deployment, use `railway.json` configuration.

## Architecture

- **7-Agent Pipeline**: collector → extractor → geopolitical_analyst → kosovo_agent → risk_assessment → executive → telegram
- **Local LLM**: Uses Ollama for all AI processing
- **SQLite Memory**: Persistent storage for events and briefs
- **Cross-Platform**: Works on Windows, Linux, macOS
