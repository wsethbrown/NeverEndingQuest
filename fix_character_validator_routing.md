# Fix Character Validator Output Routing

## Problem
Character validator messages appear in Game Output tab instead of Debug tab when called during gameplay.

## Root Cause
The WebOutputCapture class in web_interface.py has complex routing logic that can misroute messages if they appear during Dungeon Master narration sections.

## Solution

### Option 1: Use a Special Prefix Pattern (Recommended)
Modify character_validator.py to use a prefix that explicitly routes to debug:

```python
# Instead of:
print(f"[Character Validator] Starting validation for {character_name}...")

# Use:
print(f"DEBUG: [Character Validator] Starting validation for {character_name}...")
```

The WebOutputCapture class already has logic at line 43-50 that routes messages starting with "DEBUG:" to the debug logger.

### Option 2: Add Character Validator Pattern to Debug Filters
Add character validator patterns to the debug message filters in web_interface.py around line 185:

```python
# In WebOutputCapture.write() method, add to the debug patterns list:
if any(marker in clean_line for marker in [
    'Lightweight chat history updated',
    'System messages removed:',
    # ... existing patterns ...
    '[Character Validator]',  # Add this
    '[AI Validator]',         # Add this
    '[Consolidation]',        # Add this
]):
    # These are debug messages - send to debug output
    debug_output_queue.put({
        'type': 'debug',
        'content': clean_line,
        'timestamp': datetime.now().isoformat()
    })
```

### Option 3: Force Flush Before Validator Messages
Ensure the Dungeon Master section is closed before validator messages:

```python
# In update_character_info.py, before calling validator:
sys.stdout.flush()  # Force flush any buffered DM content
print()  # Empty line to break DM section
print(f"[Character Validator] Starting validation for {character_name}...")
```

## Implementation Recommendation

I recommend **Option 1** as the quickest fix. Simply prefix all character validator print statements with "DEBUG: ".

This leverages existing routing logic without modifying the complex WebOutputCapture class.

## Testing
After implementing, test by:
1. Starting the web interface
2. Making a character update during gameplay
3. Verifying validator messages appear in Debug tab, not Game Output