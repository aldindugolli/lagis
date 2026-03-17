# LAGIS - Telegram Service
# Handles Telegram bot for delivery and queries

import os
import re
import logging
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError
from typing import Optional

logger = logging.getLogger("LAGIS.Telegram")

load_dotenv()

MARKDOWN_CHARS = r'[*_`\[\](){}|>_~]'

MAX_MESSAGE_LENGTH = 4000


def sanitize_for_telegram(text: str) -> str:
    """Remove/escape Markdown characters to prevent parsing errors"""
    text = re.sub(MARKDOWN_CHARS, '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


def chunk_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list:
    """Split large messages into chunks"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    lines = text.split('\n')
    current = []
    current_len = 0
    
    for line in lines:
        line_len = len(line) + 1
        if current_len + line_len > max_length:
            if current:
                chunks.append('\n'.join(current))
                current = []
                current_len = 0
        current.append(line)
        current_len += line_len
    
    if current:
        chunks.append('\n'.join(current))
    
    return chunks


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
    
    def send_message(self, text: str, parse_mode: str = None) -> bool:
        """Send message to configured chat - no Markdown parsing"""
        if not self.enabled or not self.bot:
            logger.warning("Telegram not enabled, skipping send")
            return False
        
        text = sanitize_for_telegram(text)
        
        chunks = chunk_message(text)
        
        try:
            import requests
            for i, chunk in enumerate(chunks):
                url = f"https://api.telegram.org/bot{self.token}/sendMessage"
                payload = {
                    "chat_id": self.chat_id,
                    "text": chunk
                }
                
                response = requests.post(url, json=payload, timeout=30)
                
                if not response.ok:
                    logger.error(f"Telegram error (chunk {i+1}): {response.text}")
                    return False
                
                if len(chunks) > 1:
                    logger.info(f"Sent chunk {i+1}/{len(chunks)}")
            
            logger.info(f"Message sent successfully ({len(chunks)} chunks)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send: {e}")
            return False
    
    def send_brief(self, brief_text: str) -> bool:
        """Send daily brief to Telegram"""
        header = "[REPORT] LAGIS Daily Brief\n\n"
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
