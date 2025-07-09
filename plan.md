# XP Update Investigation Plan

## Objective
Find out why XP is calculated correctly in combat but not applied to characters.

## Current Issue
- Combat calculates XP: "XP awarded: 200"
- Character's XP remains at 1325/2700 (not updated)
- Commented out code (lines 1884-1889) was causing double XP

## Investigation Steps
1. Trace XP calculation in combat_manager.py ✓
2. Find where combat XP should be applied to characters ✓
3. Investigate updateCharacterInfo action in action_handler.py ✓
4. Check update_character_info.py for XP application logic ✓
5. Understand the double XP issue with the commented code ✓

## Files Examined
- combat_manager.py - XP calculation during combat
- action_handler.py - updateCharacterInfo action handling
- update_character_info.py - Character XP update logic
- xp.py - XP calculation logic
- main.py - Main game loop and combat handling

## Findings

### 1. XP Calculation Flow
- Combat ends → `calculate_xp()` from xp.py is called
- Returns: `(xp_narrative, xp_awarded)` where `xp_awarded` is per-participant XP
- Example: 200 total XP divided among participants = 200 XP each

### 2. The Commented Code Issue (Lines 1884-1889)
```python
# xp_update_response = f"Update the character's experience points. XP Awarded: {xp_awarded}"
# updated_data_tuple = update_json_schema(xp_update_response, player_info, encounter_data, party_tracker_data)
```
- This was causing double XP because:
  - `update_json_schema()` function extracts XP from the AI response string
  - It was passing `xp_awarded` (per-participant) but treating it as total XP
  - The comment says "now handled by general character update"

### 3. Current XP Update Mechanism
- XP narrative is added to conversation history: `"XP Awarded: {xp_narrative}"`
- The narrative contains the full description of XP distribution
- Example: "Norn and their companions Mac'Davier defeated 1 enemy... awarding each participant 200 experience points."

### 4. The Missing Link
- The XP narrative is added to conversation history but **no actual character update is triggered**
- The comment says "now handled by general character update" but this isn't happening
- The AI is expected to see the "XP Awarded:" message and issue an updateCharacterInfo action
- However, this is happening in the combat_manager conversation, not the main conversation

## Root Cause
The XP update mechanism was removed to fix double XP, but no replacement was implemented. The XP narrative is added to the combat conversation history, but:
1. Combat ends and returns to main.py
2. The main game loop doesn't have visibility of the combat conversation
3. The AI in the main loop never sees the XP award message
4. No updateCharacterInfo action is triggered for XP

## Recommended Fix
Need to implement one of these solutions:
1. **Option A**: Re-enable the direct XP update in combat_manager.py but fix the double XP issue
2. **Option B**: Pass the XP information back to main.py so it can trigger the update
3. **Option C**: Add the XP award message to the main conversation history after combat