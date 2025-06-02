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

---

## Issue 8: Improve validation error handling with AI feedback loop
**Labels:** `enhancement`, `error-handling`, `ai-integration`

### Description
When character update validation fails (like the recent consumable item_type issue), the system retries 3 times with the same AI response, leading to repeated failures. We need a feedback mechanism that informs the AI about the specific validation error so it can correct its response.

### Current Behavior
- Validation fails with specific error message
- System retries 3 times with identical AI response
- No feedback provided to AI about what failed
- Changes are reverted after max attempts
- User experiences failed update with no resolution

### Expected Behavior
- On validation failure, extract the specific error details
- Generate a corrective prompt explaining the validation issue
- Request AI to regenerate response with proper format/values
- Include schema constraints in error feedback
- Successfully complete update with corrected data

### Technical Requirements
1. Parse validation error messages to identify:
   - Failed field path (e.g., `equipment.9.item_type`)
   - Invalid value provided (e.g., `'consumable'`)
   - Valid values expected (e.g., `['weapon', 'armor', 'miscellaneous']`)

2. Generate corrective prompt:
   - Explain what validation failed and why
   - Provide the correct schema constraints
   - Request AI to retry with valid values

3. Implement feedback loop:
   - After validation failure, send error details back to AI
   - Allow AI to regenerate the update with corrections
   - Validate the corrected response

### Affected Files
- `update_character_info.py` (main validation and retry logic)
- `gpt.py` or AI interaction module (for sending corrective prompts)
- Schema validation error parsing

### Example Implementation
```python
if not is_valid:
    # Parse validation error
    error_details = parse_validation_error(error_msg)
    
    # Generate corrective prompt
    correction_prompt = f"""
    The character update failed validation:
    - Field: {error_details.field_path}
    - Invalid value: {error_details.invalid_value}
    - Valid options: {error_details.valid_options}
    
    Please regenerate the update using only valid values from the schema.
    For equipment items, use only: weapon, armor, or miscellaneous.
    """
    
    # Get corrected response from AI
    corrected_response = ai_model.request_correction(
        original_prompt=prompt,
        error_feedback=correction_prompt,
        character_data=current_data
    )
```

### Benefits
- Reduces failed updates and user frustration
- AI learns from validation errors in real-time
- More robust system that self-corrects
- Better handling of schema evolution
- Improved debugging with detailed error tracking

---

## Issue 9: Implement proper Hit Dice tracking for short rests
**Labels:** `enhancement`, `game-mechanics`, `data-integrity`

### Description
The game currently lacks a proper system for tracking Hit Dice usage during short rests. When the AI tries to track Hit Dice spent, it attempts to add fields like 'hitDiceRemaining' or 'hitDice' to character data, which fails validation because these fields aren't in the schema. Hit Dice spent during short rests are not being tracked, and there's no mechanism to restore them during long rests according to D&D 5e rules.

### Current Behavior
- No Hit Dice tracking fields in character schema
- AI attempts to add hitDiceRemaining/hitDice fail validation
- Hit Dice usage during short rests is mentioned but not persisted
- No automatic restoration during long rests
- No validation to prevent using more Hit Dice than available

### Evidence from Logs
```
Warning: Adding new field 'hitDiceRemaining' to character
Validation failed: Additional properties are not allowed ('hitDiceRemaining' was unexpected)
Warning: Adding new field 'hitDice' to character  
Validation failed: Additional properties are not allowed ('hitDice' was unexpected)
```

### Expected Behavior
- Track current and maximum Hit Dice in character data
- Persist Hit Dice usage across sessions
- Automatically restore half (rounded up) of max Hit Dice on long rest
- Validate Hit Dice availability before allowing usage
- Display remaining Hit Dice in character stats

### D&D 5e Rules Reference
- Characters have Hit Dice equal to their level
- Hit Die type depends on class (d10 for Fighter, d8 for Rogue, etc.)
- Short rest: Can spend any number of available Hit Dice
- Long rest: Regain Hit Dice equal to half character level (minimum 1)

### Technical Requirements
1. Update character schema to include:
   ```json
   "hitDice": {
     "current": 4,
     "maximum": 4,
     "dieType": "d10"
   }
   ```

2. Set schema additionalProperties to false to catch these issues

3. Modify short rest handling:
   - Check available Hit Dice before allowing usage
   - Update current Hit Dice count after usage
   - Persist changes to character file

4. Implement long rest mechanics:
   - Restore hit points to maximum
   - Restore Hit Dice: current = min(maximum, current + ceil(maximum/2))
   - Restore spell slots and abilities

### Affected Files
- `char_schema.json` (add hitDice object)
- `npc_schema.json` (add hitDice object)
- `update_character_info.py` (handle Hit Dice updates)
- `system_prompt.txt` (add Hit Dice tracking instructions)
- Character creation scripts (initialize Hit Dice based on class/level)

### Implementation Example
```python
def handle_short_rest(character_name, hit_dice_spent, roll_results):
    character = load_character(character_name)
    
    # Validate Hit Dice availability
    if hit_dice_spent > character["hitDice"]["current"]:
        return {"error": "Not enough Hit Dice available"}
    
    # Calculate healing
    con_modifier = calculate_modifier(character["abilities"]["constitution"])
    total_healing = sum(roll_results) + (hit_dice_spent * con_modifier)
    
    # Update character
    character["hitPoints"] = min(
        character["hitPoints"] + total_healing,
        character["maxHitPoints"]
    )
    character["hitDice"]["current"] -= hit_dice_spent
    
    save_character(character_name, character)
```

### Migration Strategy
1. Add hitDice field to schema with defaults
2. Update existing characters:
   - Set maximum = character level
   - Set current = maximum (assume full Hit Dice)
   - Set dieType based on class mapping
3. Update AI prompts to use the proper hitDice structure

### Benefits
- Accurate D&D 5e mechanics implementation
- Prevents validation errors when AI tries to track Hit Dice
- Better resource management gameplay
- Consistent tracking across sessions
- Clear display of available resources

---

## Issue 10: AI creates non-existent location paths and connections
**Labels:** `bug`, `ai-behavior`, `game-consistency`

### Description
The AI Dungeon Master is creating narrative elements (like secret paths and location connections) that don't exist in the actual campaign structure files. This leads to confusion when players attempt to follow AI-suggested paths that aren't defined in the game's location data, breaking immersion and causing inconsistencies between the narrative and the actual game state.

### Current Behavior
- AI invents secret passages, hidden doors, and alternate routes not in location files
- AI describes connections between locations that don't exist in the JSON structure
- Players get confused when trying to follow AI-described paths
- Narrative continuity breaks when suggested paths can't be followed
- No validation that AI responses match actual game structure

### Example Case
In the Keep of Doom campaign, the AI described:
- A "secret path" from the Haunted Hall (HH001) to other locations
- This path didn't exist in the actual HH001.json location file
- Player attempted to follow the secret path, causing confusion
- Required manual intervention to clarify actual available exits

### Expected Behavior
- AI should only reference locations that exist in the campaign files
- AI should only describe connections defined in location JSON files
- When describing a room, AI should check actual exits in the location data
- AI should not invent new paths, doors, or connections
- Clear error handling when AI tries to reference non-existent locations

### Root Cause
The system prompt doesn't explicitly instruct the AI to:
1. Check location files before describing paths/exits
2. Limit descriptions to actual game structure
3. Validate that narrative elements match campaign data

### Proposed Solution
1. Update system prompts to include strict instructions:
   ```
   LOCATION COMPLIANCE RULES:
   - Only describe exits that exist in the location's JSON file
   - Never invent secret passages, hidden doors, or alternate routes
   - Always check the actual location data before describing connections
   - If asked about paths not in the data, respond: "There is no such path here"
   - Reference only locations that exist in the campaign structure
   ```

2. Add validation layer:
   - Before AI response is sent, validate mentioned locations exist
   - Check that described exits match location JSON data
   - Flag any discrepancies for correction

3. Provide location context to AI:
   - Include current location's actual exits in the context
   - List valid connecting locations
   - Explicitly state which paths are available

### Affected Files
- `system_prompt.txt` (add location compliance rules)
- `dm_wrapper.py` or AI interaction layer (add validation)
- `location_manager.py` (provide location validation methods)
- Campaign location JSON files (ensure complete exit definitions)

### Implementation Example
```python
def validate_ai_location_response(ai_response, current_location):
    """Validate that AI response matches actual location data"""
    location_data = load_location(current_location)
    valid_exits = location_data.get('exits', [])
    
    # Check for invalid exit mentions
    mentioned_exits = extract_exits_from_narrative(ai_response)
    invalid_exits = [exit for exit in mentioned_exits if exit not in valid_exits]
    
    if invalid_exits:
        # Request AI to regenerate response with only valid exits
        correction_prompt = f"""
        Your response mentioned exits that don't exist: {invalid_exits}
        The only valid exits from {current_location} are: {valid_exits}
        Please regenerate your response using only these actual exits.
        """
        return get_corrected_response(correction_prompt)
    
    return ai_response
```

### Testing Strategy
1. Create test scenarios with limited exits
2. Prompt AI to describe the location
3. Verify AI only mentions actual exits
4. Test AI behavior when asked about non-existent paths
5. Ensure consistent behavior across multiple sessions

### Benefits
- Maintains consistency between narrative and game structure
- Reduces player confusion and frustration
- Ensures game progression follows designed paths
- Improves overall game reliability
- Makes debugging easier when issues arise