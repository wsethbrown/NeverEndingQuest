# DungeonMasterAI Automated Testing System

## Overview
The automated testing system uses GPT-4o-mini as an AI player to test the game, finding bugs and edge cases much faster than manual testing.

## Quick Start

### Easy Launch
```bash
python quick_test.py
```
Then select from the menu:
1. Quick Exploration (15 min)
2. Combat Test (30 min)
3. Skill Check Test (20 min)
4. Bug Hunter (30 min)
5. Main Quest (90 min)
6. Full Test Suite (4+ hours)

### Command Line
```bash
# Run specific test profile
python run_automated_test.py thorough_explorer

# Run with custom action limit
python run_automated_test.py combat_stress_test --max-actions 200

# List available profiles
python run_automated_test.py --list-profiles
```

## Test Profiles

### 1. **Thorough Explorer** (60 min)
- Visits all village locations
- Talks to all NPCs
- Searches for hidden items
- Tests location transitions

### 2. **Main Quest Speedrun** (90 min)
- Follows critical path only
- Tests main story progression
- Verifies quest completion

### 3. **Combat Stress Test** (120 min)
- Engages all combat encounters
- Tests different tactics
- Verifies HP and damage tracking

### 4. **Skill Check Validator** (90 min)
- Tests all skill types
- Verifies DC mechanics
- Tests advantage/disadvantage

### 5. **Edge Case Hunter** (120 min)
- Tries to break the game
- Tests invalid commands
- Looks for exploits

### 6. **Narrative Completionist** (180 min)
- Completes all side quests
- Explores all dialogue
- Tests multiple endings

### 7. **Technical Validator** (60 min)
- Tests file operations
- Verifies data persistence
- Stress tests saves

## How It Works

1. **AI Player** (`ai_player.py`)
   - Uses GPT-4o-mini to make decisions
   - Follows test objectives
   - Reports issues automatically

2. **Test Runner** (`run_automated_test.py`)
   - Manages game/AI interaction
   - Monitors progress
   - Generates reports

3. **Test Objectives** (`test_objectives.json`)
   - Defines what to test
   - Sets constraints
   - Tracks known issues

## Test Results

Results are saved to `test_results_[profile]_[timestamp].json` containing:
- Actions taken
- Issues found
- Objectives completed
- Sample interactions

### Example Output
```json
{
  "test_profile": "thorough_explorer",
  "total_actions": 127,
  "issues_found": 3,
  "objectives_completed": 8,
  "issues_detail": [
    {
      "type": "Missing content detected",
      "location": "Town Square",
      "context": "Cannot find location 'Secret Basement'"
    }
  ]
}
```

## Customizing Tests

### Add New Test Profile
Edit `test_objectives.json`:
```json
"my_custom_test": {
  "name": "My Custom Test",
  "description": "Tests specific features",
  "objectives": [
    "Test objective 1",
    "Test objective 2"
  ],
  "constraints": {
    "avoid_combat": true
  },
  "expected_duration_minutes": 30
}
```

### Modify AI Behavior
The AI player can have different personalities:
- `CAUTIOUS`: Searches for traps, saves often
- `AGGRESSIVE`: Rushes into combat
- `CURIOUS`: Examines everything
- `SPEEDRUNNER`: Minimal interactions

## Integration with Logging

Test sessions use the enhanced logging system:
- Console shows key events with icons
- `game_errors.log` captures issues
- `game_debug.log` has full details

View test logs:
```bash
python view_logs.py errors
python view_logs.py search "combat"
```

## Best Practices

1. **Start Small**: Run quick tests first
2. **Check Logs**: Review game_errors.log after each test
3. **Compare Results**: Run same test multiple times
4. **Focus Testing**: Use specific profiles for problem areas
5. **Save Results**: Keep test_results files for comparison

## Troubleshooting

**Test Hangs**: Set lower --max-actions limit
**AI Confused**: Check test objectives are clear
**Missing Content**: AI will report and continue
**Crashes**: Check game_errors.log for details

## Future Enhancements

- Parallel test execution
- Visual test playback
- Regression test suite
- Performance benchmarking
- Screenshot capture at issues