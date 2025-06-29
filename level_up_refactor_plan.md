# Level Up System Refactor Plan

## Problem Summary
The level up system currently causes an infinite loop because:
1. **Current Architecture**: `levelUp` action in action_handler.py simply adds guidance to conversation history and waits for a response
2. **No Direct Execution**: Unlike combat_manager which has `run_combat_simulation()`, there's no direct function call for level up
3. **Infinite Loop**: The system keeps waiting for a response that never comes, causing repeated attempts
4. **Token Drain**: Each retry consumes API tokens, creating significant costs

## Root Cause Analysis
From claude.txt analysis:
- combat_manager.py works because it's called as a function within the same process
- level_up.py fails because it's launched as a subprocess expecting terminal input
- The web interface cannot communicate with the subprocess, causing the hang

## Solution Overview
Refactor level_up.py from a standalone interactive script to a function-based module that can be called directly from action_handler.py, similar to how combat_manager.py works.

## Detailed Implementation Plan

### 1. Refactor level_up.py Structure

#### Current Structure (PROBLEMATIC):
```python
def level_up_character(character_name):
    # Interactive loop with input() calls
    while True:
        user_input = input("Your choice: ")  # THIS CAUSES THE HANG
        # Process input...

if __name__ == "__main__":
    character_name = input("Enter character name: ")
    level_up_character(character_name)
```

#### New Structure (SOLUTION):
```python
def run_level_up_process(character_name, current_level, new_level, conversation_history):
    """
    Run the level up process as a function call, not a subprocess
    
    Args:
        character_name: Name of character to level up
        current_level: Current character level
        new_level: Target level (current + 1)
        conversation_history: Game conversation context
        
    Returns:
        dict: Result containing success status, character updates, and messages
    """
    # Load character data
    character_data = safe_read_json(f"{character_name}.json")
    if not character_data:
        return {
            "success": False,
            "error": f"Could not load character data for {character_name}"
        }
    
    # Process level up with AI
    level_up_result = process_level_up_with_ai(character_data, current_level, new_level)
    
    # Return structured result
    return {
        "success": True,
        "character_updates": level_up_result["updates"],
        "messages": level_up_result["messages"],
        "new_character_data": level_up_result["character_data"]
    }
```

### 2. Update action_handler.py

#### Current Implementation (PROBLEMATIC):
```python
elif action_type == ACTION_LEVEL_UP:
    entity_name = parameters.get("entityName")
    new_level = parameters.get("newLevel")
    
    # Just adds guidance and waits - NO ACTUAL EXECUTION
    dm_note = f"Leveling Dungeon Master Guidance: Proceed with leveling up..."
    conversation_history.append({"role": "user", "content": dm_note})
    return create_return(status="needs_response", needs_update=True)
```

#### New Implementation (SOLUTION):
```python
elif action_type == ACTION_LEVEL_UP:
    status_processing_levelup()
    print(f"DEBUG: Processing levelUp action")
    
    entity_name = parameters.get("entityName")
    new_level = parameters.get("newLevel")
    
    try:
        # Import the refactored function
        from level_up import run_level_up_process
        
        # Get current character data
        character_file = f"characters/{entity_name}.json"
        character_data = safe_read_json(character_file)
        
        if not character_data:
            print(f"ERROR: Could not find character {entity_name}")
            return create_return(status="continue", needs_update=False)
        
        current_level = character_data.get("level", 1)
        
        # Run level up process
        result = run_level_up_process(
            entity_name, 
            current_level, 
            new_level,
            conversation_history[-10:]  # Last 10 messages for context
        )
        
        if result["success"]:
            # Update character file
            safe_write_json(character_file, result["new_character_data"])
            
            # Add success message to conversation
            level_up_message = f"[Level Up Complete] {entity_name} has advanced to level {new_level}!"
            conversation_history.append({"role": "system", "content": level_up_message})
            
            # Add any important messages from the level up process
            for message in result.get("messages", []):
                conversation_history.append({"role": "system", "content": message})
            
            needs_conversation_history_update = True
            print(f"DEBUG: Successfully leveled up {entity_name} to level {new_level}")
        else:
            error_msg = result.get("error", "Unknown level up error")
            print(f"ERROR: Level up failed - {error_msg}")
            conversation_history.append({"role": "system", "content": f"Level up failed: {error_msg}"})
            needs_conversation_history_update = True
            
    except Exception as e:
        print(f"ERROR: Exception during level up: {str(e)}")
        import traceback
        traceback.print_exc()
        
    return create_return(status="continue", needs_update=needs_conversation_history_update)
```

### 3. Handle Input/Output Flow

Remove all `input()` calls and replace with AI-driven decisions:

```python
def get_level_up_choices(character_data, level_info, choice_type):
    """Get level up choices from AI instead of user input"""
    
    prompt = f"""
    Character {character_data['name']} is leveling up and needs to make the following choice:
    {choice_type}
    
    Current character data:
    {json.dumps(character_data, indent=2)}
    
    Available options:
    {level_info}
    
    Provide the choice in JSON format.
    """
    
    # Use AI to make the choice
    response = client.chat.completions.create(
        model=LEVEL_UP_MODEL,
        messages=[{"role": "system", "content": prompt}]
    )
    
    return parse_json_safely(response.choices[0].message.content)
```

### 4. Add Safety Mechanisms

```python
def run_level_up_process(character_name, current_level, new_level, conversation_history):
    """Run level up with safety mechanisms"""
    
    # Timeout protection
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Level up process timed out")
    
    # Set 30 second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    
    try:
        # Level up logic here
        result = process_level_up_with_ai(...)
        
        # Cancel timeout
        signal.alarm(0)
        
        # Log success
        log_level_up_attempt(character_name, current_level, new_level, "success")
        
        return result
        
    except TimeoutError:
        signal.alarm(0)
        log_level_up_attempt(character_name, current_level, new_level, "timeout")
        return {"success": False, "error": "Level up timed out"}
        
    except Exception as e:
        signal.alarm(0)
        log_level_up_attempt(character_name, current_level, new_level, f"error: {str(e)}")
        return {"success": False, "error": str(e)}
```

### 5. Testing Strategy

1. **Create Test Character**:
   ```python
   test_character = {
       "name": "test_levelup",
       "level": 1,
       "experience": 300,
       "experience_goal": 300,
       "class": "Fighter"
   }
   ```

2. **Test Cases**:
   - Character at exactly 300/300 XP
   - NPC level up
   - Multiple level ups in sequence
   - Error handling (missing character file)
   - Timeout handling

3. **Validation Checks**:
   - XP resets to 0 after level up
   - New experience_goal is set correctly
   - Hit points increase appropriately
   - Class features are added
   - No infinite loops occur

## Expected Outcome

- **Seamless Integration**: Level up happens within game flow
- **No Terminal Switch**: Everything stays in the web interface
- **Proper Updates**: Character files update correctly
- **XP Management**: XP resets to 0, new goal set
- **No Loops**: Timeout protection prevents infinite loops
- **Cost Savings**: No token drain from retries

## Risk Mitigation

1. **Backup Files**:
   ```bash
   cp level_up.py level_up.py.backup
   cp action_handler.py action_handler.py.backup
   ```

2. **Test Environment**:
   - Use test character files
   - Run in debug mode
   - Monitor token usage

3. **Rollback Plan**:
   - Keep original files as .backup
   - Document all changes
   - Test rollback procedure

## Implementation Order

1. ✅ Create this level_up_refactor_plan.md
2. Backup current files
3. Refactor level_up.py to be function-based
4. Update action_handler.py to call the function
5. Add safety mechanisms (timeouts, logging)
6. Test with test character
7. Fix any issues found
8. Deploy to main game
9. Monitor for issues
10. Update documentation

## Success Criteria

- [ ] Level up completes without hanging
- [ ] Character file updates correctly
- [ ] XP resets to 0 after level up
- [ ] New experience_goal is set
- [ ] No infinite loops occur
- [ ] No token drain
- [ ] Works for both players and NPCs
- [ ] Errors are handled gracefully
- [ ] Process completes within 30 seconds

## Notes

- Similar pattern to combat_manager.py implementation
- Must maintain compatibility with existing character schema
- Should work with web interface input/output
- Consider adding progress indicators for long operations