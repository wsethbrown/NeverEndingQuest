# Enhanced Testing Framework Usage Guide

## Quick Start

### 1. Run Comprehensive Test Suite
```bash
python enhanced_test_runner.py --comprehensive
```
This runs all test profiles in isolated environments with complete feature coverage analysis.

### 2. Run Discovery-Focused Testing
```bash
python enhanced_test_runner.py --discovery
```
Tests how well AI players can discover features organically without instructions.

### 3. Run Specific Test Profiles
```bash
python enhanced_test_runner.py --comprehensive --profiles thorough_explorer combat_specialist
```

### 4. Run Feature Discovery Tests
```bash
python feature_discovery_tests.py --all
```
Tests specific feature discovery scenarios like storage chests, location transitions, etc.

### 5. Run Single Feature Discovery Test
```bash
python feature_discovery_tests.py --scenario storage_chest_discovery
```

## Available Test Profiles

- **thorough_explorer**: Comprehensive exploration and feature discovery
- **combat_specialist**: Focused combat system testing
- **social_navigator**: NPC interaction and dialogue testing
- **system_breaker**: Edge case and error handling testing
- **feature_discoverer**: AI-specific discovery testing without instructions
- **integration_tester**: End-to-end integration and continuity testing

## Key Features

### Enhanced AI Player System
- **Complete Character Data**: AI has full access to character JSON (stats, equipment, abilities)
- **Continuous Conversation**: AI maintains full conversation history with DM
- **Natural Language**: Conversational 20-35 word responses (no artificial limits)
- **Context Awareness**: AI can reference previous events, NPCs, and stored items
- **Equipment Knowledge**: AI knows exactly what they have and can use
- **Smart Constraints**: Only removes extremely verbose phrases, preserves natural speech

### Isolated Testing Environment
- Each test runs in a completely separate environment
- No interference with main game files
- Clean state for each test run
- Automatic cleanup with log preservation

### Discovery Testing
- Tests AI ability to find features organically
- No hints or instructions provided
- Measures feature accessibility for AI players
- Validates intuitive game design

### Comprehensive Analysis
- Feature coverage analysis
- Performance metrics
- Discovery pattern analysis
- Validation against success criteria

### Enhanced Reporting
- Detailed test results with metrics
- Discovery timeline and efficiency scores
- Performance and coverage analysis
- Issue identification and categorization

## Test Results Location

Test results are saved to:
- `comprehensive_test_results_YYYYMMDD_HHMMSS.json`
- `feature_discovery_results_YYYYMMDD_HHMMSS.json`
- `test_logs/` directory for preserved logs

## Validation and Success Criteria

The framework validates:
- ✅ **Feature Coverage**: All major game systems tested
- ✅ **Discovery Success**: AI can find features without help
- ✅ **Performance**: Tests complete within expected timeframes
- ✅ **Error Handling**: System resilience to edge cases
- ✅ **Integration**: Cross-system functionality works correctly

## Customization

You can customize testing by:
1. Editing `test_objectives.json` to modify test profiles
2. Adding new discovery scenarios in `feature_discovery_tests.py`
3. Adjusting validation criteria and thresholds
4. Creating custom AI personality profiles

This framework ensures your DungeonMasterAI system is robust and accessible for AI players before alpha release.