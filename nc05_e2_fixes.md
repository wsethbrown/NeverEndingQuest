# Recommended Fixes for NC05-E2 Combat Validation Issues

## Immediate Fixes

### 1. Fix Round Number Synchronization
In `combat_manager.py`, ensure both fields are updated together:
```python
# When updating round number
encounter_data['combat_round'] = new_round
encounter_data['current_round'] = new_round
```

### 2. Increase Validator Context for Complex Encounters
Modify the validation context window based on participant count:
```python
def get_validation_context_size(encounter_data):
    creature_count = len([c for c in encounter_data.get('creatures', []) 
                         if c.get('status', 'alive') == 'alive'])
    # For 8+ creatures, provide more context
    if creature_count >= 8:
        return 36  # 18 exchange pairs
    elif creature_count >= 6:
        return 28  # 14 exchange pairs
    else:
        return 24  # 12 exchange pairs (current default)
```

### 3. Add Combat State Summary
Include a combat state summary with validation requests:
```python
def create_combat_state_summary(encounter_data):
    summary = {
        "round": encounter_data.get("current_round", 1),
        "creatures_acted_this_round": [],
        "creatures_pending_this_round": [],
        "hp_changes_this_round": []
    }
    # Populate based on action history
    return summary
```

### 4. Relax Initiative Order Validation
Allow for tactical variations in turn order:
- NPCs may delay actions for narrative reasons
- Group initiatives (same value) can act in any order
- Dead/unconscious creatures should be skipped

### 5. Separate Validation Concerns
```python
validation_checks = {
    "mechanical": {
        "hp_math_correct": True,
        "valid_dice_usage": True,
        "resource_tracking": True
    },
    "narrative": {
        "all_hits_narrated": True,
        "death_described": True
    },
    "state_consistency": {
        "round_numbers_match": True,
        "all_creatures_tracked": True
    }
}
```

## Code Changes

### In combat_manager.py:
1. Add debug logging for validation attempts
2. Include combat state summary in validation requests
3. Synchronize round number fields
4. Track which creatures have acted this round

### In combat_validation_prompt.txt:
1. Add flexibility for group initiative
2. Clarify that NPCs may tactically delay
3. Separate critical errors from narrative preferences

### New Validation Mode for Complex Encounters:
Add a "complex_encounter_mode" that:
- Provides more context
- Focuses on critical mechanical errors
- Allows more narrative flexibility
- Tracks partial round completion

## Testing Recommendations

1. Create test encounters with 6-10 participants
2. Test with multiple creatures at same initiative
3. Verify round advancement with partial completion
4. Test validation with narrative variations

## Long-term Improvements

1. **Action Queue System**: Track pending actions explicitly
2. **Round State Machine**: Clear states for round progression
3. **Validation Severity Levels**: Errors vs warnings vs suggestions
4. **Combat Summary Generation**: Auto-generate round summaries for validation