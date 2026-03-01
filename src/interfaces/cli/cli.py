# LAGIS - CLI Interface with Scheduler Support

import sys
import json
import logging
from pathlib import Path

from src.orchestration.graph import run_pipeline
from src.core.memory.memory import get_memory
from src.core.llm.engine import get_llm
from src.core.scheduler.scheduler import get_scheduler


from src.core.config import LOGS_DIR

LOG_DIR = LOGS_DIR
LOG_DIR.mkdir(exist_ok=True)


def setup_logging():
    """Setup logging configuration"""
    log_file = LOG_DIR / f"lagis_{datetime.now().strftime('%Y%m%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("LAGIS")


from datetime import datetime


class CLI:
    """Interactive CLI for LAGIS"""
    
    def __init__(self):
        self.memory = get_memory()
        self.llm = get_llm()
        self.logger = setup_logging()
    
    def show_brief(self):
        brief = self.memory.get_latest_brief()
        if brief:
            print(brief.get("content", "No brief content"))
        else:
            print("No brief available. Run pipeline first.")
    
    def show_risk(self, country: str):
        trends = self.memory.get_risk_trend(country, 30)
        if not trends:
            print(f"No risk data for {country}")
            return
        
        print(f"\nRisk trend for {country}:")
        print("-" * 40)
        for t in trends:
            print(f"Date: {t.get('created_at', '')}")
            print(f"  Overall Risk: {t.get('overall_risk', 0):.1f}/10")
            print(f"  Trend: {t.get('trend', 'unknown')}")
    
    def show_events(self, limit: int = 20):
        events = self.memory.get_recent_events(limit)
        if not events:
            print("No events in database")
            return
        
        print(f"\nRecent Events:")
        print("-" * 40)
        for e in events:
            print(f"- {e.get('event_title', '')}")
            print(f"  Severity: {e.get('severity_score', 0)}/10")
    
    def show_logs(self, lines: int = 50):
        """Show recent log entries"""
        log_files = sorted(LOG_DIR.glob("lagis_*.log"), reverse=True)
        if not log_files:
            print("No logs available")
            return
        
        with open(log_files[0], 'r') as f:
            log_lines = f.readlines()[-lines:]
        print("".join(log_lines))
    
    def scheduler_status(self):
        """Show scheduler status"""
        scheduler = get_scheduler()
        status = scheduler.get_status()
        print(f"\nScheduler Status:")
        print("-" * 40)
        print(f"Running: {status['running']}")
        print(f"Scheduled Time: {status['scheduled_time']}")
        if status['next_run']:
            print(f"Next Run: {status['next_run']}")
    
    def query(self, question: str):
        brief = self.memory.get_latest_brief()
        events = self.memory.get_recent_events(20)
        
        context = []
        if brief:
            context.append(f"Latest Brief: {brief.get('content', '')[:500]}")
        if events:
            context.append(f"Recent Events: {json.dumps(events[:5], indent=2)}")
        
        prompt = f"""Based on the intelligence data:

{chr(10).join(context)}

Question: {question}

Provide a detailed answer:"""

        response = self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1024,
            system="You are a geopolitical intelligence analyst."
        )
        
        print(response)
    
    def run_interactive(self):
        print("LAGIS CLI - Type 'help' for commands\n")
        
        while True:
            try:
                cmd = input("> ").strip()
                
                if not cmd:
                    continue
                if cmd.lower() in ["exit", "quit", "q"]:
                    scheduler = get_scheduler()
                    scheduler.stop()
                    print("Goodbye!")
                    break
                if cmd.lower() == "help":
                    print("""
Commands:
  brief            - Show latest brief
  events [n]       - Show recent events (default 20)
  risk <country>   - Show risk trend for country
  query <q>        - Ask a question
  run              - Run pipeline
  scheduler start  - Start daily scheduler
  scheduler stop   - Stop scheduler
  scheduler status - Show scheduler status
  logs [n]         - Show recent logs (default 50)
  help             - Show this help
  exit             - Quit
""")
                    continue
                if cmd.lower() == "brief":
                    self.show_brief()
                    continue
                if cmd.lower().startswith("events"):
                    parts = cmd.split()
                    limit = int(parts[1]) if len(parts) > 1 else 20
                    self.show_events(limit)
                    continue
                if cmd.lower().startswith("risk "):
                    country = cmd[5:].strip()
                    self.show_risk(country)
                    continue
                if cmd.lower() == "run":
                    run_pipeline()
                    continue
                if cmd.lower() == "scheduler start":
                    scheduler = get_scheduler()
                    scheduler.start()
                    continue
                if cmd.lower() == "scheduler stop":
                    scheduler = get_scheduler()
                    scheduler.stop()
                    continue
                if cmd.lower() == "scheduler status":
                    self.scheduler_status()
                    continue
                if cmd.lower().startswith("logs"):
                    parts = cmd.split()
                    lines = int(parts[1]) if len(parts) > 1 else 50
                    self.show_logs(lines)
                    continue
                
                self.query(cmd)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="LAGIS CLI")
    parser.add_argument("command", nargs="?", help="Command to run")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--run", "-r", action="store_true", help="Run pipeline")
    parser.add_argument("--schedule", "-s", action="store_true", help="Start scheduler")
    
    args = parser.parse_args()
    
    cli = CLI()
    
    if args.schedule:
        scheduler = get_scheduler()
        scheduler.start()
        print("Scheduler started in background. Use 'python main.py -i' to interact.")
        return
    
    if args.interactive or not args.command:
        cli.run_interactive()
    elif args.command == "brief":
        cli.show_brief()
    elif args.command == "run" or args.run:
        run_pipeline()
    elif args.command == "scheduler":
        cli.scheduler_status()
    elif args.command == "logs":
        cli.show_logs()
    else:
        cli.query(args.command)


if __name__ == "__main__":
    main()
