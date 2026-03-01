#!/usr/bin/env python3
"""
LAGIS - Local Autonomous Geopolitical Intelligence System
Main entry point
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.interfaces.cli.cli import main

if __name__ == "__main__":
    main()
