# LAGIS - Telegram Service
# Handles Telegram bot for delivery and queries

import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError
from typing import Optional

logger = logging.getLogger("LAGIS.Telegram")

# Load environment variables
load_dotenv()


class TelegramService:
    """Telegram bot service for brief delivery and queries"""
    
    def __init__(self):
        self.token = os.getenv("TG_TOKEN")
        self.chat_id = os.getenv("TG_CHAT")
        self.enabled = bool(self.token and self.chat_id)
        self.bot = Bot(token=self.token) if self.enabled else None
        
        if self.enabled:
            logger.info("Telegram service enabled")
        else:
            logger.warning("Telegram not configured - set TG_TOKEN and TG_CHAT in .env")
    
    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send message to configured chat"""
        if not self.enabled or not self.bot:
            logger.warning("Telegram not enabled, skipping send")
            return False
        
        try:
            # Use synchronous request
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            import requests
            response = requests.post(url, json={
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }, timeout=30)
            
            if response.ok:
                logger.info("Message sent successfully")
                return True
            else:
                logger.error(f"Telegram error: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to send: {e}")
            return False
    
    def send_brief(self, brief_text: str) -> bool:
        """Send daily brief to Telegram"""
        header = f"📊 *LAGIS Daily Brief*\n"
        return self.send_message(header + brief_text)


_telegram_service: Optional[TelegramService] = None


def get_telegram() -> TelegramService:
    global _telegram_service
    if _telegram_service is None:
        _telegram_service = TelegramService()
    return _telegram_service


def send_telegram_message(text: str) -> bool:
    """Quick send function"""
    service = get_telegram()
    return service.send_message(text)
