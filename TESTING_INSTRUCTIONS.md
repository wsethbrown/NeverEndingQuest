# DungeonMasterAI Testing Framework - Complete Instructions

## Quick Start Commands

### 1. Basic Comprehensive Testing
```bash
# Run all test profiles with full analysis
python enhanced_test_runner.py --comprehensive

# List available test profiles first
python enhanced_test_runner.py --list-profiles
```

### 2. Feature Discovery Testing (Recommended for Alpha)
```bash
# Test AI discovery of storage chests and features
python feature_discovery_tests.py --all

# Test specific feature discovery
python feature_discovery_tests.py --scenario storage_chest_discovery
```

### 3. Individual Test Profiles
```bash
# Run specific profiles only
python enhanced_test_runner.py --comprehensive --profiles thorough_explorer combat_specialist

# Run discovery-focused testing
python enhanced_test_runner.py --discovery
```

### 4. Legacy Testing (Original System)
```bash
# Run original test system for comparison
python run_automated_test.py thorough_explorer

# List legacy profiles
python run_automated_test.py --list-profiles
```

## Test Profiles Explained

### Core Test Profiles
- **`thorough_explorer`** - Comprehensive exploration and feature testing (45 min)
- **`combat_specialist`** - Combat system stress testing (30 min)
- **`social_navigator`** - NPC interaction and dialogue testing (35 min)
- **`system_breaker`** - Edge cases and error handling (25 min)
- **`feature_discoverer`** - AI discovers features without hints (40 min)
- **`integration_tester`** - End-to-end system integration (60 min)

### Feature Discovery Scenarios
- **`storage_chest_discovery`** - Can AI find and use storage system?
- **`location_transition_discovery`** - Can AI navigate between areas?
- **`npc_interaction_discovery`** - Can AI find and talk to NPCs?
- **`inventory_management_discovery`** - Can AI manage items effectively?
- **`combat_system_discovery`** - Can AI discover combat mechanics?

## Reading Test Results

### Comprehensive Test Results
```bash
# Results saved to: comprehensive_test_results_YYYYMMDD_HHMMSS.json
cat comprehensive_test_results_*.json | jq '.summary'
```

**Key Metrics:**
- **Total Profiles**: Number of test profiles run
- **Successful Tests**: Tests that completed without crashes
- **Validation Passed**: Tests that met success criteria
- **Systems Covered**: Number of game systems tested
- **Total Actions**: Total AI actions performed

### Feature Discovery Results
```bash
# Results saved to: feature_discovery_results_YYYYMMDD_HHMMSS.json
cat feature_discovery_results_*.json | jq '.summary'
```

**Key Metrics:**
- **Successful Discoveries**: Features AI found organically
- **Criteria Met**: Specific discovery objectives achieved
- **Efficiency Score**: Discovery rate per action taken
- **Timeline**: When each feature was discovered

## Understanding Test Output

### During Test Execution
```
[INFO] Starting automated test: thorough_explorer
[INFO] Progress: 50 actions taken
[WARNING] AI response truncated from 15 words to: examine the chest
[INFO] Test completed: 127 actions taken
```

### Success Indicators
- ✅ **Feature Coverage**: All major systems tested
- ✅ **Discovery Success**: AI found features without help
- ✅ **Performance**: Completed within time limits
- ✅ **No Critical Issues**: System remained stable

### Warning Signs
- ❌ **High Issue Count**: Many errors or bugs found
- ❌ **Poor Discovery**: AI couldn't find basic features
- ❌ **Timeout**: Test exceeded expected duration
- ❌ **Validation Fail**: Success criteria not met

## Troubleshooting

### Test Won't Start
```bash
# Check if test_objectives.json exists
ls -la test_objectives.json

# Verify AI player can load
python test_ai_constraints.py

# Check for module files
ls -la modules/Keep_of_Doom/
```

### Test Fails Immediately
```bash
# Check logs for errors
tail -f enhanced_logger.log

# Verify character files exist
ls -la modules/Keep_of_Doom/characters/norn.json

# Test basic game startup
python main.py
```

### Tests Run But Find Many Issues
```bash
# Check specific issue types
cat test_results_*.json | jq '.issues_detail'

# Review AI interaction logs
tail -f ai_player_llm_debug.log

# Run validation separately
python validate_module_files.py
```

## Interpreting Results for Alpha Release

### Ready for Alpha ✅
- **Feature Coverage**: 80%+ systems tested successfully
- **Discovery Score**: 70%+ features found organically
- **Issue Density**: <5 issues per 100 actions
- **Performance**: Tests complete within 150% of expected time
- **Validation**: 80%+ test profiles pass all criteria

### Needs Work ⚠️
- **Poor Discovery**: <50% features found organically
- **High Issues**: >10 issues per 100 actions
- **System Failures**: Tests crash or timeout frequently
- **Validation Fails**: <60% test profiles pass criteria

### Not Ready ❌
- **Can't Complete**: Tests fail to run or crash immediately
- **No Discovery**: AI can't find basic features like movement
- **Critical Bugs**: Game-breaking issues found
- **Performance**: Tests take 3x+ expected time

## Advanced Usage

### Custom Test Profiles
1. Edit `test_objectives.json`
2. Add new profile under `test_profiles`
3. Define objectives, focus areas, and constraints
4. Run with `--profiles your_custom_profile`

### Isolated Environment Inspection
```bash
# Find test environments
ls -la isolated_testing/

# Examine specific test run
cd isolated_testing/profile_thorough_explorer_*/
ls -la

# Check test-specific logs
cat logs/*.log
```

### Performance Monitoring
```bash
# Monitor system resources during testing
htop

# Check test duration trends
grep "Test completed" test_logs/*/*.log

# Analyze action efficiency
cat test_results_*.json | jq '.performance_metrics'
```

## Pre-Alpha Release Checklist

### Essential Tests
- [ ] Run comprehensive test suite: `python enhanced_test_runner.py --comprehensive`
- [ ] Run feature discovery tests: `python feature_discovery_tests.py --all`
- [ ] Verify storage system discovery works
- [ ] Confirm location transitions work
- [ ] Test combat system functionality
- [ ] Validate NPC interactions

### Success Criteria
- [ ] 80%+ comprehensive test success rate
- [ ] 70%+ feature discovery success
- [ ] Storage system discoverable by AI
- [ ] All major game systems functional
- [ ] <5 critical issues per test run
- [ ] Tests complete within reasonable time

### Final Validation
- [ ] Run full test suite 3 times successfully
- [ ] No game-breaking bugs found
- [ ] AI can play without human intervention
- [ ] All core features accessible to AI players

## Getting Help

### Log Files
- **Enhanced Logs**: `enhanced_logger.log`
- **AI Debug**: `ai_player_llm_debug.log`
- **Test Results**: `*test_results*.json`
- **Isolated Logs**: `isolated_testing/*/logs/`

### Validation Tools
- **Module Validation**: `python validate_module_files.py`
- **AI Constraints**: `python test_ai_constraints.py`
- **Storage System**: `python test_storage_system.py`

### Common Issues
1. **Missing Files**: Ensure all module files are in `modules/Keep_of_Doom/`
2. **Permission Errors**: Check file permissions in test directories
3. **API Errors**: Verify OpenAI API key in `config.py`
4. **Memory Issues**: Close other applications during testing
5. **Timeout Issues**: Increase test duration in profile settings

This testing framework provides comprehensive validation for your DungeonMasterAI system before alpha release. The isolated testing environment ensures your main game remains unaffected while thorough feature discovery testing validates that AI players can find and use all game features organically.