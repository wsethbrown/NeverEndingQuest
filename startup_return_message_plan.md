# Startup Return Message Injection Plan

## Objective
Modify main.py to automatically detect when a player has returned after an unexpected exit/crash and inject a "player has returned" message to maintain conversation continuity.

## Requirements Analysis

### Detection Criteria
1. **Game has started before**: Must have existing user messages in conversation history
2. **Missing return message**: Last message should not already be "player has returned"
3. **Timing**: Must happen BEFORE any conversation history processing or AI interactions

### Smart Detection Logic
- Check if conversation history exists and has user messages (game was previously started)
- Examine the last user message in conversation history
- If last message is NOT "Dungeon Master Note: Resume the game, the player has returned." then inject it
- Skip injection if conversation history is empty (first time startup)

## Implementation Plan

### Step 1: Create Detection Function
```python
def check_and_inject_return_message(conversation_history):
    """
    Checks if a 'player has returned' message needs to be injected at startup.
    
    Args:
        conversation_history: List of conversation messages
        
    Returns:
        Updated conversation history with return message if needed
    """
    # Skip if no conversation history (first startup)
    if not conversation_history:
        return conversation_history
    
    # Check if there are any user messages (game has been played before)
    user_messages = [msg for msg in conversation_history if msg.get("role") == "user"]
    if not user_messages:
        return conversation_history
    
    # Get the last message
    last_message = conversation_history[-1] if conversation_history else None
    if not last_message:
        return conversation_history
    
    # Check if last message is already a return message
    last_content = last_message.get("content", "")
    if "Resume the game, the player has returned" in last_content:
        print("DEBUG: Return message already present, skipping injection")
        return conversation_history
    
    # Inject return message
    return_message = {
        "role": "user", 
        "content": "Dungeon Master Note: Resume the game, the player has returned."
    }
    conversation_history.append(return_message)
    print("DEBUG: Injected 'player has returned' message at startup")
    return conversation_history
```

### Step 2: Integration Point
- Add the function call in `main_game_loop()` immediately after loading conversation history
- Ensure it happens BEFORE any other conversation processing
- Save the updated conversation history if message was injected

### Step 3: Placement in main.py
```python
def main_game_loop():
    # ... existing setup code ...
    
    # Load conversation history
    conversation_history = load_json_file("conversation_history.json") or []
    
    # CRITICAL: Check and inject return message BEFORE any processing
    conversation_history = check_and_inject_return_message(conversation_history)
    if conversation_history:  # Save if we made changes
        save_conversation_history(conversation_history)
    
    # ... rest of existing code continues normally ...
```

### Step 4: Edge Cases to Handle
1. **Empty conversation history**: Skip injection (first startup)
2. **No user messages**: Skip injection (system-only messages)
3. **Last message already return**: Skip injection (prevent duplicates)
4. **Conversation history corruption**: Handle gracefully

### Step 5: Testing Scenarios
1. **Normal startup after clean exit**: Should NOT inject message
2. **Startup after crash/forced exit**: Should inject message
3. **First time startup**: Should NOT inject message
4. **Multiple consecutive startups**: Should only inject once

## Benefits
- Maintains conversation continuity after unexpected exits
- Helps AI understand context when resuming game
- Prevents confusion about game state
- Automatic and transparent to player
- No impact on normal game flow

## Implementation Order
1. Create the detection function
2. Identify exact placement in main_game_loop()
3. Add function call and save logic
4. Test with various scenarios
5. Commit changes

This plan ensures robust handling of startup scenarios while maintaining conversation history integrity.