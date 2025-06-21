# Complex DM Test Plan

## Overview
This document describes the complex DM testing framework designed to stress-test the AI Dungeon Master's ability to handle multiple simultaneous function calls and complex narrative scenarios.

## Test Design Philosophy

### The Complex Test Prompt
```
Dungeon Master Note: Current date and time: 1492 Springmonth 2 15:13:00. Player: I want to give Elen a potion of healing and 50 gold, then have her cast a spell to detect magic on my sword. While she's doing that, I'll update my journal about finding a mysterious symbol in the ruins. Also, we found a hidden compartment with a magical tome that teaches the Shield spell - I want to learn it. Oh, and 2 hours pass during all this. Update the plot to reflect we discovered clues about an ancient curse affecting the village. Finally, I think I've earned enough XP to level up!
```

### Functions Tested Simultaneously
1. **updateCharacterInfo** (multiple times)
   - Removing items from Norn's inventory
   - Adding items to Elen's inventory
   - Learning new spell (Shield)
   - Tracking spell usage (Detect Magic)

2. **updateTime**
   - Advancing game time by 2 hours

3. **updatePlot**
   - Adding new plot element about ancient curse
   - Connecting discoveries to village mystery

4. **levelUp**
   - Character advancement for accumulated XP

5. **Complex NPC Interactions**
   - Elen casting spell
   - Responding to gifts
   - Participating in investigation

## Test Components

### 1. Test Setup (`dm_complex_test_setup.py`)
- Loads original conversation history
- Replaces final message with complex test prompt
- Generates mock DM response for validation
- Saves all intermediate files

### 2. Specialized Validator (`dm_complex_validator.py`)
- Validates JSON structure and required fields
- Checks for proper action parameters
- Verifies narrative covers all requested elements
- Ensures no Unicode characters
- Validates inventory tracking accuracy

### 3. Test Runner (`run_complex_dm_test.py`)
- Orchestrates entire test process
- Provides clear output and status
- Generates comprehensive reports

## Expected DM Response Structure

```json
{
  "narration": "Rich narrative covering all player actions...",
  "actions": [
    {
      "action": "updateCharacterInfo",
      "parameters": {
        "characterName": "norn",
        "changes": "Removed items, learned spell..."
      }
    },
    {
      "action": "updateCharacterInfo",
      "parameters": {
        "characterName": "elen", 
        "changes": "Added items, cast spell..."
      }
    },
    {
      "action": "updateTime",
      "parameters": {
        "hoursToAdd": 2
      }
    },
    {
      "action": "updatePlot",
      "parameters": {
        "plotKey": "ancient_village_curse",
        "description": "Discovered clues...",
        "status": "discovered"
      }
    },
    {
      "action": "levelUp",
      "parameters": {
        "characterName": "norn"
      }
    }
  ]
}
```

## Validation Criteria

### Critical Requirements (Must Pass)
- [x] Valid JSON structure
- [x] All required fields present
- [x] No Unicode characters
- [x] Minimum 2 `updateCharacterInfo` actions
- [x] Exactly 1 `updateTime` action
- [x] Exactly 1 `updatePlot` action
- [x] Exactly 1 `levelUp` action

### Quality Indicators (Warnings if Missing)
- [x] Narrative mentions all key elements
- [x] Inventory changes properly tracked
- [x] Spell usage recorded
- [x] Time passage reflected
- [x] Plot progression logical

## Usage Instructions

### Quick Test
```bash
python run_complex_dm_test.py
```

### Individual Components
```bash
# Setup test only
python dm_complex_test_setup.py

# Validate existing response
python dm_complex_validator.py dm_test_response_TIMESTAMP.json
```

## Generated Files

### During Test Run
- `dm_complex_test_conversation_TIMESTAMP.json` - Modified conversation history
- `dm_test_response_TIMESTAMP.json` - DM response to validate
- `dm_complex_test_summary_TIMESTAMP.json` - Test execution summary
- `dm_test_response_TIMESTAMP_validation_report.json` - Detailed validation results

## Test Scenarios Covered

### Core Mechanics
- Multiple inventory transfers
- Spell learning and usage
- Time progression
- Plot advancement
- Character leveling

### Narrative Complexity
- Multi-character interactions
- Simultaneous actions
- Discovery sequences
- Journal keeping
- Magical investigations

### Edge Cases
- Multiple actions on same character
- Cross-character dependencies
- Time-sensitive events
- Learning new abilities
- Plot revelation timing

## Success Metrics

### Perfect Score
- All actions present and correctly formatted
- Narrative covers all elements
- No validation errors or warnings
- Proper inventory tracking
- Logical event sequencing

### Acceptable Performance
- All critical actions present
- Minor narrative omissions (warnings only)
- Proper parameter formatting
- Unicode compliance maintained

### Failure Conditions
- Missing required actions
- Malformed JSON
- Unicode character usage
- Incorrect parameter types
- Major narrative gaps

## Benefits of This Test

1. **Comprehensive Coverage** - Tests multiple DM functions simultaneously
2. **Real-World Complexity** - Mirrors actual gameplay scenarios
3. **Validation Rigor** - Strict checking of all requirements
4. **Automated Execution** - Reproducible test runs
5. **Detailed Reporting** - Clear success/failure indicators

## Future Enhancements

- Combat scenario testing
- Location transition complexity
- Multi-session continuity
- Error recovery testing
- Performance benchmarking

This framework provides a robust foundation for ensuring the DM AI can handle complex, multi-faceted player requests while maintaining game state integrity and narrative quality.