# Investigation Plan for Infinite Loop Issue

## Problem
The system is continuously generating empty prompts with just player status information like:
`[20:08:00][HP:44/47][XP:16581/14000] norn:`

This suggests an infinite loop where the game loop is running without proper user input handling.

## Investigation Steps

1. **Examine main game loop** - Check main.py for the primary game loop and any while True loops
2. **Search for status generation code** - Find where the player status line is generated
3. **Check for auto-refresh mechanisms** - Look for timers, threading, or automatic refresh code
4. **Review recent changes** - Examine modified files (action_handler.py, etc.) for changes that might cause loops
5. **Analyze prompt generation logic** - Find where empty prompts might be generated
6. **Check for exit conditions** - Verify all loops have proper termination conditions

## Files to Examine
- main.py (main game loop)
- action_handler.py (recently modified)
- Any files handling player status display
- Input handling mechanisms
- Prompt generation code

## Expected Root Causes
- Missing input() call or user input handling
- Loop without proper exit condition
- Auto-refresh mechanism gone wrong
- Recent changes breaking the input flow

---

# DungeonMasterAI Debugging and Improvement Plan

## Executive Summary
This document outlines a comprehensive plan to debug and improve the DungeonMasterAI system based on identified issues during gameplay testing. The plan addresses critical bugs, infrastructure problems, and system reliability improvements.

## Current Debug Issues Identified

### Issue #1: Skill Check Not Being Conducted (HIGH PRIORITY)
**Problem**: Persuasion check not being conducted - AI didn't ask player to roll or conduct the check when persuasion was attempted.

**Root Cause**: 
- AI model not following system prompt instructions about skill checks (lines 152-165 in system_prompt.txt)
- Validation system not catching missing skill check requests
- System prompt instructions may not be clear enough about when to request rolls

**Evidence**: User reported during gameplay testing

**Fix Strategy**:
1. Enhance system prompt with more explicit skill check instructions
2. Add validation rules to catch missing skill check requests
3. Implement fallback prompts when skill checks are implied but not requested
4. Add debugging logs for skill check detection

### Issue #2: Time Passage Tracking (MEDIUM PRIORITY)
**Problem**: Ensure each conversation round adds at least 1 minute using updateTime action.

**Root Cause**:
- AI forgetting to use `updateTime` action for basic conversation interactions
- System prompt lines 441-461 require updateTime for activities taking significant time

**Evidence**: General observation during gameplay

**Fix Strategy**:
1. Strengthen system prompt requirements for time updates
2. Add validation to ensure updateTime is called for each interaction
3. Implement automatic time advancement fallback
4. Add time tracking debug logging

### Issue #3: Sub-Location Handling Inconsistency (HIGH PRIORITY)
**Problem**: Cellar/closets/rooms within locations sometimes treated as separate areas vs part of main location.

**Symptoms**:
- Sometimes cellar treated as part of inn
- Sometimes cellar treated as separate area needing non-existent location
- Causes location transition errors and gameplay confusion

**Evidence**: User reported inconsistent behavior with inn cellar

**Fix Strategy**:
1. **Narrative Approach**: Treat sub-areas as descriptive elements within main location
2. **Location Data Enhancement**: Add `subAreas: ["cellar", "upstairs", "storage room"]` to location JSON
3. **System Prompt Clarification**: Add explicit instructions about when to transition vs narrate
4. **Validation Rules**: Prevent transitions to non-existent locations

### Issue #4: AI Creating Non-Existent Content (HIGH PRIORITY)
**Problem**: AI is inventing doors, paths, and dungeons not in the campaign data, potentially corrupting world state when code appends/adds locations.

**Risk**: World state corruption when code appends/adds these fictional locations

**Evidence**: User reported campaign creating doors and paths not in campaign files

**Fix Strategy**:
1. **Strict Validation**: Validate all location references against campaign data before allowing actions
2. **System Prompt Enhancement**: Strengthen instructions about world consistency
3. **Code Safeguards**: Add location existence checks before any file writes
4. **AI Response Validation**: Check AI responses for location references before processing
5. **Campaign Data Lock**: Make campaign files read-only during gameplay

### Issue #5: Plot Loading Issue (HIGH PRIORITY)
**Problem**: Plot files for other areas don't exist, but first area contains overall campaign plot not being pulled forward to new areas.

**Impact**: Players lose access to main story context when moving to new areas

**Evidence**: Error logs show repeated `plot_G001.json not found` errors

**Fix Strategy**:
1. **Plot Inheritance System**: Copy HH001 plot to all area directories when missing
2. **Fallback Plot Loading**: If current area plot doesn't exist, load from HH001
3. **Centralized Plot Management**: Create campaign-wide plot file separate from area-specific plots
4. **Plot File Generation**: Auto-generate missing plot files from master campaign plot

### Issue #6: UpdatePlayer Inventory Corruption (HIGH PRIORITY)
**Problem**: Character file update error corrupted/wiped player equipment inventory.

**Root Cause Analysis** (from error logs):
- updatePlayerInfo IS functioning correctly (lines 132-217 in error.txt show successful updates)
- Infrastructure issues around file management cause failures:
  - Campaign path resolution failures
  - Race conditions during concurrent file operations
  - Partial write failures causing JSON corruption
  - Validation failures due to encoding issues

**Evidence**: 
- error.txt lines 132-184: Successful equipment updates
- error.txt lines 202-217: Successful special abilities update
- Repeated file not found errors for campaign paths

**Fix Strategy**:
1. **Add File Locking**: Prevent concurrent writes to player files
2. **Atomic Writes**: Write to temp file, then rename (prevents corruption)
3. **Better Error Handling**: Catch and recover from partial write failures
4. **Path Validation**: Ensure campaign paths exist before attempting writes
5. **Backup on Write**: Create .bak files before each update

## Error Log Analysis

### Primary Error Sources (from error.txt):

1. **Campaign Structure Issues** (Lines 7, 11, 33, etc.):
   ```
   DEBUG: File campaigns/Keep_of_Doom/npcs/norn.json not found.
   ```
   - Repeated 15+ times
   - Player file path resolution failing

2. **Plot File Missing** (Lines 85, 88, 95, etc.):
   ```
   ERROR: Plot file plot_G001.json not found.
   DEBUG: File campaigns/Keep_of_Doom/plot_G001.json not found.
   ```
   - Repeated 10+ times
   - Relates to Issue #5

3. **Adventure Summary Errors** (Line 106):
   ```
   ERROR: Error occurred while running adv_summary.py: Command returned non-zero exit status 1.
   ```
   - Cascades into other system failures

4. **Successful updatePlayerInfo Operations** (Lines 132-217):
   - Equipment updates working correctly
   - Special abilities updates working correctly
   - Proves core system functionality is sound

### Debug Files Used:
- `/mnt/c/dungeon_master_v1/error.txt` - Primary error log with detailed timeline
- `/mnt/c/dungeon_master_v1/debug_player_update.json` - Player update debug info
- `/mnt/c/dungeon_master_v1/debug_log.txt` - General debug information
- `/mnt/c/dungeon_master_v1/npc_update_debug_log.json` - NPC update logs (working correctly)

## Implementation Strategy

### Phase 1: Critical Infrastructure Fixes (Week 1)
1. **Fix Campaign Path Resolution**
   - Update campaign_path_manager.py to handle missing files gracefully
   - Add file existence validation before operations
   - Implement fallback paths for missing campaign files

2. **Implement Atomic File Operations**
   - Add file locking mechanism
   - Implement atomic writes (temp file + rename)
   - Add automatic backup creation before writes

3. **Fix Plot Loading System**
   - Implement plot inheritance from HH001 to other areas
   - Add fallback plot loading mechanism
   - Create missing plot files automatically

### Phase 2: AI Behavior Improvements (Week 2)
1. **Enhance System Prompt**
   - Add explicit skill check requirements
   - Clarify sub-location handling rules
   - Strengthen world consistency instructions
   - Add time tracking requirements

2. **Implement Response Validation**
   - Add skill check detection in validation
   - Validate location references against campaign data
   - Add time update validation
   - Implement content creation prevention

### Phase 3: User Interface Enhancements (Week 3)
1. **Improve Web Interface**
   - Add current location display (COMPLETED)
   - Enhance error reporting in debug panel
   - Add real-time file corruption detection
   - Implement recovery mechanisms

2. **Add Debugging Tools**
   - Enhanced logging for all major operations
   - File integrity checking
   - Campaign validation tools
   - Performance monitoring

### Phase 4: Testing and Validation (Week 4)
1. **Comprehensive Testing**
   - Test all skill check scenarios
   - Validate location transition handling
   - Test equipment/inventory operations
   - Stress test file operations

2. **Documentation Updates**
   - Update system prompt documentation
   - Create troubleshooting guide
   - Document recovery procedures
   - Update deployment instructions

## Files Modified So Far

### Recent Changes Made:
1. **main.py** - Fixed trap DC KeyError with defensive programming (lines 569-572)
2. **web_interface.py** - Added location data endpoint for debugging display
3. **templates/game_interface.html** - Added current location display in header
4. **clear.py** - Enhanced to clear gameplay-acquired equipment while preserving progression

### Commits to Include in Backup:
- Fix trap DC KeyError in main.py
- Add current location display to web interface
- Enhanced clear.py for better equipment management

## Risk Assessment

### High Risk Items:
1. **Data Corruption**: File operation failures could corrupt save games
2. **World Consistency**: AI creating non-existent content breaks campaign integrity
3. **Player Experience**: Skill checks not working breaks core D&D mechanics

### Medium Risk Items:
1. **Performance**: File locking might slow down operations
2. **Complexity**: Additional validation could complicate system
3. **Compatibility**: Changes might affect existing save games

### Mitigation Strategies:
1. **Backup Everything**: Automatic backups before any file operations
2. **Gradual Rollout**: Implement fixes in phases with testing
3. **Rollback Plan**: Keep previous versions available for quick reversion
4. **Monitoring**: Enhanced logging to catch issues early

## Success Metrics

### Primary Goals:
1. **100% Skill Check Detection**: AI always requests appropriate skill checks
2. **Zero Data Corruption**: No player file corruption incidents
3. **Consistent World State**: No AI-invented locations or content
4. **Complete Plot Continuity**: Plot information available in all areas

### Secondary Goals:
1. **Improved Performance**: Faster file operations with safety
2. **Better User Experience**: Clear error messages and recovery options
3. **Enhanced Debugging**: Comprehensive logging for issue resolution
4. **System Reliability**: 99%+ uptime for core game functions

## Conclusion

### Issue #7: Missing Location Summaries After Exit/Resume (MEDIUM PRIORITY)
**Problem**: Location visits can be skipped for summarization when exitGame/resume occurs during a visit.

**Symptoms**:
- Messages between location transitions are not summarized
- Conversation history shows raw messages instead of location summary
- Occurs when player exits game mid-location and resumes

**Evidence**: User found Wyrd Lantern Inn (A05) visit was never summarized after exit/resume cycle

**Root Cause**:
- Exit/resume disrupts location visit tracking
- System only processes most recent transition
- Check for "already processed" may incorrectly skip summarization
- State not properly preserved across game sessions

**Fix Strategy**:
1. **Build recovery function**: Scan conversation history for missing summaries
2. **Detect pattern**: Find location transitions without summaries between them
3. **Generate missing summaries**: Summarize orphaned location visits
4. **Run on game load**: Check and fix on startup or periodically
5. **Preserve state**: Better tracking across exit/resume cycles

## Conclusion

This plan addresses the core issues identified during gameplay testing while maintaining system stability and improving overall reliability. The phased approach allows for careful implementation and testing of critical fixes while building toward a more robust and user-friendly system.

The evidence shows that most core systems are functioning correctly, but infrastructure improvements are needed to handle edge cases and provide better error recovery. The focus should be on defensive programming, better validation, and improved user feedback to create a stable gaming experience.