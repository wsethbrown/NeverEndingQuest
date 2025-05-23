"""
Debug configuration for DungeonMasterAI
Controls what debug messages are shown and logged
"""

# Debug categories - set to True to enable, False to disable
DEBUG_CATEGORIES = {
    # Critical errors only
    "errors": True,
    
    # Campaign/path management
    "campaign_loading": False,  # "CampaignPathManager loaded campaign..."
    
    # File operations
    "file_operations": True,    # File read/write errors
    "file_success": False,      # Successful file operations
    
    # Conversation/summary management
    "conversation_cleanup": False,  # "System messages removed...", "Lightweight chat..."
    "summary_building": True,       # Summary generation progress
    "summary_details": False,       # Detailed summary operations
    
    # Game mechanics
    "location_transitions": True,   # Location change events
    "plot_updates": True,          # Plot progression
    "validation": False,           # "Validation passed successfully"
    "time_updates": False,         # Time passage logs
    
    # Character/inventory
    "character_updates": True,     # Player/NPC changes
    "inventory_changes": True,     # Item additions/removals
    
    # Combat
    "combat_events": True,         # Combat initialization and results
    
    # Verbose/detailed logs
    "hex_strings": False,          # Location hex representations
    "schema_processing": False,    # Schema validation details
    "attempt_counts": False,       # "Successfully on attempt X"
}

# Log file settings
ERROR_LOG_FILE = "game_errors.log"
DEBUG_LOG_FILE = "game_debug.log"
MAX_LOG_SIZE_MB = 10  # Rotate logs when they exceed this size

# Message filters - messages containing these strings will be filtered out
FILTER_PATTERNS = [
    "load_ssl_context",
    "httpx",
    "httpcore",
    "receive_response_body",
    "HTTP Request:",
    "Lightweight chat history updated",
    "System messages removed:",
    "User messages:",
    "Assistant messages:",
]

def should_log_message(message: str, category: str = None) -> bool:
    """Determine if a message should be logged based on configuration"""
    # Filter out patterns
    for pattern in FILTER_PATTERNS:
        if pattern in message:
            return False
    
    # Check category if provided
    if category:
        return DEBUG_CATEGORIES.get(category, True)
    
    # Default to logging if no category specified
    return True

def get_log_level_from_message(message: str) -> str:
    """Determine log level from message content"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["error", "failed", "exception"]):
        return "ERROR"
    elif any(word in message_lower for word in ["warning", "warn"]):
        return "WARNING"
    elif "debug:" in message_lower:
        return "DEBUG"
    else:
        return "INFO"