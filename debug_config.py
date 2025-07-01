"""
Debug configuration for DungeonMasterAI
Controls what debug messages are shown and logged
"""

# Debug categories - set to True to enable, False to disable
DEBUG_CATEGORIES = {
    # Critical errors only
    "errors": True,
    
    # Module/path management
    "module_loading": False,  # "ModulePathManager loaded module..."
    
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
    
    # Script-specific debug categories (used in enhanced_logger migration)
    "session_management": True,     # Session startup/shutdown, return message injection
    "narrative_generation": True,   # AI narrative generation for transitions
    "npc_management": True,         # NPC loading, validation, updates
    "ai_validation": True,          # AI response validation, retry logic
    "module_management": True,      # Module loading, transitions, completion checks
    "conversation_management": True, # Conversation history updates, compression
    "level_up": True,              # Level up sessions and processing
    "startup": True,               # Game startup, wizard, initialization
    "xp_tracking": True,           # Experience point awards and tracking
    "encounter_setup": True,       # Encounter initialization, creature setup
    "encounter_management": True,  # Encounter updates during combat
    "character_validation": True,  # Character data validation, corrections
    "ai_processing": True,         # AI API calls, response processing
    "testing": True,               # Test function debug output
    "save_game": True,             # Save/restore operations
    "module_transitions": True,    # Cross-module movement and summaries
    "storage_operations": True,    # Player storage system operations
    "combat_validation": True,     # Combat response validation, rule checking
    "combat_logs": True,           # Combat logging and summary generation
    "subprocess_output": True,     # Output from subprocess calls
    "combat_processing": True,     # Combat encounter creation and updates
    "party_management": True,      # Party tracker updates
    
    # Legacy categories (kept for backward compatibility)
    "main_debug": False,
    "action_handler_debug": False,
    "character_updater_debug": False,
    "combat_manager_debug": False,
    "save_manager_debug": False,
    "path_manager_debug": False,
    "campaign_manager_debug": False,
    "location_manager_debug": False,
    "storage_manager_debug": False
}

# Log file settings
ERROR_LOG_FILE = "modules/logs/game_errors.log"
DEBUG_LOG_FILE = "modules/logs/game_debug.log"
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