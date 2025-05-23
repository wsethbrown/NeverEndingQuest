# DungeonMasterAI Major Update - May 22, 2025

## Overview
This update implements significant improvements to the DungeonMasterAI system, addressing critical bugs and enhancing core functionality based on extensive gameplay testing.

## Major Changes

### 1. Lighting System Removal
- **Removed** the lighting field from location and room schemas
- **Cleaned** all lighting data from existing JSON files
- **Simplified** location data structure
- **Fixed** validation errors caused by complex lighting values

### 2. Unified Plot System
- **Created** single `campaign_plot.json` file per campaign
- **Removed** area-specific plot files (moved to old_plot_files/)
- **Eliminated** "plot file not found" errors
- **Simplified** plot management across areas

### 3. Fixed Player vs NPC Path Resolution
- **Fixed** case sensitivity issue causing player files to be searched in NPC folders
- **Added** separate name and display_name fields
- **Resolved** "npcs/norn.json not found" errors

### 4. Atomic File Operations
- **Implemented** `file_operations.py` module for safe JSON writes
- **Added** automatic backups before file modifications
- **Implemented** file locking to prevent concurrent access
- **Uses** temporary files and atomic renames
- **Prevents** data corruption and equipment loss

### 5. Enhanced Skill Check System
- **Strengthened** skill check requirements in system prompt
- **Added** explicit trigger phrases for common actions
- **Emphasized** CRITICAL RULE to always ask for rolls
- **Improved** step-by-step process clarity

### 6. Cumulative Adventure Summary System
- **Replaced** lossy 9-message summarization
- **Implemented** cumulative narrative from journal entries
- **Preserves** all adventure details
- **Provides** complete context without information loss
- **Created** `cumulative_summary.py` module

## Files Modified

### Core System Files
- `main.py` - Removed old summarization, added cumulative summary
- `system_prompt.txt` - Enhanced skill check instructions
- `campaign_path_manager.py` - Updated for unified plots
- `location_manager.py` - Enhanced summary generation
- `plot_update.py` - Updated for campaign-wide plots
- `action_handler.py` - Fixed plot filename handling

### Update Modules
- `update_player_info.py` - Added atomic file operations
- `update_npc_info.py` - Added atomic file operations  
- `update_party_tracker.py` - Added atomic file operations

### Schema Files
- `loca_schema.json` - Removed lighting field
- `room_schema.json` - Removed lighting field

### New Files
- `file_operations.py` - Atomic file operations module
- `cumulative_summary.py` - Adventure summary management
- `campaign_plot.json` - Unified plot file
- Various documentation files

## Bug Fixes
- Fixed player files being searched in NPC directories
- Fixed plot file not found errors
- Fixed adventure summary validation errors
- Fixed potential file corruption issues
- Fixed skill check consistency issues

## Technical Improvements
- Better error handling throughout
- Improved file operation safety
- Cleaner code architecture
- Better separation of concerns
- Enhanced debugging capabilities

## Migration Notes
- Old plot files moved to `old_plot_files/` directories
- Existing conversation histories automatically cleaned
- Lighting data removed from all location files
- System backwards compatible with existing saves

## Testing Notes
All changes have been tested for:
- File operation safety
- Plot system functionality
- Summary generation accuracy
- Skill check prompting
- Path resolution correctness

## Known Issues Resolved
1. Skill checks not being requested consistently
2. Plot files missing for areas other than HH001
3. Player files searched in wrong directories
4. File corruption during updates
5. Adventure context lost through summarization

---
*This update represents a major improvement in system reliability and gameplay experience.*