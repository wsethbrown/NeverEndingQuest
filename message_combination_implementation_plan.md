# Message Combination System Implementation Plan

## Overview
Implement a buffering system that detects `createEncounter` actions in validated AI responses and holds the first message to combine it with the subsequent combat resolution message, creating seamless narrative flow.

## Core Requirements
- **Dual Condition Check**: Both validation must pass AND `createEncounter` action must be present
- **Message Buffering**: Hold first message temporarily until second message arrives
- **Safe Integration**: Minimal disruption to existing validation and processing workflow

## Implementation Steps

### 1. Add Buffering State Variables to main.py
- Add module-level variables:
  - `held_response = None` - stores the buffered first message
  - `awaiting_combat_resolution = False` - tracks if we're waiting for second message

### 2. Create Helper Functions
- `detect_create_encounter(parsed_data)` - checks if actions contain createEncounter
- `combine_messages(first_response, second_response)` - merges narration and actions
- `clear_message_buffer()` - resets buffering state

### 3. Modify Main Processing Logic
**Location**: After validation in main.py (around where `dm_response_validator.py` is called)

**New Flow**:
```python
# After validation passes
is_valid, errors, parsed_data = validator.validate_response(response)
if is_valid:
    has_create_encounter = detect_create_encounter(parsed_data)
    
    if has_create_encounter and not awaiting_combat_resolution:
        # Hold this message for combination
        held_response = response
        awaiting_combat_resolution = True
        # Display message but don't process actions yet
        return  
    
    elif awaiting_combat_resolution:
        # Combine with held message
        combined_response = combine_messages(held_response, response)
        clear_message_buffer()
        # Process combined message normally
        
    else:
        # Normal processing (no encounter, no buffering)
        # Process message normally
```

### 4. Message Combination Logic
- **Narration**: Append second message narration to first message narration
- **Actions**: Merge action arrays (first message + second message actions)
- **Preserve**: Maintain JSON structure and all metadata

### 5. Error Handling
- **Validation Failure**: If first message validation fails, don't buffer
- **Timeout Protection**: Clear buffer if second message doesn't arrive within reasonable time
- **Graceful Fallback**: If combination fails, process messages separately

### 6. Integration Points
- **Before Action Processing**: Insert combination logic after validation, before action handling
- **Conversation History**: Ensure combined messages are properly recorded
- **User Display**: Show combined narrative as single cohesive response

## Technical Details
- **File Location**: Primary changes in `main.py` around line 224 (validation context area)
- **Dependencies**: Uses existing `dm_response_validator.py` and JSON parsing
- **State Management**: Simple module-level variables for buffering state
- **Safety**: Only triggers on both validation pass + createEncounter detection

## Testing Strategy
- Test with createEncounter actions (should combine)
- Test with other actions (should process normally)  
- Test validation failures (should not buffer)
- Test edge cases (malformed JSON, missing second message)

## Expected Outcome
This implementation will eliminate the fragmented combat responses shown in `claude.txt` by creating seamless narrative flow while maintaining all existing validation and safety systems.