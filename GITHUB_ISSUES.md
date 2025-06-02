# GitHub Issues to Create

## Issue 1: Temporary ability effects not tracked or expired
**Labels:** `bug`, `enhancement`, `game-mechanics`

### Description
Temporary special abilities and effects (like spell durations, potion effects, or combat buffs) are not being tracked for duration or automatically expired when their time runs out.

### Current Behavior
- Temporary effects remain active indefinitely
- No duration tracking system in place
- No automatic expiration when time passes
- No UI indication of remaining duration

### Expected Behavior
- Track duration of temporary effects (rounds, minutes, hours)
- Automatically remove expired effects based on game time progression
- Display remaining duration in character stats
- Notify when effects are about to expire or have expired

### Affected Files
- `status_manager.py`
- `update_player_info.py` 
- `party_tracker.json` (worldConditions.time)
- `combat_manager.py` (for round-based effects)

### Possible Solution
Add a `temporaryEffects` array to character data with:
- Effect name and description
- Duration type (rounds, minutes, hours)
- Duration remaining
- Expiration timestamp
- Effect modifiers

---

## Issue 2: Duplicate class features and special abilities in character data
**Labels:** `bug`, `data-integrity`

### Description
Class features and special abilities are being duplicated in the character JSON files, appearing in multiple arrays (features, classFeatures, specialAbilities) with inconsistent formatting.

### Current Behavior
- Same ability appears in multiple arrays
- Inconsistent data structure (some as strings, some as objects)
- No clear distinction between feature types
- UI displays duplicates or wrong section

### Expected Behavior
- Each feature/ability appears only once
- Clear separation: `classFeatures` for class-based, `specialAbilities` for other
- Consistent object structure with name and description
- No duplication across arrays

### Affected Files
- `norn.json` and other character files
- `char_schema.json`
- `update_player_info.py`
- `templates/game_interface.html` (display logic)

### Example of Problem
```json
{
  "features": ["Second Wind", "Action Surge"],
  "classFeatures": [
    {"name": "Second Wind", "description": "..."},
    {"name": "Action Surge", "description": "..."}
  ],
  "specialAbilities": [
    {"name": "Second Wind", "description": "..."}
  ]
}
```

---

## Issue 3: Currency can go negative without validation
**Labels:** `bug`, `validation`

### Description
Player currency (gold, silver, copper) can become negative when spending money, as there's no validation to prevent overspending.

### Current Behavior
- Currency values can go below 0
- No checks when deducting money
- No warning when insufficient funds
- Negative values display in inventory

### Expected Behavior
- Prevent transactions that would result in negative currency
- Display "insufficient funds" message
- Validate currency operations before applying
- Option to convert between denominations (e.g., 1gp = 10sp)

### Affected Files
- `update_player_info.py` (validation functions)
- `char_schema.json` (add minimum: 0 constraint)
- Transaction handling in game logic

### Test Case
```
Player has: 5gp, 3sp, 2cp
Tries to spend: 10gp
Result: Should fail with "insufficient funds"
Current: Results in -5gp
```

---

## Issue 4: No tracking for expended/exhausted class features
**Labels:** `enhancement`, `game-mechanics`

### Description
Class features that have limited uses (like Second Wind 1/short rest, or Action Surge 1/short rest) don't track whether they've been used or when they refresh.

### Current Behavior
- No "uses remaining" counter
- No "exhausted" state tracking
- No automatic refresh on rest
- Players can use limited features unlimited times

### Expected Behavior
- Track uses remaining for each limited feature
- Mark features as exhausted when uses = 0
- Automatically refresh on appropriate rest type
- UI shows uses remaining (e.g., "Second Wind (0/1)")

### Affected Files
- Character data structure (`classFeatures` array)
- `char_schema.json` (add uses tracking)
- `update_player_info.py` (handle use/refresh)
- Rest system implementation

### Proposed Structure
```json
"classFeatures": [
  {
    "name": "Second Wind",
    "description": "Regain 1d10+level HP",
    "uses": {
      "current": 0,
      "max": 1,
      "refreshOn": "shortRest"
    }
  }
]
```

---

## Issue 5: Missing location summaries after exit/resume
**Labels:** `bug`, `persistence`

### Description
When exiting and resuming the game, location summaries from the conversation history are not being properly reconstructed, causing loss of context about previously visited locations.

### Current Behavior
- Location summaries missing after reload
- Only current location loaded
- Historical context lost
- AI lacks information about previous areas

### Expected Behavior
- Persist location summaries between sessions
- Rebuild context from conversation history
- Maintain continuity of adventure

### Affected Files
- `cumulative_summary.py`
- `conversation_utils.py`
- `location_manager.py`

*Note: Already documented in plan.md as Issue #7*

---

## Issue 6: Standardize character naming conventions for filesystem compatibility
**Labels:** `enhancement`, `data-integrity`, `breaking-change`

### Description
Character names with spaces or special characters (e.g., "Sir Reginald", "D'Artagnan") can cause filesystem issues when used in filenames. We need to establish and enforce a standard naming convention for all character files.

### Current Behavior
- Character names can contain spaces, apostrophes, and other special characters
- Some operations sanitize filenames ad-hoc (e.g., level_up conversation logs)
- No validation when creating new characters
- Inconsistent handling across different modules

### Expected Behavior
- Establish naming convention: alphanumeric, underscore, and hyphen only (e.g., "Sir_Reginald", "D_Artagnan")
- Validate character names at creation time
- Provide migration script for existing character files
- Consistent filename handling across all modules

### Affected Files
- `npc_builder.py` (enforce during NPC creation)
- `char_schema.json` (add pattern validation for name field)
- All character JSON files in campaigns
- `level_up.py` (already partially addressed)
- Any module that creates character-named files

### Migration Strategy
1. Add validation to prevent new characters with non-compliant names
2. Create migration script to rename existing character files
3. Update all references in campaign data
4. Provide clear error messages for invalid names

### Example Valid Names
- "Norn" ✓
- "Sir_Reginald" ✓ 
- "D_Artagnan" ✓
- "Mary-Sue" ✓
- "Fighter_1" ✓

### Example Invalid Names
- "Sir Reginald" ✗ (contains space)
- "D'Artagnan" ✗ (contains apostrophe)
- "Mary Sue" ✗ (contains space)
- "Fighter #1" ✗ (contains space and #)

---

## Issue 7: Inconsistent text capitalization in game interface
**Labels:** `bug`, `ui/ux`

### Description
The game interface displays inconsistent capitalization for character sheet sections and labels, making the UI look unprofessional. Field names and section headers should follow proper title case conventions.

### Current Behavior
- Mixed capitalization styles across different sections
- Some fields use lowercase (e.g., "hit points" instead of "Hit Points")
- Inconsistent formatting between character stats, equipment, and abilities
- No standard capitalization rules applied

### Expected Behavior
- All section headers use title case (e.g., "Character Stats", "Equipment", "Class Features")
- Field labels use consistent capitalization (e.g., "Hit Points", "Armor Class", "Proficiency Bonus")
- Maintain consistency across all character sheet elements
- Follow standard UI/UX conventions for RPG character sheets

### Affected Files
- `templates/game_interface.html` (main UI template)
- CSS styling files for text formatting
- Any JavaScript that dynamically generates field labels

### Examples to Fix
- "hit points" → "Hit Points"
- "armor class" → "Armor Class" 
- "class features" → "Class Features"
- "temporary effects" → "Temporary Effects"
- "background feature" → "Background Feature"

### Implementation Notes
- Create a consistent capitalization style guide
- Apply text-transform CSS rules where appropriate
- Update HTML templates to use proper casing
- Consider using CSS classes for consistent styling across similar elements