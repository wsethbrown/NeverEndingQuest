# Module and Party Tracker Refactoring Plan

## Overview
This document outlines the comprehensive refactoring of the module system to create clean separation between module-specific content and world-level settings, plus implementation of a generic calendar system.

## Problem Statement

### Current Issues
1. **Module JSON Bloat**: World-level settings are mixed with module-specific content
2. **Copyright Concerns**: Using Forgotten Realms calendar month names
3. **Architectural Confusion**: Unclear separation between world, campaign, and module levels
4. **Schema Inconsistency**: Module schema requires world-level information unnecessarily

### Goals
1. **Clean Separation**: Module files contain only module-relevant content
2. **Generic Calendar**: Non-copyrighted month names for universal use
3. **Future-Proofing**: Prepare for world/campaign file implementation
4. **Schema Clarity**: Clear, focused schemas for each component

## Calendar System Implementation

### Research Findings
- **D&D Standard**: 7-day weeks are canonical
- **Tolkien Months**: Under copyright protection until 2044+, avoid use
- **Generic Approach**: Custom month names avoid copyright issues

### Proposed Calendar Structure
```json
{
  "months": [
    "Firstmonth",    // January equivalent - New beginnings
    "Coldmonth",     // February equivalent - Deepest winter
    "Thawmonth",     // March equivalent - Winter's end
    "Springmonth",   // April equivalent - Spring awakening
    "Bloommonth",    // May equivalent - Flowers and growth
    "Sunmonth",      // June equivalent - Summer's arrival
    "Heatmonth",     // July equivalent - Peak summer
    "Harvestmonth",  // August equivalent - Early harvest
    "Autumnmonth",   // September equivalent - Fall begins
    "Fademonth",     // October equivalent - Leaves fall
    "Frostmonth",    // November equivalent - First frosts
    "Yearend"        // December equivalent - Year's conclusion
  ],
  "daysPerWeek": 7,
  "weeksPerMonth": 4,
  "daysPerMonth": 28,
  "daysPerYear": 336
}
```

### Calendar Rationale
- **Predictable**: Each month has exactly 4 weeks (28 days)
- **Generic**: No trademark/copyright issues
- **Descriptive**: Month names reflect seasonal progression
- **D&D Compatible**: Maintains 7-day week structure

## Module Schema Refactoring

### Current Schema Issues
The `worldSettings` section contains:
- `worldName`, `era`, `cosmology` - World-level
- `planarConnections`, `majorDeities` - World-level  
- `majorPowers`, `predominantRaces` - World-level
- `magicPrevalence`, `currentConflicts` - Mixed world/module

### New Module Schema Structure

#### REMOVE Entirely
```json
"worldSettings": {
  // All world-level content removed
}
```

#### ADD Optional Section
```json
"moduleConflicts": {
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "conflictName": {"type": "string"},
      "description": {"type": "string"},
      "scope": {"type": "string", "enum": ["local", "regional"]},
      "impact": {"type": "string"}
    },
    "required": ["conflictName", "description", "scope", "impact"]
  }
}
```

#### KEEP Unchanged
- `moduleMetadata` - Module publication info
- `mainPlot` - Core module content  
- `factions` - Module-specific factions
- `worldMap` - Module areas/regions
- `timelineEvents` - Module-specific events

### Schema Migration Strategy

#### Before (Current)
```json
{
  "moduleName": "Keep of Doom",
  "worldSettings": {
    "worldName": "Shadowvale",
    "era": "Late Age of Turmoil",
    "cosmology": "Great Wheel",
    "currentConflicts": [
      "World conflict 1",
      "World conflict 2", 
      "Module conflict 1"
    ]
  }
}
```

#### After (Refactored)
```json
{
  "moduleName": "Keep of Doom",
  "moduleConflicts": [
    {
      "conflictName": "Haunting of Shadowfall Keep",
      "description": "Supernatural activity threatens local stability",
      "scope": "local",
      "impact": "Affects party progression and NPC interactions"
    }
  ]
}
```

## Party Tracker Schema Updates

### Current Party Schema Issues
- Month field uses Forgotten Realms names
- No validation for month values
- Schema doesn't enforce calendar consistency

### Updated Party Schema

#### Month Field Enhancement
```json
"month": {
  "type": "string",
  "enum": [
    "Firstmonth", "Coldmonth", "Thawmonth", "Springmonth",
    "Bloommonth", "Sunmonth", "Heatmonth", "Harvestmonth", 
    "Autumnmonth", "Fademonth", "Frostmonth", "Yearend"
  ],
  "description": "Current month using generic fantasy calendar"
}
```

#### Additional Validations
```json
"day": {
  "type": "integer",
  "minimum": 1,
  "maximum": 28,
  "description": "Day of month (1-28 in standardized calendar)"
}
```

## File-by-File Implementation Plan

### 1. Party Tracker Updates

#### `party_tracker.json`
**Current**: `"month": "Ches"`
**Update**: `"month": "Springmonth"` (March equivalent)

#### `party_schema.json`
- Add month enum with 12 generic names
- Update day validation (1-28)
- Update descriptions to reference generic calendar

### 2. Module Schema Updates

#### `module_schema.json`
**Remove**:
- Entire `worldSettings` section
- `worldSettings` from required fields

**Add**:
- Optional `moduleConflicts` section
- Proper schema validation for conflicts

#### `modules/Keep_of_Doom/Keep_of_Doom_module.json`
**Remove Sections**:
- `worldSettings.worldName`
- `worldSettings.era` 
- `worldSettings.cosmology`
- `worldSettings.planarConnections`
- `worldSettings.majorDeities`
- `worldSettings.majorPowers`
- `worldSettings.predominantRaces`
- `worldSettings.magicPrevalence`

**Extract Local Conflicts**:
From `worldSettings.currentConflicts`, keep only:
- Conflicts directly affecting module gameplay
- Local/regional scope conflicts
- NPC faction conflicts within module

**Convert to `moduleConflicts`**:
```json
"moduleConflicts": [
  {
    "conflictName": "Order of Silver Vigil vs Local Autonomy",
    "description": "Zealous knights clash with local authorities over jurisdiction",
    "scope": "regional", 
    "impact": "Affects party's relationship with both factions"
  },
  {
    "conflictName": "Black Banner Infiltration",
    "description": "Secret agents spread chaos and misinformation",
    "scope": "local",
    "impact": "Creates trust issues and false information for party"
  }
]
```

### 3. Module Builder Updates

#### `module_builder.py`
**Remove Prompts**:
- World name generation
- Era/cosmology selection
- Deity creation
- Major powers definition
- Race prevalence
- Magic level setting

**Add Prompts**:
- Local conflict identification
- Module-specific faction focus
- Regional scope definition

#### `module_generator.py` 
**Update Generation Logic**:
- Remove world-building sections
- Focus on module-specific content
- Generate targeted conflicts
- Emphasize playable content over world lore

### 4. Related File Updates

#### Any files referencing old schema
- Update imports and validation
- Modify generation prompts
- Adjust error handling

## Implementation Order

### Phase 1: Schema Updates
1. Update `party_schema.json` with month enum
2. Update `module_schema.json` to remove worldSettings
3. Test schema validation

### Phase 2: Data Migration  
1. Update `party_tracker.json` month value
2. Refactor `Keep_of_Doom_module.json`
3. Validate against new schemas

### Phase 3: Builder Updates
1. Modify `module_builder.py` prompts
2. Update `module_generator.py` logic
3. Test module generation workflow

### Phase 4: Testing & Validation
1. Generate new test module
2. Validate party tracker functionality
3. Confirm calendar system works
4. Test module loading/validation

## Benefits of This Refactoring

### Immediate Benefits
- **Cleaner Modules**: Focus on playable content only
- **Legal Safety**: No copyright-infringing month names
- **Schema Clarity**: Clear separation of concerns
- **File Size**: Smaller, more focused module files

### Future Benefits
- **World Files**: Easy to implement world/campaign level
- **Module Reusability**: Modules work in any setting
- **Scalability**: Clear architecture for expansion
- **Maintenance**: Easier to update and debug

### Development Benefits
- **Generator Efficiency**: Faster module creation
- **Validation**: Clear error messages
- **Documentation**: Self-documenting schemas
- **Testing**: Focused unit tests possible

## Migration Strategy for Existing Modules

### Automated Migration
1. **Extract Conflicts**: Script to identify module-relevant conflicts
2. **Remove Sections**: Automated removal of world-level content
3. **Validate**: Ensure resulting module passes new schema
4. **Backup**: Preserve original files before migration

### Manual Review Required
- **Conflict Relevance**: Human review of which conflicts matter
- **Faction Integration**: Ensure factions remain coherent
- **Plot Dependencies**: Verify plot doesn't reference removed content

## Testing Strategy

### Unit Tests
- Schema validation for all file types
- Calendar date calculations
- Module loading/parsing

### Integration Tests  
- Complete module generation workflow
- Party tracker time progression
- Cross-file reference validation

### User Acceptance Tests
- Generate complete module from scratch
- Load and play existing module
- Verify all functionality preserved

## Risk Mitigation

### Backup Strategy
- **Git Commits**: Incremental commits for each phase
- **File Backups**: Preserve original JSON files
- **Schema Versioning**: Maintain old schemas during transition

### Rollback Plan
- **Phase Isolation**: Each phase can be independently reverted
- **Data Preservation**: Original data extractable from backups
- **Gradual Migration**: Test thoroughly before each phase

## Success Criteria

### Technical Success
- ✅ All modules validate against new schema
- ✅ Party tracker uses generic calendar
- ✅ Module builder generates focused content
- ✅ No functionality lost in refactoring

### Architectural Success  
- ✅ Clear separation between module and world level
- ✅ Schemas enforce proper boundaries
- ✅ System ready for world/campaign file addition
- ✅ Module reusability across different settings

### Legal/Copyright Success
- ✅ No copyrighted content in calendar system
- ✅ Generic month names avoid trademark issues
- ✅ System legally safe for distribution
- ✅ Future-proof against copyright changes

This refactoring creates a solid foundation for the module-centric architecture while addressing copyright concerns and improving system clarity.