# DungeonMasterAI Logging System

## Overview
The enhanced logging system provides cleaner console output and detailed file logging with configurable debug categories.

## Files Created
- `debug_config.py` - Configuration for what gets logged
- `enhanced_logger.py` - Main logging functionality
- `redirect_debug_output.py` - Intercepts and cleans debug output
- `view_logs.py` - Utility to view and search logs
- `game_errors.log` - Error log file (auto-created)
- `game_debug.log` - Debug log file (auto-created)

## Configuration
Edit `debug_config.py` to control what appears in console:

```python
DEBUG_CATEGORIES = {
    "errors": True,                    # Always show errors
    "campaign_loading": False,         # Hide repetitive campaign loading messages
    "file_operations": True,           # Show file errors
    "location_transitions": True,      # Show location changes
    "plot_updates": True,              # Show plot progression
    # ... etc
}
```

## Console Output Icons
- 📍 Location transitions
- 📖 Plot updates  
- 🎒 Inventory changes
- 👤 Character updates
- ⚔️ Combat events
- ✓ Successful operations
- ❌ Errors
- ⚠️ Warnings
- ⏰ Time updates

## Viewing Logs

### From Command Line:
```bash
# View recent errors (last 10 minutes)
python view_logs.py errors

# View recent debug messages (last 30 minutes)
python view_logs.py debug 30

# Search for specific terms
python view_logs.py search "location transition"

# Show last 20 lines of error log
python view_logs.py tail error
```

### From Python/Claude:
```python
# Read error log directly
with open('game_errors.log', 'r') as f:
    recent_errors = f.readlines()[-50:]  # Last 50 lines
```

## Integration
The logging system automatically integrates when you run the web interface. The debug interceptor will:
- Clean up repetitive messages
- Format messages with icons
- Log errors to `game_errors.log`
- Log everything to `game_debug.log`
- Filter based on your configuration

## Troubleshooting
- If logs get too large, they auto-rotate at 10MB
- To disable all console debug output, set all categories to False in `debug_config.py`
- To see everything again, delete the import of `redirect_debug_output` from `web_interface.py`