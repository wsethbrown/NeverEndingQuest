# Closed GitHub Issues

This file contains GitHub issues that have been resolved or closed.

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

## Issue 2: Duplicate class features and special abilities in character data [CLOSED]
**Labels:** `bug`, `data-integrity`
**Date Closed:** 2025-05-31

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

## Issue 3: Currency can go negative without validation [CLOSED]
**Labels:** `bug`, `validation`
**Date Closed:** 2025-06-01

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

## Issue 20: Cannot determine equipped items and accurate AC calculation [CLOSED]
**Labels:** `bug`, `enhancement`
**Date Closed:** 2025-06-03

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