# LAGIS - Telegram Service
# Handles Telegram bot for delivery and queries

import os
import logging
import threading
import requests
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger("LAGIS.Telegram")

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/{method}"


class TelegramService:
    """Telegram bot service for brief delivery and queries"""
    
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.token and self.chat_id)
        
        if self.enabled:
            logger.info("Telegram service enabled")
        else:
            logger.warning("Telegram not configured - set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
    
    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send message to configured chat"""
        if not self.enabled:
            logger.warning("Telegram not enabled, skipping send")
            return False
        
        url = TELEGRAM_API_URL.format(token=self.token, method="sendMessage")
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.ok:
                logger.info("Message sent successfully")
                return True
            else:
                logger.error(f"Failed to send: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False
    
    def send_brief(self, brief_text: str) -> bool:
        """Send daily brief to Telegram"""
        header = f"📊 *LAGIS Daily Brief*\n{datetime.now().strftime('%Y-%m-%d')}\n\n"
        return self.send_message(header + brief_text)
    
    def get_updates(self, offset: int = 0, timeout: int = 60) -> list:
        """Get updates from Telegram"""
        if not self.enabled:
            return []
        
        url = TELEGRAM_API_URL.format(token=self.token, method="getUpdates")
        payload = {"timeout": timeout, "offset": offset}
        
        try:
            response = requests.post(url, json=payload, timeout=timeout + 10)
            if response.ok:
                return response.json().get("result", [])
        except Exception as e:
            logger.error(f"Get updates error: {e}")
        return []


_telegram_service: Optional[TelegramService] = None


def get_telegram() -> TelegramService:
    global _telegram_service
    if _telegram_service is None:
        _telegram_service = TelegramService()
    return _telegram_service


class TelegramListener:
    """Background listener for Telegram commands"""
    
    def __init__(self):
        self.service = get_telegram()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.offset = 0
    
    def start(self):
        """Start listening for messages"""
        if not self.service.enabled:
            logger.warning("Telegram not configured, cannot start listener")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        logger.info("Telegram listener started")
    
    def stop(self):
        """Stop listening"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Telegram listener stopped")
    
    def _listen_loop(self):
        """Main listening loop"""
        while self.running:
            try:
                updates = self.service.get_updates(offset=self.offset, timeout=30)
                
                for update in updates:
                    self.offset = update.get("update_id", 0) + 1
                    message = update.get("message", {})
                    text = message.get("text", "")
                    chat_id = message.get("chat", {}).get("id")
                    
                    if text and chat_id:
                        self._handle_message(text, chat_id)
                        
            except Exception as e:
                logger.error(f"Listen error: {e}")
        
    def _handle_message(self, text: str, chat_id: str):
        """Handle incoming message"""
        from src.interfaces.cli.cli import CLI
        
        logger.info(f"Received: {text}")
        
        # Simple response - in production would be more sophisticated
        response = "Processing your query..."
        self.service.send_message(response)
        
        # Process query through CLI
        cli = CLI()
        try:
            # This would need modification to work without memory context
            result = f"Query received: {text}\n\nUse /brief for daily brief or /help for commands."
            self.service.send_message(result)
        except Exception as e:
            logger.error(f"Query error: {e}")
            self.service.send_message(f"Error: {str(e)}")


_telegram_listener: Optional[TelegramListener] = None


def get_telegram_listener() -> TelegramListener:
    global _telegram_listener
    if _telegram_listener is None:
        _telegram_listener = TelegramListener()
    return _telegram_listener
