# DM System Testing Plan

## Overview
This document provides a comprehensive testing framework for the DungeonMasterAI system, covering all available actions, expected response formats, and validation requirements.

## DM Response Format Specification

### Required JSON Structure
All DM responses MUST follow this exact format:

```json
{
  "narration": "Descriptive text, dialogue, and narrative content shown to players",
  "actions": [
    {
      "action": "actionType",
      "parameters": {
        // action-specific parameters
      }
    }
  ]
}
```

### Format Rules
1. **Single Object Rule**: Always return ONE JSON object, never multiple
2. **Narration Field**: Required, can be empty string if no text needed
3. **Actions Array**: Required, can be empty array [] if no actions
4. **Parameter Types**: Parameters can be strings, numbers, objects, or arrays
5. **No Code Blocks**: Response should be raw JSON, not wrapped in ```json blocks

## Available DM Actions

### 1. Character Management

#### updateCharacterInfo
Updates character stats, inventory, abilities, conditions, spell slots.

**Parameters:**
- `characterName` (string): Name of character to update
- `changes` (string or object): JSON string containing changes

**Example:**
```json
{
  "action": "updateCharacterInfo",
  "parameters": {
    "characterName": "Norn",
    "changes": "{\"hitPoints\": 35, \"inventory\": {\"add\": [\"Healing Potion\"]}}"
  }
}
```

**Valid Changes:**
- Hit points, max hit points
- Experience points
- Ability scores
- Inventory (add/remove items)
- Spell slots (current/max)
- Conditions (poisoned, exhausted, etc.)
- Equipment slots
- Currency (gold, silver, copper)

#### levelUp
Initiates character level advancement process.

**Parameters:**
- `entityName` (string): Character name
- `newLevel` (number): Target level

**Example:**
```json
{
  "action": "levelUp",
  "parameters": {
    "entityName": "Norn",
    "newLevel": 6
  }
}
```

### 2. Location and Movement

#### transitionLocation
Moves party to adjacent location within module.

**Parameters:**
- `newLocation` (string): Destination location ID (e.g., "A01", "B05", "C03")

**Example:**
```json
{
  "action": "transitionLocation",
  "parameters": {
    "newLocation": "B02"
  }
}
```

**Validation Rules:**
- Location must exist in module
- Must be adjacent/connected to current location
- Cannot create new locations
- System auto-handles area transitions

### 3. Combat Management

#### createEncounter
Initializes new combat encounter.

**Parameters:**
- Complex object passed to combat_builder.py
- Includes monsters, positions, encounter ID

**Example:**
```json
{
  "action": "createEncounter",
  "parameters": {
    "encounterId": "E01-E1",
    "monsters": ["Goblin", "Goblin"],
    "positions": ["front", "back"]
  }
}
```

#### updateEncounter
Modifies active encounter.

**Parameters:**
- `encounterId` (string): Active encounter ID
- `changes` (object): Modifications to apply

### 4. Story/Plot Management

#### updatePlot
Advances plot points and story elements.

**Parameters:**
- `plotPointId` (string): Plot point identifier
- `newStatus` (string): New status (discovered, completed, failed)
- `plotImpact` (string, optional): Narrative impact description

**Example:**
```json
{
  "action": "updatePlot",
  "parameters": {
    "plotPointId": "PLOT001",
    "newStatus": "completed",
    "plotImpact": "The party discovered the ancient artifact"
  }
}
```

### 5. World State

#### updateTime
Advances game world time.

**Parameters:**
- `timeEstimate` (string or number): Time to advance in minutes

**Example:**
```json
{
  "action": "updateTime",
  "parameters": {
    "timeEstimate": "30"
  }
}
```

### 6. Party Management

#### updatePartyNPCs
Add or remove NPCs from party.

**Parameters:**
- `operation` (string): "add" or "remove"
- `npc` (object): NPC data including name, race, class, level

**Example:**
```json
{
  "action": "updatePartyNPCs",
  "parameters": {
    "operation": "add",
    "npc": {
      "name": "Elara",
      "race": "Elf",
      "class": "Ranger",
      "level": 5
    }
  }
}
```

#### updatePartyTracker
General party state updates.

**Parameters:**
- Various fields from party_tracker.json
- Can update location, module, world conditions

**Example:**
```json
{
  "action": "updatePartyTracker",
  "parameters": {
    "module": "Keep_of_Doom",
    "currentLocationId": "A01",
    "currentLocation": "Entrance Hall"
  }
}
```

### 7. Module/Campaign

#### createNewModule
AI-driven module generation.

**Parameters:**
- `narrative` (string): Description of desired module
- OR structured parameters for detailed control

**Example:**
```json
{
  "action": "createNewModule",
  "parameters": {
    "narrative": "Create a mysterious underwater temple adventure for level 5-7 characters"
  }
}
```

#### establishHub
Creates base of operations.

**Parameters:**
- `hubName` (string): Name of hub
- `hubType` (string): Type (tavern, keep, tower, etc.)
- `description` (string): Hub description
- `services` (array): Available services
- `ownership` (string): Who owns it

**Example:**
```json
{
  "action": "establishHub",
  "parameters": {
    "hubName": "The Silver Swan Inn",
    "hubType": "tavern",
    "description": "A cozy inn with warm hearths",
    "services": ["rest", "information", "supplies"],
    "ownership": "party"
  }
}
```

### 8. Storage System

#### storageInteraction
Handle item storage operations.

**Parameters:**
- `description` (string): Natural language storage request
- `characterName` (string): Character performing action

**Example:**
```json
{
  "action": "storageInteraction",
  "parameters": {
    "description": "Store my longsword in the chest",
    "characterName": "Norn"
  }
}
```

### 9. Session Management

#### exitGame
Ends game session gracefully.

**Parameters:** None

**Example:**
```json
{
  "action": "exitGame",
  "parameters": {}
}
```

## Validation Requirements

### 1. JSON Structure Validation
- Must be valid JSON
- Must have "narration" and "actions" fields
- Actions must be array (can be empty)
- Each action must have "action" and "parameters" fields

### 2. Action Validation
- Action type must be recognized
- Required parameters must be present
- Parameter types must match expected types
- Parameter values must be valid

### 3. Game State Validation
- Location transitions must be valid paths
- Character names must exist
- Plot points must be defined
- Encounter IDs must be unique

### 4. Content Validation
- No Unicode characters in narration (Windows console compatibility)
- No creation of undefined locations/areas
- No contradicting established game state

## Test Scenarios

### Basic Functionality Tests
1. **Empty Response**: Test narration with no actions
2. **Single Action**: Test each action type individually
3. **Multiple Actions**: Test combining 2-3 actions
4. **Parameter Variations**: Test different parameter formats

### Error Handling Tests
1. **Invalid JSON**: Malformed JSON structure
2. **Missing Fields**: Missing narration or actions
3. **Invalid Actions**: Unrecognized action types
4. **Bad Parameters**: Missing or wrong type parameters

### Integration Tests
1. **Combat Flow**: Create encounter → update → resolve
2. **Travel Sequence**: Check location → transition → update time
3. **Character Progress**: Update XP → trigger level up → apply changes
4. **Story Flow**: Update plot → check triggers → advance narrative

### Edge Cases
1. **Long Narration**: Test with very long text
2. **Many Actions**: Test with 10+ actions in one response
3. **Complex Parameters**: Nested objects in parameters
4. **Special Characters**: Test escaping in strings

## Expected Validation Behavior

### Success Cases
- Valid JSON with correct structure → Process normally
- Empty actions array → Process narration only
- Valid location transition → Update location and continue

### Failure Cases
- Invalid JSON → Retry with error message
- Invalid location → Reject transition, explain limitation
- Missing parameters → Request missing information
- Unrecognized action → Ignore action, process others

## Testing Best Practices

1. **Isolation**: Test each action type separately first
2. **Combination**: Test realistic action combinations
3. **State Verification**: Check game state after each action
4. **Error Recovery**: Verify system handles errors gracefully
5. **Performance**: Monitor response time for complex actions

## Metrics to Track

- Action success rate by type
- Validation pass/fail rate
- Average retry count
- Common failure patterns
- Response time by action complexity

This comprehensive testing plan ensures thorough validation of the DM system while maintaining game integrity and user experience.