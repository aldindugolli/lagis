# LAGIS - APScheduler-based Daily Pipeline Scheduler
# Reliable autonomous execution with persistence

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from src.orchestration.graph import run_pipeline
from src.core.memory.memory import get_memory
from src.core.config import LOGS_DIR, SCHEDULER_HOUR, SCHEDULER_MINUTE


def setup_logging():
    """Setup logging configuration"""
    LOG_DIR = LOGS_DIR
    LOG_DIR.mkdir(exist_ok=True)
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


logger = setup_logging()


def run_daily_pipeline():
    """Execute the daily intelligence pipeline"""
    logger.info("=" * 50)
    logger.info("SCHEDULED PIPELINE EXECUTION STARTED")
    logger.info("=" * 50)
    
    try:
        result = run_pipeline()
        status = result.get('status', 'unknown')
        logger.info(f"Pipeline completed with status: {status}")
        
        memory = get_memory()
        memory.store_brief({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "content": f"Scheduled run - Status: {status}",
            "top_events": [],
            "escalation_risks": []
        })
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise


def job_executed(event):
    """Log job execution events"""
    if event.exception:
        logger.error(f"Job {event.job_id} failed with exception: {event.exception}")
    else:
        logger.info(f"Job {event.job_id} completed successfully")


class Scheduler:
    """APScheduler-based daily pipeline scheduler"""
    
    def __init__(self, hour: int = None, minute: int = None):
        self.hour = hour if hour is not None else SCHEDULER_HOUR
        self.minute = minute if minute is not None else SCHEDULER_MINUTE
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.running = False
        
        logger.info(f"Scheduler configured for {self.hour:02d}:{self.minute:02d} daily")
    
    def start(self):
        """Start the scheduler"""
        if not self.running:
            trigger = CronTrigger(
                hour=self.hour,
                minute=self.minute,
                second=0
            )
            
            self.scheduler.add_job(
                run_daily_pipeline,
                trigger=trigger,
                id='daily_pipeline',
                name='Daily Intelligence Pipeline',
                replace_existing=True
            )
            
            self.scheduler.start()
            self.running = True
            logger.info(f"Scheduler started - will run daily at {self.hour:02d}:{self.minute:02d}")
            
            logger.info("Running initial pipeline execution...")
            run_daily_pipeline()
    
    def stop(self):
        """Stop the scheduler"""
        if self.running:
            self.scheduler.shutdown(wait=True)
            self.running = False
            logger.info("Scheduler stopped")
    
    def run_now(self):
        """Run pipeline immediately"""
        logger.info("Manual pipeline execution triggered")
        return run_daily_pipeline()
    
    def get_status(self) -> dict:
        """Get scheduler status"""
        job = self.scheduler.get_job('daily_pipeline')
        next_run = job.next_run_time.isoformat() if job and job.next_run_time else None
        
        return {
            "running": self.running,
            "scheduled_time": f"{self.hour:02d}:{self.minute:02d}",
            "next_run": next_run
        }


_scheduler: Optional[Scheduler] = None


def get_scheduler(hour: int = None, minute: int = None) -> Scheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler(hour=hour, minute=minute)
    return _scheduler
