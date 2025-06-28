# Fix Double Injection Bug Plan

## Problem Analysis
The double injection bug occurs in the message combination system in `main.py:715-766`. The current flow:

1. Assistant generates response
2. Response immediately added to conversation history
3. If combat encounter detected, response is "held" for combination
4. When combination happens, system tries to replace the held response
5. But normal processing continues, potentially adding the response again
6. Result: Duplicate identical responses in conversation history

## Root Cause
The buffer system adds responses to conversation history before determining if they should be held/combined, leading to duplication when the combination logic runs.

## Solution Strategy
**Defer Conversation History Updates**: Don't add responses to conversation history until after combination decisions are made.

## Implementation Plan

### Step 1: Modify Buffer Logic in main.py
- Lines 715-766: Refactor message combination system
- Create temporary response storage during combination phase
- Only add final responses to conversation history

### Step 2: Separate Action Processing
- Process actions immediately (for game state updates)
- Handle conversation history separately from action processing

### Step 3: Single Insertion Point
- Ensure only one place in code adds assistant responses to conversation history
- Eliminate duplicate insertion paths

## Files to Modify
- `/mnt/c/dungeon_master_v1/main.py` (primary fix)

## Testing Plan
1. Verify no duplicate responses during location transitions
2. Ensure combat encounter combinations still work
3. Confirm conversation compression (72→26 messages) functions normally
4. Test with the specific scenario from claude.txt (Rangers' Command Post to Trader's Rest transition)

## Expected Outcome
- Single assistant responses in conversation history
- Combat encounter combinations work correctly
- No impact on conversation compression system
- Clean conversation flow without duplicates