# Debug Message Standardization - Migration Status

## Completed Files

### ✅ Enhanced Logger Updates
- Added `import re` for Unicode sanitization
- Implemented `_sanitize_unicode()` method in CleanConsoleFormatter
- Created SanitizingFormatter for file handlers
- Added new game events: combat_end, module_transition, save_game, load_game
- Fixed warning and error functions to accept category parameter

### ✅ Debug Config Updates
- Added script-specific debug categories:
  - main_debug
  - action_handler_debug
  - character_updater_debug
  - combat_manager_debug
  - save_manager_debug
  - path_manager_debug
  - campaign_manager_debug
  - location_manager_debug
  - storage_manager_debug

### ✅ Module Path Manager (module_path_manager.py)
- Removed redundant try/except blocks for imports
- Converted all print statements to logger calls
- Added script prefix [ModulePathManager]
- Uses appropriate categories for different message types

### ✅ Storage Manager (storage_manager.py) 
- Added enhanced_logger import
- Converted single print statement to error() call
- Added script prefix [StorageManager]

### ✅ Location Manager (location_manager.py)
- Added enhanced_logger import
- Converted all 33 print statements to appropriate logger calls
- Added script prefix [LocationManager]
- Added game_event for successful location transitions
- Uses structured logging for location changes

### ✅ Campaign Manager (campaign_manager.py)
- Added enhanced_logger import
- Converted all 22 print statements to appropriate logger calls
- Added script prefix [CampaignManager]
- Added game_event for module transitions
- Uses appropriate categories for different operations

## Remaining Files to Migrate

### 🔲 action_handler.py
- Convert ~50 print statements
- Add enhanced_logger import
- Use [ActionHandler] prefix

### 🔲 combat_manager.py
- Convert ~50 print statements
- Remove color codes
- Add enhanced_logger import
- Use [CombatManager] prefix

### 🔲 update_character_info.py
- Convert ~50 print statements
- Remove color codes (RED, ORANGE, etc.)
- Add enhanced_logger import
- Use [CharacterUpdater] prefix

### 🔲 character_validator.py
- Unify logging approach (currently mixed)
- Add debug level logging
- Use [CharacterValidator] prefix

### 🔲 main.py
- Convert ~100+ print statements
- Add enhanced_logger import
- Use [Main] prefix

### 🔲 save_game_manager.py
- Add debug level logging (currently only warnings/errors)
- Convert test section prints
- Use [SaveGameManager] prefix

## Key Standardization Rules Applied

1. **Script Prefixes**: All messages now include [ScriptName] prefix
2. **No Unicode**: All Unicode characters replaced with ASCII equivalents
3. **Structured Events**: Common operations use game_event() for consistency
4. **Proper Categories**: Messages use appropriate debug categories from debug_config.py
5. **Exception Handling**: Errors include exception objects when available
6. **Consistent Formatting**: DEBUG, INFO, WARNING, ERROR (all caps)

## Benefits Achieved So Far

1. **Better Debugging**: Script identification makes it easy to trace issues
2. **Cleaner Output**: Enhanced logger filters verbose messages
3. **File Logging**: All messages saved to log files for analysis
4. **Unicode Safety**: No more encoding crashes on Windows
5. **Structured Events**: Game events are consistent and parseable

## Next Steps

Continue migrating the remaining 6 files following the same patterns established in the completed files.