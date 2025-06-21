# DM System Testing Guide

## Quick Start

Run all tests:
```bash
python run_dm_tests.py
```

Run quick subset:
```bash
python run_dm_tests.py --quick
```

Run specific category:
```bash
python run_dm_tests.py --category character_management
```

Run tests for specific action:
```bash
python run_dm_tests.py --action updateCharacterInfo
```

## Testing Framework Components

### 1. Test Runner (`run_dm_tests.py`)
Main orchestrator that:
- Loads test scenarios
- Sends prompts to DM AI
- Validates responses
- Generates reports

### 2. Test Scenarios (`dm_test_scenarios.json`)
Defines:
- Test prompts
- Expected responses
- Validation rules
- Test categories

### 3. Response Validator (`dm_response_validator.py`)
Validates:
- JSON format
- Required fields
- Action parameters
- Game rules
- Content restrictions (no Unicode)

### 4. Function Tester (`test_dm_functions.py`)
Individual function tests:
- Basic narration
- Each action type
- Error cases
- Complex scenarios

### 5. Test Documentation (`dm_system_testing_plan.md`)
Complete reference for:
- All available actions
- Parameter specifications
- Validation rules
- Expected behaviors

## Test Categories

- **fundamental**: Basic response format
- **character_management**: Stats, inventory, conditions
- **movement**: Location transitions
- **time_management**: Time advancement
- **combat**: Encounter creation
- **story**: Plot updates
- **party_management**: NPC management
- **storage**: Item storage
- **campaign**: Module creation, hub establishment
- **session**: Game session control
- **complex**: Multi-action scenarios

## Understanding Test Results

### Console Output
```
[PASS] Response valid in 1.23s
       Actions: updateCharacterInfo, updateTime
```

### JSON Report
- `dm_integration_test_results_[timestamp].json`: Full results
- `dm_test_failures_[timestamp].json`: Failed tests only

### Markdown Report
- `dm_test_report_[timestamp].md`: Human-readable summary

## Common Issues and Solutions

### Issue: JSON Parse Errors
**Cause**: DM not returning valid JSON
**Solution**: Check system prompt includes JSON format example

### Issue: Missing Actions
**Cause**: DM not generating expected actions
**Solution**: Ensure action is mentioned in system prompt

### Issue: Unicode Characters
**Cause**: DM using special characters
**Solution**: System prompt should prohibit Unicode

### Issue: Invalid Location IDs
**Cause**: DM creating non-existent locations
**Solution**: Emphasize location restrictions in prompt

## Adding New Tests

1. Add scenario to `dm_test_scenarios.json`:
```json
{
  "id": "new_test",
  "name": "New Test Scenario",
  "category": "appropriate_category",
  "prompt": "Test prompt here",
  "expected_response": {
    "has_narration": true,
    "required_actions": ["expectedAction"],
    "expected_parameters": {
      "param1": "value1"
    }
  }
}
```

2. Run the new test:
```bash
python run_dm_tests.py --category appropriate_category
```

## Validation Rules

### Required JSON Structure
```json
{
  "narration": "string",
  "actions": [
    {
      "action": "actionType",
      "parameters": {}
    }
  ]
}
```

### Action Validation
- Action type must be recognized
- Required parameters must be present
- Parameter types must match expected
- No Unicode characters allowed

### Game Rule Validation
- HP must be non-negative
- Levels 1-20 only
- Ability scores 1-30
- Valid location IDs only

## Performance Benchmarks

Expected response times:
- Simple narration: < 2 seconds
- Single action: < 3 seconds
- Complex multi-action: < 5 seconds

## Debugging Failed Tests

1. Check the failure report:
```bash
cat dm_test_failures_[timestamp].json | jq '.[0]'
```

2. Validate a specific response:
```bash
python dm_response_validator.py response.json
```

3. Run individual test:
```bash
python test_dm_functions.py
```

## Integration with CI/CD

The test runner returns exit codes:
- 0: All tests passed
- 1: One or more tests failed

This allows integration with CI/CD pipelines:
```bash
python run_dm_tests.py --quick || echo "Tests failed!"
```

## Best Practices

1. **Run quick tests frequently** during development
2. **Run full suite** before major changes
3. **Review failed tests** immediately
4. **Update scenarios** when adding new features
5. **Monitor performance** trends over time

## Troubleshooting

### API Rate Limits
Tests include delays between scenarios. If hitting limits:
- Increase delay in `run_dm_tests.py`
- Run subset of tests
- Use `--quick` flag

### Model Variations
Different models may behave differently. Always test with the production model specified in `config.py`.

### Environment Issues
Ensure all dependencies are installed:
```bash
pip install openai
```

And API key is configured in `config.py`.