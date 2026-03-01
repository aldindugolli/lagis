# LAGIS - Configuration Module
# Centralized configuration for cross-platform compatibility

import os
from pathlib import Path

# Base directory - use current working directory
BASE_DIR = Path.cwd()

# Data directories
DATA_DIR = BASE_DIR / "data"
MEMORY_DIR = BASE_DIR / "memory"
LOGS_DIR = BASE_DIR / "logs"
OUTPUT_DIR = BASE_DIR / "output"
CONFIG_DIR = BASE_DIR / "config"
DOCS_DIR = BASE_DIR / "docs"

# Ensure directories exist
for directory in [DATA_DIR, MEMORY_DIR, LOGS_DIR, OUTPUT_DIR, CONFIG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database path
DATABASE_PATH = DATA_DIR / "lagis.db"
KNOWLEDGE_DB_PATH = DATA_DIR / "knowledge.db"

# Output paths
BRIEFS_DIR = OUTPUT_DIR / "briefs"
BRIEFS_DIR.mkdir(parents=True, exist_ok=True)

# Archive paths
ARCHIVE_DIR = DATA_DIR / "archive"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Config paths
SETTINGS_PATH = CONFIG_DIR / "settings.json"
ENV_PATH = BASE_DIR / ".env"

# Scheduler settings
SCHEDULER_HOUR = int(os.environ.get("SCHEDULER_HOUR", "6"))
SCHEDULER_MINUTE = int(os.environ.get("SCHEDULER_MINUTE", "0"))

# Get Telegram credentials from environment
TELEGRAM_TOKEN = os.environ.get("TG_TOKEN", "")
TELEGRAM_CHAT = os.environ.get("TG_CHAT", "")
TELEGRAM_ENABLED = bool(TELEGRAM_TOKEN and TELEGRAM_CHAT)

# LLM settings
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

# Agent settings
MAX_ARTICLES = int(os.environ.get("MAX_ARTICLES", "10"))
MAX_EVENTS = int(os.environ.get("MAX_EVENTS", "5"))
