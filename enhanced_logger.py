"""
Enhanced logging system for DungeonMasterAI
Provides cleaner console output and detailed file logging
"""

import logging
import sys
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from debug_config import *

class CategoryFilter(logging.Filter):
    """Filter logs based on debug categories"""
    def filter(self, record):
        # Check if message should be logged
        return should_log_message(record.getMessage(), getattr(record, 'category', None))

class CleanConsoleFormatter(logging.Formatter):
    """Simplified formatter for console output"""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Skip certain verbose messages
        msg = record.getMessage()
        
        # Simplify campaign loading messages
        if "CampaignPathManager loaded campaign" in msg:
            return None  # Skip these entirely
            
        # Simplify file operation messages
        if "Successfully updated" in msg and "attempt" in msg:
            # Extract just the important part
            parts = msg.split(" on attempt")
            return f"✓ {parts[0]}"
            
        # Format time updates more concisely
        if "Current Time:" in msg and "Time Advanced:" in msg:
            parts = msg.split(", ")
            new_time = parts[2].split(": ")[1] if len(parts) > 2 else "Unknown"
            return f"⏰ {new_time}"
            
        # Simplify validation messages
        if "Validation passed successfully" in msg:
            return "✓ Response validated"
            
        # Format location transitions
        if "Transitioning from" in msg:
            parts = msg.split("'")
            if len(parts) >= 4:
                return f"📍 {parts[1]} → {parts[3]}"
                
        # Format errors with color
        levelname = record.levelname
        if levelname in self.COLORS:
            color = self.COLORS[levelname]
            
            # Special formatting for errors
            if levelname == 'ERROR':
                return f"{color}❌ {msg}{self.RESET}"
            elif levelname == 'WARNING':
                return f"{color}⚠️  {msg}{self.RESET}"
            else:
                return msg
                
        return msg

class GameLogger:
    """Main logger class for the game"""
    
    def __init__(self):
        self.logger = logging.getLogger('DungeonMasterAI')
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Console handler with clean formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(CleanConsoleFormatter())
        console_handler.addFilter(CategoryFilter())
        self.logger.addHandler(console_handler)
        
        # Error file handler
        error_handler = RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
            backupCount=3
        )
        error_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        error_handler.setLevel(logging.WARNING)
        self.logger.addHandler(error_handler)
        
        # Debug file handler (everything)
        debug_handler = RotatingFileHandler(
            DEBUG_LOG_FILE,
            maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
            backupCount=3
        )
        debug_handler.setFormatter(error_formatter)
        debug_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(debug_handler)
    
    def debug(self, message, category=None):
        """Log debug message with optional category"""
        record = self.logger.makeRecord(
            self.logger.name, logging.DEBUG, "", 0, message, [], None
        )
        if category:
            record.category = category
        self.logger.handle(record)
    
    def info(self, message, category=None):
        """Log info message with optional category"""
        record = self.logger.makeRecord(
            self.logger.name, logging.INFO, "", 0, message, [], None
        )
        if category:
            record.category = category
        self.logger.handle(record)
    
    def warning(self, message, category=None):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message, exception=None, category=None):
        """Log error message with optional exception"""
        if exception:
            self.logger.error(f"{message}: {str(exception)}")
        else:
            self.logger.error(message)
    
    def game_event(self, event_type, details):
        """Log a game event in a structured way"""
        if event_type == "location_transition":
            self.info(f"📍 {details['from']} → {details['to']}", category="location_transitions")
        elif event_type == "plot_update":
            self.info(f"📖 Plot: {details['plot_id']} - {details['status']}", category="plot_updates")
        elif event_type == "inventory_change":
            self.info(f"🎒 {details['action']}: {details['item']}", category="inventory_changes")
        elif event_type == "character_update":
            self.info(f"👤 {details['character']}: {details['change']}", category="character_updates")
        elif event_type == "combat_start":
            self.info(f"⚔️ Combat: {details['enemies']}", category="combat_events")
        else:
            self.info(f"{event_type}: {details}")

# Global logger instance
game_logger = GameLogger()

# Convenience functions
def debug(message, category=None):
    game_logger.debug(message, category)

def info(message, category=None):
    game_logger.info(message, category)

def warning(message):
    game_logger.warning(message)

def error(message, exception=None):
    game_logger.error(message, exception)

def game_event(event_type, details):
    game_logger.game_event(event_type, details)