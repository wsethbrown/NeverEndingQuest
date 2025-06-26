# Blank Input Loop Fix Plan

## Issues Identified

### 1. Blank Input Loop Bug in main.py
**Location**: main.py, lines 1295-1300
**Problem**: The empty_input_count is never incremented when empty input is detected. The code has:
```python
# Skip processing if input is empty or only whitespace
if not user_input_text or not user_input_text.strip():
    continue
else:
    # Reset counter on valid input
    empty_input_count = 0
```

But it never increments empty_input_count, so the max_empty_inputs safeguard never triggers.

### 2. Blank Input During Character Creation in startup_wizard.py
**Location**: startup_wizard.py, line 717
**Problem**: The character creation loop has:
```python
# Skip empty input to prevent infinite loops
if not user_input:
    continue
```
This causes blank inputs to be silently ignored, which might feed into the AI model as context.

### 3. Potential JSON Display Issue
Need to verify if character JSON data is being displayed to players anywhere during character creation or gameplay.

## Fixes to Implement

### Fix 1: Increment empty_input_count in main.py
```python
# Skip processing if input is empty or only whitespace
if not user_input_text or not user_input_text.strip():
    empty_input_count += 1
    if empty_input_count >= max_empty_inputs:
        print(f"[WARNING] Received {max_empty_inputs} empty inputs in a row. Breaking loop to prevent hang.")
        print("Please restart the game if you wish to continue playing.")
        break
    continue
else:
    # Reset counter on valid input
    empty_input_count = 0
```

### Fix 2: Better handling in startup_wizard.py
```python
# Skip empty input to prevent infinite loops
if not user_input:
    print("Please enter a response.")
    continue
```

### Fix 3: Add logging to track blank input issues
Add debug logging when blank inputs are detected to help diagnose the root cause.

## Implementation Order
1. Fix the empty_input_count increment in main.py
2. Add user feedback for blank inputs in startup_wizard.py
3. Add debug logging to track when/why blank inputs occur
4. Test the fixes thoroughly