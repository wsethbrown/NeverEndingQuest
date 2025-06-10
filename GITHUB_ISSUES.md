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

---

## Issue #18 - Location Transition Bug (Comprehensive Navigation System)
**Labels:** `bug`, `enhancement`, `critical`

### Description
This is a critical issue affecting multi-area campaigns. Current transition system has several failure points:
- Inconsistent connectivity definitions between areas
- No validation of cross-area connections
- Missing path validation logic
- String matching issues between location names and IDs

### Proposed Solution: Comprehensive Navigation Validation System

A multi-component system to handle all location transitions with proper validation:

**Core Components:**
1. **Campaign Graph Builder** (`campaign_graph_builder.py`)
   - Build complete connectivity graph of entire campaign
   - Validate bidirectional connections
   - Detect orphaned/unreachable locations

2. **Path Finder** (`path_finder.py`) 
   - Dijkstra/A* pathfinding algorithms
   - Handle cross-area transitions
   - Support alternative routes

3. **Navigation Validator** (`navigation_validator.py`)
   - Main validation engine for transitions
   - Check for blocking monsters
   - Verify visited location requirements  
   - Prevent teleportation cheating

4. **Monster Blocking System** (`monster_blocking.py`)
   - Track monsters that block specific paths
   - Handle conditional path availability

**Key Features:**
- Anti-cheating system (prevent jumping to unconnected locations)
- Monster blocking detection (enemies can block progress)
- Visited location tracking (player exploration history)
- Dynamic path calculation with constraints
- Integration with combat system and action handler

**Implementation Priority:**
- Phase 1: Basic graph and validation (fixes current issue)
- Phase 2: Monster blocking system
- Phase 3: Anti-cheating validation
- Phase 4: Advanced features (alternative paths, etc.)

**Benefits:**
- Prevents cheating/teleportation
- Enhances immersion through logical movement
- Supports complex multi-area campaigns
- Meaningful monster obstacle integration
- Easy debugging of connectivity issues

This comprehensive solution would completely resolve the location transition failures while adding robust navigation features that enhance gameplay.

---

## Issue #20 - Cannot determine equipped items and accurate AC calculation
**Labels:** `bug`, `enhancement`, `game-mechanics`, `ui/ux`

### Description
Players cannot tell which items are equipped vs owned, and Armor Class is displayed as a static number without showing how it's calculated. The current system stores armor, weapons, and equipment in disconnected ways, making it impossible to understand what contributes to a character's AC or combat effectiveness.

### Current Problems

**1. No Equipped vs Owned Distinction**
- All equipment shows as a flat list with no indication of what's equipped
- No `equipped` boolean field in equipment schema
- Players can't tell what armor/weapons they're actually using

**2. Missing Armor Data**
- Character has AC 16 but no armor pieces listed in equipment
- Armor Class appears as static number with no source breakdown
- No way to see what provides the base AC value

**3. Disconnected Equipment Systems**
- Weapons stored in `attacksAndSpellcasting` array (separate from equipment)
- Armor not stored anywhere despite contributing to AC
- Equipment items not linked to combat stats

**4. No AC Calculation Logic**
- AC shown as static field with no calculation
- Missing breakdown: Base Armor + DEX mod + Fighting Style + other bonuses
- Cannot verify if AC is correct for current equipment

### Current Character Data Example (Norn)
```json
"armorClass": 16,  // Static number, no source shown
"equipment": [     // No armor pieces listed
  {"item_name": "Hemp Rope", "item_type": "miscellaneous"},
  {"item_name": "Torch", "item_type": "miscellaneous"}
],
"attacksAndSpellcasting": [  // Weapons disconnected from equipment
  {"name": "Longsword", "attackBonus": 5}
]
```

### Expected Behavior

**1. Equipment Schema Enhancement**
```json
"equipment": [
  {
    "item_name": "Chain Mail", 
    "item_type": "armor", 
    "equipped": true,
    "ac_base": 16,
    "dex_limit": 0
  },
  {
    "item_name": "Shield", 
    "item_type": "armor", 
    "equipped": true,
    "ac_bonus": 2
  },
  {
    "item_name": "Longsword", 
    "item_type": "weapon", 
    "equipped": true,
    "damage": "1d8+3",
    "attack_bonus": 5
  },
  {
    "item_name": "Backup Sword", 
    "item_type": "weapon", 
    "equipped": false
  }
]
```

**2. AC Calculation Display**
```json
"ac_calculation": {
  "base_armor": 16,        // From equipped Chain Mail
  "dex_modifier": 0,       // Limited by heavy armor
  "shield_bonus": 2,       // From equipped shield  
  "fighting_style": 1,     // Defense fighting style
  "other_bonuses": 0,      // Magical items, spells, etc.
  "total": 19
}
```

**3. UI Improvements**
- Visual distinction between equipped (highlighted) and unequipped items
- AC breakdown showing each contributing factor
- Equipment slots (Head, Chest, Hands, etc.) with drag-and-drop equipping
- Weapons section showing equipped vs backup weapons

### Technical Requirements

**1. Schema Updates**
- Add `equipped` boolean field to equipment items
- Add armor-specific fields: `ac_base`, `ac_bonus`, `dex_limit`
- Add weapon-specific fields: `damage`, `attack_bonus`, `weapon_type`
- Add `ac_calculation` object to character data

**2. Data Migration**
- Add missing armor pieces to existing characters
- Set appropriate `equipped` flags based on current stats
- Link weapons from `attacksAndSpellcasting` to `equipment`

**3. AC Calculation Logic**
```python
def calculate_armor_class(character_data):
    equipped_armor = get_equipped_armor(character_data)
    base_ac = equipped_armor.get('ac_base', 10)  # 10 + DEX if no armor
    
    dex_modifier = get_dex_modifier(character_data)
    if equipped_armor.get('dex_limit') is not None:
        dex_modifier = min(dex_modifier, equipped_armor['dex_limit'])
    
    shield_bonus = get_shield_bonus(character_data)
    fighting_style_bonus = get_fighting_style_ac_bonus(character_data)
    other_bonuses = get_magical_ac_bonuses(character_data)
    
    return {
        'base_armor': base_ac,
        'dex_modifier': dex_modifier,
        'shield_bonus': shield_bonus,
        'fighting_style': fighting_style_bonus,
        'other_bonuses': other_bonuses,
        'total': base_ac + dex_modifier + shield_bonus + fighting_style_bonus + other_bonuses
    }
```

**4. UI Enhancements**
- Equipment slots interface with equip/unequip functionality
- AC breakdown tooltip or expandable section
- Visual indicators for equipped items (bold, different color, checkmark)
- Weapon loadout section showing primary/secondary weapons

### Affected Files
- `char_schema.json` - Add equipment fields and AC calculation object
- `norn.json` and other character files - Data migration
- `templates/game_interface.html` - UI improvements for equipment display
- `update_character_info.py` - AC calculation logic
- `system_prompt.txt` - Instructions for AI to manage equipment properly

### D&D 5e Rules Reference
- **Base AC**: Armor type determines base AC (Leather 11, Chain Mail 16, Plate 18)
- **DEX Modifier**: Added to AC, but limited by armor type (Heavy armor: +0, Medium: max +2)
- **Shield**: +2 AC when equipped
- **Fighting Styles**: Defense style gives +1 AC when wearing armor
- **Magical Items**: Can provide additional AC bonuses

### Implementation Priority
1. **Phase 1**: Add `equipped` field and basic equipment distinction
2. **Phase 2**: Implement AC calculation logic
3. **Phase 3**: Enhanced UI with equipment slots
4. **Phase 4**: Advanced features (equipment sets, automatic optimization)

### Benefits
- Players can see exactly what equipment they're using
- AC calculation is transparent and verifiable
- Equipment decisions become meaningful
- Better integration between equipment and combat stats
- Improved character sheet accuracy and usability
- Easier debugging of character stat issues

### Example Use Case
A player finds better armor and wants to compare:
- Current: Chain Mail (AC 16) + Shield (+2) + Defense Style (+1) = 19 AC
- New: Scale Mail (AC 14 + DEX 2) + Shield (+2) + Defense Style (+1) = 19 AC
- Decision: Keep Chain Mail for better AC with low DEX, or switch for other benefits

This visibility enables informed equipment choices and better gameplay experience.

---

## Issue 21: Special abilities from equipped items not reflected in character abilities section
**Labels:** `bug`, `game-mechanics`, `data-integrity`

### Description
When players equip items with special abilities (like the Knight's Heart-shaped Amulet providing damage resistance), the abilities are correctly added to the equipment inventory with `equipped: true`, but they do not appear in the character's special abilities or class features sections. This creates a disconnect where the player cannot see what special powers they currently have active from their equipped gear.

### Current Behavior
- Equipment with special abilities is properly added to inventory
- `equipped` flag is correctly set to `true` by the AI
- Special abilities from items do not appear in the specialAbilities array
- Player cannot see what powers they have from equipped gear
- No indication in abilities section that equipment provides special powers

### Example Case
The Knight's Heart-shaped Amulet provides:
- **Equipment**: Correctly shows in inventory as equipped
- **Special Ability**: Damage resistance to necrotic damage
- **Problem**: Damage resistance does not appear in character's specialAbilities section

### Expected Behavior
- When an item with special abilities is equipped, those abilities should be automatically added to the character's specialAbilities array
- Abilities should be marked as coming from equipment (not innate)
- When item is unequipped, the abilities should be automatically removed
- A comprehensive audit pass should ensure all currently equipped items with special abilities are properly reflected

### Technical Requirements

**1. Automatic Ability Synchronization**
```python
def sync_equipment_abilities(character_data):
    """Sync special abilities from equipped items to character abilities"""
    equipped_items = [item for item in character_data.get('equipment', []) 
                     if item.get('equipped', False)]
    
    equipment_abilities = []
    for item in equipped_items:
        if 'special_abilities' in item:
            for ability in item['special_abilities']:
                equipment_abilities.append({
                    'name': ability['name'],
                    'description': ability['description'],
                    'source': f"Equipment: {item['item_name']}"
                })
    
    # Remove old equipment abilities and add current ones
    non_equipment_abilities = [ability for ability in character_data.get('specialAbilities', [])
                              if not ability.get('source', '').startswith('Equipment:')]
    
    character_data['specialAbilities'] = non_equipment_abilities + equipment_abilities
```

**2. Equipment Schema Enhancement**
```json
{
  "item_name": "Knight's Heart-shaped Amulet",
  "item_type": "miscellaneous", 
  "equipped": true,
  "special_abilities": [
    {
      "name": "Necrotic Resistance",
      "description": "Resistance to necrotic damage",
      "type": "passive"
    }
  ]
}
```

**3. Abilities Display Enhancement**
```json
"specialAbilities": [
  {
    "name": "Necrotic Resistance",
    "description": "Resistance to necrotic damage", 
    "source": "Equipment: Knight's Heart-shaped Amulet"
  },
  {
    "name": "Second Wind",
    "description": "Regain 1d10+level HP once per short rest",
    "source": "Fighter Class Feature"
  }
]
```

### Implementation Strategy

**Phase 1: Audit Current Equipped Items**
- Create a script to scan all character files
- Identify equipped items with special abilities
- Add missing abilities to specialAbilities arrays
- Mark abilities with equipment source

**Phase 2: Automatic Synchronization**
- Implement sync function called whenever equipment changes
- Hook into equipment equip/unequip actions
- Update character display to show ability sources

**Phase 3: AI Integration**
- Update system prompts to instruct AI about equipment abilities
- Ensure AI considers equipment abilities in combat and decisions
- Validate that AI properly tracks equipment-based powers

### Affected Files
- `char_schema.json` - Add special_abilities field to equipment items
- `norn.json` and other character files - Data migration for equipped items
- `update_character_info.py` - Add equipment ability synchronization
- `templates/game_interface.html` - Display ability sources in UI  
- `system_prompt.txt` - Instructions for AI to consider equipment abilities

### Equipment Items to Audit
Based on common D&D magic items, check for:
- **Resistance/Immunity items** (rings, amulets, cloaks)
- **Stat boost items** (belts, gauntlets, headbands)
- **Special power items** (boots of speed, cloak of elvenkind)
- **Combat enhancement items** (weapons with special attacks, armor with abilities)

### Example Equipment with Abilities
```json
{
  "item_name": "Cloak of Elvenkind",
  "item_type": "miscellaneous",
  "equipped": true, 
  "special_abilities": [
    {
      "name": "Advantage on Stealth",
      "description": "You have advantage on Dexterity (Stealth) checks",
      "type": "passive"
    }
  ]
},
{
  "item_name": "Ring of Protection",
  "item_type": "miscellaneous",
  "equipped": true,
  "special_abilities": [
    {
      "name": "AC and Saving Throw Bonus", 
      "description": "+1 bonus to AC and saving throws",
      "type": "passive"
    }
  ]
}
```

### Benefits
- Players can see all their active abilities in one place
- Equipment choices become more meaningful and visible
- Easier to track character capabilities during play
- AI can better utilize equipment abilities in decisions
- Consistent ability tracking across all sources
- Better integration between equipment and character mechanics

### Testing Checklist
- [ ] Equipped items with abilities appear in specialAbilities
- [ ] Unequipped items remove their abilities
- [ ] Ability sources are clearly marked
- [ ] No duplicate abilities from multiple sources
- [ ] AI considers equipment abilities in combat
- [ ] UI clearly displays ability sources
- [ ] All existing equipped items are audited and updated

---

## Issue 26: No comprehensive tracking system for curses, environmental effects, and random events
**Labels:** `enhancement`, `game-mechanics`, `ai-integration`, `system-design`

### Description
The game lacks a broad overview process to ensure curses, environmental effects, random encounters, and ongoing events are properly tracked, processed, and trigger appropriate checks. These systems operate in isolation without a centralized AI-driven management system that can coordinate their interactions and ensure nothing is forgotten or overlooked.

### Current Problems

**1. Isolated Effect Systems**
- Curses exist but no systematic checking or progression
- Environmental effects (weather, magical areas, etc.) not tracked over time
- Random encounters happen but don't influence ongoing effects
- No coordination between different effect types

**2. Missing Oversight Process**
- No regular "heartbeat" system to check active effects
- AI doesn't proactively consider ongoing effects in decisions
- Effects can be forgotten or inconsistently applied
- No systematic way to trigger condition checks

**3. Limited Random Event Integration**
- Random encounters exist but aren't tied to environmental state
- Events don't influence or interact with existing effects
- No cascading effect system (one event triggering others)
- Missing narrative continuity between events

**4. No Centralized Effect Management**
- Effects scattered across different files and systems
- No unified data structure for tracking ongoing conditions
- Difficult to query "what effects are currently active?"
- No priority system for conflicting effects

### Current State Examples

**Curses**: Player might be cursed but it's only mentioned narratively, no systematic checks for:
- Curse progression over time
- Saving throw attempts to break free
- Curse interactions with other effects
- Environmental factors that worsen/improve curses

**Environmental Effects**: Magical areas, weather, terrain hazards exist but:
- No regular checks for ongoing exposure
- Effects don't evolve or change over time
- No interaction with player actions or story progression
- Missing environmental storytelling opportunities

**Random Encounters**: Events trigger but:
- Don't consider current environmental state
- Miss opportunities for effect synergy
- Lack narrative connection to ongoing situations
- No follow-up or consequence tracking

### Proposed Solution: AI-Driven Effect Management System

**Core Components:**

**1. Central Effect Registry** (`effect_registry.py`)
```json
{
  "activeEffects": [
    {
      "id": "curse_of_weakness_001",
      "type": "curse",
      "name": "Curse of Physical Weakness",
      "description": "Strength reduced by 2",
      "severity": "moderate",
      "duration": "until_removed",
      "triggers": ["combat_start", "ability_check"],
      "progression": {
        "nextCheck": "2024-01-15T14:00:00Z",
        "checkInterval": "24_hours",
        "worseningConditions": ["exposure_to_darkness", "failed_saving_throw"]
      },
      "source": "Cursed amulet from Ancient Tomb",
      "removalMethods": ["remove_curse_spell", "holy_water_ritual"]
    },
    {
      "id": "environmental_fog_002", 
      "type": "environmental",
      "name": "Mystical Fog",
      "description": "Heavy fog reduces visibility to 10 feet",
      "severity": "minor",
      "duration": "weather_dependent",
      "triggers": ["movement", "perception_check", "combat"],
      "areaEffect": "current_location",
      "interactions": ["amplifies_curse_effects", "blocks_sunlight"]
    }
  ]
}
```

**2. AI Effect Coordinator** (`ai_effect_coordinator.py`)
- Regularly queries all active effects
- Determines when checks or progressions should occur
- Coordinates effect interactions and synergies
- Generates prompts for AI to handle complex situations
- Manages effect priority and conflict resolution

**3. Effect Trigger System** (`effect_triggers.py`)
- Hooks into action handler, combat system, and time progression
- Automatically triggers relevant effect checks
- Handles cascading effects and chain reactions
- Logs effect history for narrative continuity

**4. Random Event Integration** (`enhanced_random_events.py`)
- Considers current environmental and curse state
- Generates contextually appropriate random events
- Creates synergistic encounters (e.g., fog + ambush)
- Tracks event consequences and follow-ups

### AI Integration Strategy

**1. Regular Effect Review Prompts**
```python
def generate_effect_review_prompt():
    active_effects = get_all_active_effects()
    return f"""
    EFFECT MANAGEMENT REVIEW:
    
    Current Active Effects:
    {format_effects_for_ai(active_effects)}
    
    Current Time: {get_game_time()}
    Current Location: {get_current_location()}
    Recent Player Actions: {get_recent_actions()}
    
    Please review and determine:
    1. Which effects need checks or progression?
    2. Are there any effect interactions to consider?
    3. Should any effects trigger narrative events?
    4. Are there opportunities for environmental storytelling?
    5. Should any new effects be introduced based on context?
    
    Respond with specific actions to take for each effect.
    """
```

**2. Contextual Effect Integration**
- Before major actions, AI considers all active effects
- Combat encounters factor in environmental conditions
- Dialogue and story beats reference ongoing conditions
- Effect descriptions evolve based on player actions

**3. Proactive Effect Management**
- AI suggests effect checks during appropriate moments
- Automatically reminds about forgotten effects
- Creates narrative opportunities from effect combinations
- Manages effect timing and pacing

### Implementation Features

**1. Effect Categories**
- **Curses**: Ongoing negative effects requiring removal
- **Environmental**: Location-based conditions affecting all creatures
- **Magical Areas**: Persistent spell effects in specific locations
- **Weather**: Natural conditions affecting visibility, movement, etc.
- **Random Events**: One-time or recurring special occurrences
- **Status Conditions**: Temporary character states (poisoned, blessed, etc.)

**2. Effect Interactions**
```python
effect_synergies = {
    "curse + darkness": "curse_effects_amplified",
    "fog + undead_encounter": "increased_surprise_chance", 
    "magical_area + spell_casting": "modified_spell_effects",
    "weather_storm + outdoor_travel": "navigation_penalties"
}
```

**3. Smart Trigger System**
- **Time-Based**: Daily checks, hourly progressions, seasonal changes
- **Action-Based**: Combat start, spell casting, ability checks
- **Location-Based**: Entering/leaving affected areas
- **Narrative-Based**: Story milestone triggers

**4. Effect Persistence**
- Save/load effect state between sessions
- Track effect history for narrative callbacks
- Maintain effect intensity based on story progression
- Handle effect removal and recovery narratives

### Use Case Examples

**Scenario 1: Cursed Character in Mystical Fog**
- Daily curse progression check
- Fog amplifies curse symptoms
- Random encounter with will-o'-wisps attracted to cursed aura
- AI weaves all elements into cohesive narrative

**Scenario 2: Weather Storm During Travel**
- Storm creates difficult terrain and visibility issues
- Triggers potential random encounters (bandits, shelter seeking)
- Affects camping and rest mechanics
- Creates atmosphere for story developments

**Scenario 3: Magical Area Exploration**
- Ongoing magical effects modify spell behavior
- Environmental storytelling through effect descriptions
- Hidden treasures revealed through effect interactions
- Potential curse acquisition from magical mishaps

### Technical Requirements

**1. Data Structures**
- Unified effect schema across all effect types
- Efficient querying and filtering of active effects
- Version control for effect definitions and changes
- Integration with existing character and location data

**2. AI Prompt Integration**
- System prompts include current effect summaries
- Context-aware effect considerations in all interactions
- Automated effect check reminders and triggers
- Effect-based story prompt generation

**3. Performance Considerations**
- Efficient effect polling and checking algorithms
- Minimal overhead for inactive effects
- Batch processing of multiple effect checks
- Optimized storage and retrieval systems

### Affected Files
- **New Files**: `effect_registry.py`, `ai_effect_coordinator.py`, `effect_triggers.py`
- **Enhanced Files**: `action_handler.py`, `dm_wrapper.py`, `party_tracker.json`
- **Integration Points**: `combat_manager.py`, `location_manager.py`, `system_prompt.txt`

### Benefits

**1. Immersive Gameplay**
- Consistent and persistent world state
- Rich environmental storytelling
- Meaningful consequences for player actions
- Dynamic and evolving game world

**2. AI Enhancement**
- Better context awareness for AI decisions
- Proactive effect management and storytelling
- Reduced chance of forgotten or inconsistent effects
- More sophisticated narrative generation

**3. System Reliability**
- Comprehensive effect tracking prevents oversight
- Automated checks ensure consistent application
- Clear audit trail of effect history
- Robust save/load functionality

**4. Enhanced Immersion**
- Effects feel like living parts of the world
- Natural progression and evolution of conditions
- Seamless integration between different game systems
- Rich, interconnected storytelling opportunities

### Implementation Priority
1. **Phase 1**: Basic effect registry and tracking system
2. **Phase 2**: AI coordinator and automated checking
3. **Phase 3**: Advanced interactions and synergies  
4. **Phase 4**: Full random event integration and environmental storytelling

This comprehensive system would transform isolated effect systems into a cohesive, AI-driven experience that ensures nothing falls through the cracks while creating rich, interconnected storytelling opportunities.

---

## Issue 27: AI creates non-existent area files when attempting location transitions [RESOLVED]
**Labels:** `bug`, `critical`, `ai-behavior`, `data-integrity`

### Description
The AI Dungeon Master can inadvertently attempt to create transitions to non-existent areas by providing invalid `areaConnectivityId` values in location transitions. When the game tries to load these non-existent area files (like `OC01.json`), it generates "File not found - creating first time" messages and fails the transition, breaking immersion and causing navigation errors.

### Current Behavior
- AI can specify any `areaConnectivityId` in `transitionLocation` actions
- System attempts to load area files that don't exist
- No validation against actual campaign area files
- Error messages like "File campaigns/Keep_of_Doom/OC01.json not found - creating first time"
- Failed transitions with cryptic error messages to users

### Root Cause
The `transitionLocation` action handler in `action_handler.py` doesn't validate that specified area connectivity IDs correspond to actual existing area files before attempting to load them.

### Example Case
In the Keep of Doom campaign, the AI set:
```json
"areaConnectivityId": ["OC01"]
```
in The Ruined Chapel (C03), but `OC01.json` doesn't exist in the campaign, causing transition failures when following Scout Elen's trail.

### Expected Behavior
- Validate `areaConnectivityId` values against existing campaign area files
- Prevent AI from creating transitions to non-existent areas
- Provide clear error messages when invalid areas are specified
- Gracefully handle invalid transitions without breaking game flow

### Proposed Solution: Campaign-Agnostic Area Validation

A simple, elegant validation that works with any campaign:

1. **Dynamic Area Discovery**: Scan the current campaign directory for existing `.json` area files
2. **Pre-transition Validation**: Check that any specified `areaConnectivityId` corresponds to an actual file
3. **Graceful Error Handling**: Return meaningful error messages instead of attempting to load non-existent files

### Technical Implementation

**In `action_handler.py`, before processing `transitionLocation`:**
```python
def validate_area_connectivity_id(area_connectivity_id, campaign_dir):
    """Validate that area connectivity ID corresponds to existing area file"""
    if not area_connectivity_id:
        return True  # Within-area transitions are always valid
    
    # Extract base area ID (handle formats like "G001-B07" -> "G001")
    base_area_id = area_connectivity_id.split('-')[0]
    area_file_path = os.path.join(campaign_dir, f"{base_area_id}.json")
    
    if not os.path.exists(area_file_path):
        return False
    
    return True
```

**Error Handling:**
```python
if area_connectivity_id and not validate_area_connectivity_id(area_connectivity_id, campaign_dir):
    return create_return(
        status="error", 
        message=f"Cannot transition to area '{area_connectivity_id}' - area file does not exist in campaign"
    )
```

### Benefits
- **Campaign Agnostic**: Works with any campaign structure without hard-coding area IDs
- **Simple Implementation**: Minimal code change with maximum protection
- **Clear Error Messages**: Users understand why transitions fail
- **Data Integrity**: Prevents corruption of campaign data
- **AI Learning**: Error messages help AI understand valid vs invalid transitions

### Affected Files
- `action_handler.py` - Add validation logic to `transitionLocation` handler
- Error handling and user feedback systems

### Alternative Solutions Considered
1. **Whitelist Validation**: Hard-coded list of valid areas (rejected - not campaign agnostic)
2. **Complex Graph System**: Full connectivity validation (rejected - over-engineered for this issue)
3. **AI Prompt Restrictions**: Instruct AI to avoid non-existent areas (rejected - doesn't prevent the underlying issue)

### Test Cases
1. Valid area transition (e.g., "G001-B07" where G001.json exists) - should succeed
2. Invalid area transition (e.g., "OC01" where OC01.json doesn't exist) - should fail gracefully
3. Within-area transition (no areaConnectivityId) - should always succeed
4. Malformed area ID (e.g., "INVALID") - should fail gracefully

This elegant solution provides robust protection against AI-created invalid area transitions while maintaining campaign flexibility and providing clear feedback when issues occur.

### RESOLUTION - IMPLEMENTED
**Date Resolved:** December 2024

**Changes Made:**
1. **Enhanced System Prompts** (`system_prompt.txt`):
   - Added CRITICAL AREA RESTRICTION RULES section
   - Explicit instructions: "NEVER create, invent, or reference area connectivity IDs that don't exist"
   - Clear guidance: "NEVER add new areaConnectivityId values to location data"
   - Validation requirements for area references

2. **Area Validation Function** (`action_handler.py`):
   - Added `validate_area_connectivity_id()` function
   - Pre-transition validation of area connectivity IDs
   - Campaign-agnostic validation (works with any campaign structure)
   - Graceful error handling with clear messages

3. **Transition Protection** (`action_handler.py`):
   - Added validation call before processing `transitionLocation` actions
   - Blocks transitions to non-existent areas with clear error messages
   - Maintains data integrity by preventing bad area IDs from being processed

**Result:** 
- AI can no longer create invalid area connections
- System validates area IDs before attempting file operations  
- Clear error messages guide AI to use only valid areas
- No more "File not found - creating first time" errors
- Maintains campaign flexibility while ensuring data integrity

**Test Results:**
- Valid areas (G001, SK001): ✅ Pass validation
- Invalid areas (OC01): ❌ Fail with clear error message  
- Within-area transitions: ✅ Always allowed
- Empty/null area IDs: ✅ Handled correctly

This implementation successfully prevents the root cause of the issue while providing clear feedback for both AI and users.

---

## Issue 28: Combat model passes introduction twice breaking immersion
**Labels:** `bug`, `combat`, `ai-behavior`, `immersion`

### Description
During combat encounters, the AI receives duplicate introductory information that breaks immersion. The issue occurs because both main.py and combat_manager.py send similar introductory content to the user, resulting in redundant narrative that repeats the same scene setup.

### Current Behavior
- Main.py sends a combat summary/introduction to the user
- Combat manager also sends its own initial introduction narrative  
- Player sees essentially the same information twice
- Creates redundant, immersion-breaking double exposition
- Breaks the narrative flow of combat encounters

### Example Flow
1. **Main.py**: Sends combat context summary describing the scene
2. **Combat Manager**: Also provides scene introduction with similar details
3. **Result**: Player reads the same scene setup information twice

### Expected Behavior
- Single, cohesive introduction to combat
- No duplicate scene descriptions
- Smooth transition from exploration to combat
- Clear narrative flow without repetition

### Root Cause
The system has two separate components that both attempt to provide combat introductions:
1. **Main.py**: Provides context summary when combat starts
2. **Combat Manager**: Generates its own introductory narrative

These operate independently without coordination, leading to redundant content.

### Proposed Solution
Choose one of these approaches:

**Option 1: Remove Main.py Summary**
- Have main.py not send a summary/introduction when combat starts
- Let combat manager handle all introductory narrative
- Cleaner single source of combat introduction

**Option 2: Remove Combat Manager Introduction**  
- Have combat manager skip initial scene setup
- Let main.py handle the introduction
- Combat manager focuses on action resolution only

**Option 3: Coordinate Introductions**
- Add flag to indicate if introduction was already provided
- Skip redundant introductions based on coordination

### Technical Implementation
The simplest fix would be Option 1 - modify main.py to not send combat summaries when transitioning to combat, allowing combat_manager.py to handle the complete introduction.

### Affected Files
- `main.py` - Combat transition and summary logic
- `combat_manager.py` - Combat introduction narrative
- Combat flow coordination between modules

### Benefits
- Eliminates redundant narrative content
- Improves immersion and narrative flow
- Cleaner combat encounter experience
- Reduced confusion for players
- More professional presentation

---

## Issue 29: Add clickable dice icons to web UI for automatic roll insertion
**Labels:** `enhancement`, `ui/ux`, `web-interface`, `quality-of-life`

### Description
The web UI should include clickable dice icons (d4, d6, d8, d10, d12, d20, d100) that automatically roll the dice and insert the result at the current cursor position in the input field. This would provide a convenient way for players to generate dice rolls without manually typing roll commands or using external dice tools.

### Current Behavior
- Players must manually type dice rolls like "I roll a 15" or "d20: 8"
- No visual dice rolling interface
- Players often use external dice apps or physical dice
- Manual entry prone to typos and requires switching between tools
- No visual feedback for the rolling action

### Proposed Enhancement
Add a dice toolbar with clickable icons for common dice types that:
1. Generate random roll results when clicked
2. Insert the formatted result at cursor position in the input field
3. Provide visual rolling animation/feedback
4. Support both individual dice and common combinations

### UI Design Mockup
```
Input Field: [Type your action here...                    ]
Dice Bar:    [d4] [d6] [d8] [d10] [d12] [d20] [d100] [2d6] [3d6] [1d20+5]
```

### Technical Requirements

**1. Dice Icon Interface**
- Clickable icons for each die type (d4, d6, d8, d10, d12, d20, d100)
- Common combinations (2d6, 3d6, 1d20+modifier)
- Custom dice builder for complex rolls (like 2d8+3)

**2. Roll Generation**
```javascript
function rollDice(sides, count = 1, modifier = 0) {
    let total = 0;
    let individual_rolls = [];
    
    for (let i = 0; i < count; i++) {
        let roll = Math.floor(Math.random() * sides) + 1;
        individual_rolls.push(roll);
        total += roll;
    }
    
    total += modifier;
    
    // Format: "d20: 15" or "2d6+3: [4,6]+3 = 13"
    return formatRollResult(sides, count, modifier, individual_rolls, total);
}
```

**3. Cursor Position Insertion**
```javascript
function insertAtCursor(inputElement, text) {
    let cursorPos = inputElement.selectionStart;
    let currentValue = inputElement.value;
    
    let newValue = currentValue.slice(0, cursorPos) + text + currentValue.slice(cursorPos);
    inputElement.value = newValue;
    
    // Move cursor to end of inserted text
    inputElement.setSelectionRange(cursorPos + text.length, cursorPos + text.length);
    inputElement.focus();
}
```

**4. Visual Feedback**
- Brief rolling animation when dice are clicked
- Different colors/styles for different dice types
- Sound effects (optional, toggle-able)
- Roll result briefly highlights before insertion

### Roll Format Options

**Simple Format**: `d20: 15`
**Detailed Format**: `d20: 15` or `2d6+3: [4,6]+3 = 13`
**Narrative Format**: `I roll a 15 on the d20`

Allow users to choose their preferred format in settings.

### Dice Types and Common Rolls

**Basic Dice**:
- d4, d6, d8, d10, d12, d20, d100

**Common Combinations**:
- 2d6 (damage, stats)
- 3d6 (ability scores)
- 1d20+5 (common attack/save modifier)
- 2d8+3 (weapon damage with modifier)

**Custom Builder**:
- Dropdown for die type
- Number input for quantity  
- Number input for modifier
- "Roll" button to execute

### User Experience Features

**1. Keyboard Shortcuts**
- Ctrl+D+[number] for quick die access (Ctrl+D+20 for d20)
- Tab completion for dice expressions

**2. Roll History**
- Small log of recent rolls below dice bar
- Click to re-insert previous rolls
- Clear history button

**3. Settings Panel**
- Choose roll result format
- Enable/disable sound effects
- Show/hide roll animations
- Customize dice shortcuts

### Mobile Responsiveness
- Touch-friendly dice buttons on mobile devices
- Swipe-able dice bar for smaller screens
- Appropriate button sizing for touch targets
- Responsive layout that works on tablets and phones

### Implementation Files

**Frontend (HTML/CSS/JavaScript)**:
- `templates/game_interface.html` - Add dice bar HTML structure
- `static/css/dice-interface.css` - Styling for dice icons and animations
- `static/js/dice-roller.js` - Core dice rolling functionality
- `static/js/cursor-insertion.js` - Text insertion at cursor position
- `static/images/dice/` - Dice icon assets (SVG recommended)

**Backend Integration**:
- No backend changes required - purely client-side enhancement
- Dice results inserted as text, processed normally by existing system

### Example User Workflow

1. **Player types**: "I attack with my sword"
2. **Player clicks**: [d20] button  
3. **System rolls**: 17
4. **Text becomes**: "I attack with my sword d20: 17"
5. **Player adds**: " and if that hits, I roll damage"
6. **Player clicks**: [1d8+3] button
7. **System rolls**: 6+3=9  
8. **Final text**: "I attack with my sword d20: 17 and if that hits, I roll damage 1d8+3: 9"

### Advanced Features (Future Enhancements)

**1. Advantage/Disadvantage Support**
- Ctrl+click for advantage (roll twice, take higher)
- Shift+click for disadvantage (roll twice, take lower)
- Format: "d20 (advantage): [12,18] = 18"

**2. Dice Pool Support**  
- Multiple dice with individual results
- Success counting for systems that use it
- Exploding dice mechanics

**3. Character Sheet Integration**
- Pre-configured buttons based on character stats
- "Attack Roll" button that automatically includes attack bonus
- "Saving Throw" buttons with character modifiers

**4. Macro System**
- Save frequently used roll combinations
- Custom buttons for character-specific rolls
- Import/export roll macros

### Accessibility Features
- Screen reader support for dice button labels
- High contrast mode for dice icons
- Keyboard navigation through dice options
- Alt text for all dice imagery

### Benefits

**Player Experience**:
- Faster, more convenient dice rolling
- Reduces typing errors and formatting issues
- Visual feedback makes rolling feel more tactile
- Eliminates need for external dice tools

**Game Flow**:
- Faster combat resolution
- More consistent roll formatting
- Reduces interruptions for manual dice rolling
- Maintains immersion within the web interface

**Accessibility**:
- Helpful for players with motor difficulties
- Consistent formatting improves readability
- Visual interface aids players who struggle with text input

### Implementation Priority
1. **Phase 1**: Basic dice icons (d20, d6, d8, d10, d12) with simple insertion
2. **Phase 2**: Common combinations (2d6, 3d6) and formatting options  
3. **Phase 3**: Custom dice builder and roll history
4. **Phase 4**: Advanced features (advantage/disadvantage, macros)

This enhancement would significantly improve the user experience for the web interface while maintaining compatibility with the existing text-based game system.

---

## Issue 30: AI Combat Helper for automated modifier and resistance calculation
**Labels:** `enhancement`, `ai-integration`, `combat`, `game-mechanics`, `automation`

### Description
Implement an AI-powered combat helper that automatically scans character sheets and calculates all modifiers, resistances, immunities, and special abilities. This helper AI would inject comprehensive combat information into the DM notes passed to the main AI model, ensuring accurate and complete consideration of all character stats during combat encounters.

### Current Problems

**1. Manual Modifier Tracking**
- DM AI must manually calculate attack bonuses, damage modifiers, and AC
- Easy to miss temporary effects, equipment bonuses, or special abilities
- No centralized system for tracking all active modifiers
- Combat calculations prone to human error

**2. Complex Resistance/Immunity System**
- Characters may have resistances from multiple sources (equipment, spells, abilities)
- Conditional resistances (e.g., only vs certain damage types or creatures)
- Vulnerability calculations often overlooked
- No systematic checking of damage type interactions

**3. Incomplete Ability Consideration**
- Special abilities from equipment not always factored into combat
- Class features with combat implications missed
- Temporary effects and buffs forgotten during combat
- Passive abilities not consistently applied

**4. Inconsistent Combat Adjudication**
- Manual calculations lead to inconsistent results
- DM may not be aware of all character capabilities
- Combat balance affected by missed modifiers
- Player abilities not fully utilized

### Proposed Solution: AI Combat Helper System

**Core Architecture:**

**1. Character Sheet Analyzer** (`combat_character_analyzer.py`)
```python
class CombatCharacterAnalyzer:
    def analyze_character(self, character_data):
        """Comprehensive analysis of character combat capabilities"""
        return {
            'attack_modifiers': self.calculate_attack_modifiers(character_data),
            'damage_modifiers': self.calculate_damage_modifiers(character_data),
            'armor_class': self.calculate_ac_breakdown(character_data),
            'resistances': self.analyze_resistances(character_data),
            'immunities': self.analyze_immunities(character_data),
            'vulnerabilities': self.analyze_vulnerabilities(character_data),
            'special_abilities': self.extract_combat_abilities(character_data),
            'temporary_effects': self.process_active_effects(character_data),
            'saving_throws': self.calculate_save_modifiers(character_data)
        }
```

**2. Modifier Calculator Engine**
```python
def calculate_attack_modifiers(self, character_data):
    """Calculate all sources of attack bonuses"""
    modifiers = {
        'melee_attack': 0,
        'ranged_attack': 0,
        'spell_attack': 0,
        'sources': []
    }
    
    # Base ability modifiers
    str_mod = get_ability_modifier(character_data['abilities']['strength'])
    dex_mod = get_ability_modifier(character_data['abilities']['dexterity'])
    
    # Proficiency bonus
    prof_bonus = character_data['proficiencyBonus']
    
    # Equipment bonuses
    for item in character_data.get('equipment', []):
        if item.get('equipped') and 'attack_bonus' in item:
            modifiers['sources'].append(f"{item['item_name']}: +{item['attack_bonus']}")
    
    # Class features
    for feature in character_data.get('classFeatures', []):
        if 'attack' in feature.get('description', '').lower():
            modifiers['sources'].append(f"Class Feature: {feature['name']}")
    
    # Temporary effects
    for effect in character_data.get('temporaryEffects', []):
        if 'attack' in effect.get('description', '').lower():
            modifiers['sources'].append(f"Temporary: {effect['name']}")
    
    return modifiers
```

**3. Resistance/Immunity Processor**
```python
def analyze_resistances(self, character_data):
    """Comprehensive resistance analysis from all sources"""
    resistances = {
        'damage_types': [],
        'conditions': [],
        'sources': {},
        'conditional': []
    }
    
    # Check racial traits
    for trait in character_data.get('racialTraits', []):
        if 'resistance' in trait.get('description', '').lower():
            resistances['sources'][trait['name']] = extract_resistance_info(trait)
    
    # Check equipped items
    for item in character_data.get('equipment', []):
        if item.get('equipped') and 'special_abilities' in item:
            for ability in item['special_abilities']:
                if 'resistance' in ability.get('description', '').lower():
                    resistances['sources'][f"Equipment: {item['item_name']}"] = ability
    
    # Check temporary effects
    for effect in character_data.get('temporaryEffects', []):
        if 'resistance' in effect.get('description', '').lower():
            resistances['sources'][f"Temporary: {effect['name']}"] = effect
    
    return resistances
```

**4. DM Note Generator**
```python
def generate_combat_summary(self, character_analysis):
    """Generate comprehensive combat summary for DM AI"""
    summary = f"""
    COMBAT HELPER ANALYSIS FOR {character_analysis['name']}:
    
    ATTACK CAPABILITIES:
    - Melee Attack: +{character_analysis['attack_modifiers']['melee_attack']}
    - Ranged Attack: +{character_analysis['attack_modifiers']['ranged_attack']}
    - Spell Attack: +{character_analysis['attack_modifiers']['spell_attack']}
    
    ARMOR CLASS: {character_analysis['armor_class']['total']}
    - Base Armor: {character_analysis['armor_class']['base']}
    - DEX Modifier: +{character_analysis['armor_class']['dex_mod']}
    - Shield: +{character_analysis['armor_class']['shield']}
    - Other Bonuses: +{character_analysis['armor_class']['other']}
    
    DAMAGE RESISTANCES:
    {format_resistances(character_analysis['resistances'])}
    
    DAMAGE IMMUNITIES:
    {format_immunities(character_analysis['immunities'])}
    
    DAMAGE VULNERABILITIES:
    {format_vulnerabilities(character_analysis['vulnerabilities'])}
    
    ACTIVE SPECIAL ABILITIES:
    {format_special_abilities(character_analysis['special_abilities'])}
    
    TEMPORARY EFFECTS:
    {format_temporary_effects(character_analysis['temporary_effects'])}
    
    SAVING THROW MODIFIERS:
    {format_saving_throws(character_analysis['saving_throws'])}
    """
    return summary
```

### Integration with Main System

**1. Combat Manager Integration**
```python
# In combat_manager.py
from combat_character_analyzer import CombatCharacterAnalyzer

def initiate_combat(self, participants):
    analyzer = CombatCharacterAnalyzer()
    
    # Analyze all participants
    combat_analysis = {}
    for character in participants:
        combat_analysis[character['name']] = analyzer.analyze_character(character)
    
    # Generate DM notes with complete combat information
    dm_notes = self.generate_enhanced_dm_notes(combat_analysis)
    
    # Pass to main AI with comprehensive combat context
    return self.start_combat_with_analysis(dm_notes, combat_analysis)
```

**2. Real-time Updates**
```python
def update_character_analysis(self, character_name, changes):
    """Re-analyze character when changes occur during combat"""
    updated_character = load_character(character_name)
    new_analysis = self.analyzer.analyze_character(updated_character)
    
    # Update DM notes with new information
    updated_notes = self.generate_updated_dm_notes(new_analysis)
    
    return updated_notes
```

### Advanced Features

**1. Conditional Logic Processing**
```python
def process_conditional_abilities(self, character_data, combat_context):
    """Handle abilities that activate under specific conditions"""
    conditional_bonuses = []
    
    for ability in character_data.get('classFeatures', []):
        if 'when' in ability.get('description', '').lower():
            conditions = extract_conditions(ability['description'])
            if check_conditions(conditions, combat_context):
                conditional_bonuses.append({
                    'ability': ability['name'],
                    'bonus': extract_bonus(ability['description']),
                    'condition': conditions
                })
    
    return conditional_bonuses
```

**2. Equipment Synergy Detection**
```python
def detect_equipment_synergies(self, equipped_items):
    """Identify item combinations that provide additional bonuses"""
    synergies = []
    
    # Check for armor + weapon combinations
    armor_pieces = [item for item in equipped_items if item.get('item_type') == 'armor']
    weapons = [item for item in equipped_items if item.get('item_type') == 'weapon']
    
    for armor in armor_pieces:
        for weapon in weapons:
            if check_synergy(armor, weapon):
                synergies.append(get_synergy_bonus(armor, weapon))
    
    return synergies
```

**3. Smart Damage Calculation**
```python
def calculate_damage_after_resistances(self, base_damage, damage_type, target_resistances):
    """Automatically apply resistances/immunities to damage"""
    if damage_type in target_resistances['immunities']:
        return 0
    elif damage_type in target_resistances['resistances']:
        return base_damage // 2
    elif damage_type in target_resistances['vulnerabilities']:
        return base_damage * 2
    else:
        return base_damage
```

### Enhanced DM Note Examples

**Basic Combat Summary:**
```
COMBAT HELPER ANALYSIS FOR NORN:

ATTACK CAPABILITIES:
- Longsword Attack: +8 (STR +3, Prof +3, Weapon +2)
- Ranged Attack: +5 (DEX +2, Prof +3)

ARMOR CLASS: 19
- Chain Mail: 16 (Base)
- Shield: +2
- Defense Fighting Style: +1

DAMAGE RESISTANCES:
- Necrotic (Knight's Heart Amulet)

SPECIAL COMBAT ABILITIES:
- Second Wind: 1/Short Rest (1d10+5 healing)
- Action Surge: 1/Short Rest (extra action)
- Extra Attack: 2 attacks per Attack action

TEMPORARY EFFECTS:
- Blessing of Protection: +2 AC vs undead (4 hours remaining)
```

**Conditional Abilities Alert:**
```
CONDITIONAL COMBAT BONUSES AVAILABLE:
- Great Weapon Master: -5 attack/+10 damage (when using heavy weapons)
- Sentinel: Opportunity attacks stop movement
- Defense Style: +1 AC only when wearing armor ✓ ACTIVE
```

### Technical Implementation

**1. Data Structure Requirements**
```json
{
  "combat_analysis": {
    "character_name": "Norn",
    "attack_bonuses": {
      "melee": {
        "total": 8,
        "breakdown": {
          "strength": 3,
          "proficiency": 3,
          "weapon_enhancement": 2
        }
      }
    },
    "damage_resistances": {
      "necrotic": {
        "source": "Knight's Heart Amulet",
        "type": "equipment",
        "duration": "permanent"
      }
    },
    "active_abilities": [
      {
        "name": "Extra Attack",
        "description": "Make 2 attacks when taking Attack action",
        "uses_remaining": "unlimited"
      }
    ]
  }
}
```

**2. Real-time Monitoring**
```python
class CombatEffectMonitor:
    def monitor_character_changes(self, character_name):
        """Monitor for changes that affect combat calculations"""
        previous_state = self.get_cached_analysis(character_name)
        current_character = load_character(character_name)
        new_analysis = self.analyzer.analyze_character(current_character)
        
        if self.has_significant_changes(previous_state, new_analysis):
            self.update_dm_notes(character_name, new_analysis)
            self.cache_analysis(character_name, new_analysis)
```

### Integration Points

**Affected Files:**
- **New Files**: `combat_character_analyzer.py`, `modifier_calculator.py`, `resistance_processor.py`
- **Enhanced Files**: `combat_manager.py`, `dm_wrapper.py`, `system_prompt.txt`
- **Integration Points**: `action_handler.py`, `update_character_info.py`

**AI Prompt Enhancement:**
```python
def enhance_dm_prompt_with_combat_analysis(base_prompt, combat_analysis):
    """Add detailed combat information to DM prompt"""
    enhanced_prompt = f"""
    {base_prompt}
    
    COMBAT HELPER ANALYSIS:
    {format_combat_analysis(combat_analysis)}
    
    IMPORTANT: Use this analysis to ensure accurate combat calculations.
    All attack bonuses, resistances, and special abilities are pre-calculated.
    """
    return enhanced_prompt
```

### Benefits

**1. Accuracy and Consistency**
- Eliminates manual calculation errors
- Ensures all character abilities are considered
- Consistent application of resistances and immunities
- Comprehensive tracking of temporary effects

**2. Enhanced Combat Experience**
- Players' abilities are fully utilized
- Combat encounters are properly balanced
- Special equipment and abilities have meaningful impact
- Reduced confusion about character capabilities

**3. DM AI Enhancement**
- Complete character information available at all times
- Intelligent damage calculations
- Automatic consideration of conditional bonuses
- Real-time updates for character changes

**4. System Reliability**
- Automated checking prevents oversight
- Standardized calculation methods
- Audit trail of all modifiers and sources
- Easy debugging of combat issues

### Future Enhancements

**1. Predictive Analysis**
- Suggest optimal actions based on character capabilities
- Predict damage outcomes with resistance calculations
- Recommend tactical decisions based on active abilities

**2. Multi-character Synergy**
- Analyze party-wide bonuses and synergies
- Detect beneficial spell combinations
- Optimize group tactics and positioning

**3. Dynamic Encounter Balancing**
- Adjust encounter difficulty based on party capabilities
- Suggest monster tactics that counter party strengths
- Balance action economy considerations

### Implementation Priority
1. **Phase 1**: Basic modifier calculation and resistance processing
2. **Phase 2**: Integration with combat manager and DM notes
3. **Phase 3**: Conditional logic and equipment synergies
4. **Phase 4**: Advanced prediction and optimization features

This comprehensive combat helper would transform the D&D experience by ensuring every character ability, resistance, and modifier is properly considered in every combat encounter, leading to more accurate, engaging, and fair gameplay.