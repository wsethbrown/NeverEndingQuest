# Level Up System Refactor V2 - Match Startup Wizard Pattern

## Current Problem
The level_up.py is using an old pattern where:
1. It generates a complete JSON character update
2. It parses JSON from AI responses
3. It directly saves the character file

This is inconsistent with how the system works elsewhere.

## Correct Pattern (from startup_wizard.py)
The startup wizard:
1. Uses AI conversation to gather information
2. AI returns complete JSON only for initial character creation
3. For updates, it should use `updateCharacterInfo` action

## New Approach
Instead of having level_up.py generate and parse JSON, it should:
1. For NPCs: Generate a changes dictionary and return it
2. For Players: Return guidance for interactive conversation
3. Both cases should result in using `updateCharacterInfo` action

## Implementation Plan

### 1. Simplify level_up.py
- Remove JSON parsing logic
- For NPCs: Return a changes dictionary (not full character JSON)
- For Players: Return guidance text only
- No direct file saving

### 2. Update action_handler.py
- For NPCs: Call level_up to get changes dict, then use update_character_info
- For Players: Inject guidance and let AI handle via updateCharacterInfo

### 3. Changes Format
Instead of full JSON, return changes like:
```python
{
    "level": 2,
    "hitPoints": 20,
    "maxHitPoints": 20,
    "experience_points": 0,
    "exp_required_for_next_level": 900,
    "classFeatures": [...],  # New features to add
    # etc.
}
```

This matches how updateCharacterInfo expects changes.