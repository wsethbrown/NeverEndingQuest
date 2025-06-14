# Character Effects Implementation Plan

## Overview
This document outlines the plan to implement a comprehensive character effects tracking system that properly separates temporary magical effects, injuries, equipment bonuses, and class feature usage tracking.

## Current Issues
1. **Mixed Content Types**: Class abilities, damage tracking, and equipment bonuses are incorrectly mixed in `temporaryEffects`
2. **Inconsistent Duration Formats**: No standardized expiration timestamps or time tracking
3. **No Equipment Effect Calculation**: Equipment bonuses not automatically calculated from equipped items
4. **Missing Class Feature Usage**: No tracking of limited-use abilities like Second Wind

## Implementation Phases

### Phase 1: Update Character Schema (`char_schema.json`)
**Goal**: Establish the data structure foundation for the new effects system

1. **Add New Arrays to Schema**:
   - `injuries`: Array for physical damage/wounds tracking
   - `equipment_effects`: Auto-calculated array from equipped items (read-only)
   - Update `temporaryEffects`: Restrict to magical/spell effects only
   - Enhance `classFeatures`: Add usage tracking structure

2. **Enhanced Equipment Item Structure**:
   ```json
   {
     "item_name": "Knight's Heart Amulet",
     "item_type": "miscellaneous",
     "equipped": true,
     "effects": [
       {
         "type": "resistance",
         "target": "fear",
         "value": null,
         "description": "Resistance to fear effects"
       },
       {
         "type": "resistance", 
         "target": "necrotic",
         "value": null,
         "description": "Resistance to necrotic damage from Sir Garran's curse"
       }
     ]
   }
   ```

3. **Class Feature Usage Structure**:
   ```json
   {
     "name": "Second Wind",
     "description": "Once per short rest, regain 1d10 + fighter level HP",
     "usage": {
       "current": 0,
       "max": 1,
       "refreshOn": "shortRest"
     }
   }
   ```

4. **Temporary Effects Structure** (magical only):
   ```json
   {
     "name": "Blessing of the Forest Guardian",
     "description": "Advantage on saving throws against fear",
     "duration": "24 hours",
     "expiration": "1492-03-03T06:30:00",
     "source": "Forest Guardian"
   }
   ```

5. **Injuries Structure**:
   ```json
   {
     "type": "wound",
     "description": "Piercing wound from giant rat bite",
     "damage": 4,
     "healingRequired": true,
     "source": "Giant Rat Attack"
   }
   ```

### Phase 2: Create Character Effects Validator Script
**Goal**: Build the AI-powered effects management system

1. **Create `character_effects_validator.py`**:
   - Duplicate from `character_validator.py`
   - Remove AC validation logic
   - Add effects categorization AI logic
   - Add duration standardization
   - Add equipment effects calculation
   - Add class feature usage setup

2. **Key Functions**:
   - `categorize_effects()`: AI-powered migration of mixed effects
   - `calculate_equipment_effects()`: Scan equipped items for active effects
   - `standardize_durations()`: Convert text durations to timestamps
   - `setup_class_feature_usage()`: Initialize usage tracking

3. **AI Prompts**:
   - Effect categorization prompt
   - Duration interpretation prompt
   - Equipment effect extraction prompt

### Phase 3: Update Existing Character Data
**Goal**: Clean up existing character files using the new validator

1. **Migrate Norn's temporaryEffects**:
   - "Second Wind" → Move to classFeatures with usage tracking
   - Damage entries → Move to new injuries array
   - Equipment effects → Auto-populate from equipped items
   - Keep only legitimate temporary magical effects

2. **Standardize All Durations**:
   - Use game world time from `party_tracker.json`
   - Convert "24 hours" → ISO timestamp
   - Handle special cases ("until removed", "until healed")

3. **Validate All Characters**:
   - Run effects validator on all character files
   - Ensure schema compliance
   - Log all migrations for review

### Phase 4: Integration into Update Pipeline
**Goal**: Seamlessly integrate effects management into existing systems

1. **Modify `update_character_info.py`**:
   ```python
   # After existing AC validation (line 336)
   try:
       effects_validator = AICharacterEffectsValidator()
       effects_validated_data, effects_success = effects_validator.validate_character_effects_safe(character_path)
       
       if effects_success and effects_validator.corrections_made:
           print(f"{GREEN}Character effects auto-validated with corrections: {effects_validator.corrections_made}{RESET}")
   except Exception as e:
       print(f"{ORANGE}Warning: Character effects validation error: {str(e)}{RESET}")
   ```

2. **Add Time-Based Cleanup**:
   - Hook into `update_world_time.py`
   - Check and expire effects when time advances
   - Log expired effects for player awareness

3. **Equipment Change Handling**:
   - Recalculate equipment_effects on any equipment change
   - Automatic update when items are equipped/unequipped

### Phase 5: Testing and Validation
**Goal**: Ensure system reliability and correctness

1. **Unit Tests**:
   - Schema validation tests
   - Effect categorization tests
   - Duration calculation tests
   - Equipment effect tests

2. **Integration Tests**:
   - Full character update flow
   - Time advancement and expiration
   - Equipment changes
   - Class feature usage and refresh

3. **Manual Testing**:
   - Test with Norn's complex character file
   - Verify all effects properly categorized
   - Confirm equipment effects calculate correctly
   - Test time-based expiration

## Expected Outcomes

1. **Clean Separation**: Temporary effects, injuries, equipment bonuses, and class features properly separated
2. **Automatic Management**: Equipment effects auto-calculated, temporary effects auto-expire
3. **Usage Tracking**: Limited-use class features properly tracked and refreshed
4. **Time Integration**: Effects expire based on actual game time progression
5. **Data Integrity**: All character files comply with enhanced schema

## Future Enhancements (Not in Current Scope)

1. **Combat Round Tracking**: Special handling for round-based effects during combat
2. **Condition Stacking**: Rules for multiple instances of same effect
3. **Effect Interactions**: Complex effect combinations and overrides
4. **UI Indicators**: Visual representation of active effects and durations

## Implementation Timeline

- Phase 1: 1-2 hours (Schema updates)
- Phase 2: 2-3 hours (Effects validator creation)
- Phase 3: 1 hour (Data migration)
- Phase 4: 1-2 hours (Integration)
- Phase 5: 1-2 hours (Testing)

Total estimated time: 6-10 hours

## Success Criteria

1. All character files pass enhanced schema validation
2. Effects properly categorized into appropriate arrays
3. Equipment effects automatically calculated from equipped items
4. Temporary effects expire based on game time
5. Class features track usage and refresh appropriately
6. No regression in existing functionality