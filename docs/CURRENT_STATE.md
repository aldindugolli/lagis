# Current System State

## Last Updated
2026-02-27

## Status
| Component | Status | Notes |
|-----------|--------|-------|
| Pipeline | OPERATIONAL | 7 agents |
| Scheduler | ACTIVE | Daily at 06:00 |
| Logging | ENABLED | logs/ directory |
| Database | INITIALIZED | SQLite |
| Telegram | CONFIGURED | Auto-delivery enabled |

## Pipeline (7 Agents)
1. collector - RSS feeds (30 sources)
2. extractor - Event extraction
3. analyst - Strategic analysis
4. risk - Country risk scoring
5. market - Market correlation
6. kosovo - Kosovo impact analysis
7. executive - Brief generation + Telegram delivery

## Telegram Integration
- **Bot**: Configured via .env
- **Features**: Daily brief delivery, query interface
- **Commands**: /brief, /help, /status

## New Features
- Kosovo Impact Agent: Analyzes events relevant to Kosovo/Balkans
- Telegram Delivery: Auto-sends brief after generation
- Query Agent: Interactive questions via memory + LLM

## Configuration (.env)
```
TG_TOKEN=8774187453:AAHc6D4kAM_kV0-MVFCqTWbcR-hAnfMHjNs
TG_CHAT=7939198610
```

## Usage
```bash
python main.py run      # Execute pipeline + Telegram brief
python main.py brief    # Show latest brief
python main.py -s       # Start scheduler (sends daily at 06:00)
```

## Data Storage
- Database: data/lagis.db
- Briefs: output/briefs/
- Logs: logs/
- Config: config/settings.json, .env
