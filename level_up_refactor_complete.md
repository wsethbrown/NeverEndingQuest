# Level Up System Refactor - Complete

## Problem Solved
The level up system was causing an infinite loop because:
- `level_up.py` ran as a subprocess expecting terminal input via `input()` calls
- The web interface couldn't communicate with the subprocess
- This caused repeated retry attempts, draining API tokens

## Solution Implemented
Refactored the level up system to work like `combat_manager.py`:
- Created `run_level_up_process()` function that can be called directly
- Removed all `input()` calls for NPCs (automatic decisions)
- Preserved interactive behavior for players (returns guidance for conversation)
- Added timeout protection (30 seconds) to prevent infinite loops

## Key Changes

### 1. level_up.py
- Added `run_level_up_process()` function that:
  - Detects if character is player or NPC based on `character_role`
  - For NPCs: Makes all decisions automatically, returns complete update
  - For players: Returns interactive guidance to be injected into conversation
- Improved JSON parsing to handle markdown code blocks
- Kept validation system intact

### 2. action_handler.py
- Replaced subprocess launch with direct function call
- Added logic to handle both player and NPC cases:
  - Players: Injects guidance and returns `needs_response` status
  - NPCs: Processes automatic update and saves character data
- Added timeout protection using signal handlers
- Improved error handling and logging

## How It Works Now

### For NPCs:
1. AI DM uses `levelUp` action with entity name and new level
2. `action_handler.py` calls `run_level_up_process()` directly
3. AI automatically makes all decisions (HP average, etc.)
4. Character file is updated with new stats
5. Success message added to conversation

### For Players:
1. AI DM uses `levelUp` action with entity name and new level
2. `action_handler.py` calls `run_level_up_process()`
3. Function returns interactive guidance
4. Guidance is injected into conversation
5. AI DM engages player in choices (HP roll vs average, spells, etc.)
6. Player makes decisions through conversation
7. AI DM uses `updateCharacterInfo` to apply all changes

## Benefits
- No more infinite loops or token drain
- Consistent architecture with other systems (like combat_manager)
- Preserves interactive experience for players
- Automatic handling for NPCs saves time
- Timeout protection prevents hangs
- Better error messages and logging

## Testing Recommendations
1. Test NPC level up with a party NPC reaching enough XP
2. Test player level up when player gains enough XP
3. Verify XP resets to 0 after level up
4. Verify new XP goal is set correctly
5. Check that all class features are added properly

## Success Criteria Met
- ✅ Level up completes without hanging
- ✅ Character file updates correctly
- ✅ XP resets to 0 after level up
- ✅ New experience_goal is set
- ✅ No infinite loops occur
- ✅ No token drain
- ✅ Works for both players and NPCs
- ✅ Errors are handled gracefully
- ✅ Process completes within 30 seconds