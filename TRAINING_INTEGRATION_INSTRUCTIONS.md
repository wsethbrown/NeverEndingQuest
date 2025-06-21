# Training Data Collection - Complete AI Interaction Capture

## What This Does
Captures the **complete conversation history** sent to the AI model and the **complete AI response** for training data, saved to `training_data.json`:
```json
[
  {
    "id": 1,
    "timestamp": "2025-06-17T23:15:00",
    "input": [
      {"role": "system", "content": "You are a DM..."},
      {"role": "user", "content": "What do I see around me?"},
      {"role": "assistant", "content": "Previous response..."},
      {"role": "user", "content": "I look around the tavern"}
    ],
    "output": "{\"narration\": \"You find yourself in the tavern...\", \"actions\": []}"
  }
]
```

## Integration Steps ✅ COMPLETED!

The integration has been completed in `main.py`. Here's what was added:

### Step 1: Import Added ✅
Added to main.py around line 99:
```python
# Import training data collection
from simple_training_collector import log_complete_interaction
```

### Step 2: Logging Added ✅
Added to the `get_ai_response()` function around line 562:
```python
def get_ai_response(conversation_history):
    status_processing_ai()
    response = client.chat.completions.create(
        model=DM_MAIN_MODEL,
        temperature=TEMPERATURE,
        messages=conversation_history
    )
    content = response.choices[0].message.content.strip()
    
    # Use the encoding utility to sanitize the AI response
    content = sanitize_text(content)
    
    # Log training data - complete conversation history and AI response
    try:
        log_complete_interaction(conversation_history, content)
    except Exception as e:
        print(f"Warning: Could not log training data: {e}")
    
    return content
```

## Ready to Use! ✅
- Training data collection is now **active**
- Every AI interaction will be logged to `training_data.json`
- Launch the web interface normally and play - training data will accumulate automatically
- No complex integration
- Just captures input->output pairs as you play

## File Output
Creates `training_data.json` with:
- Incremental IDs
- Timestamps
- Full conversation history as input
- Complete DM response as output
- Perfect for training data

## Usage
1. Make the 3 small edits above
2. Launch the web interface normally
3. Play the game
4. Check `training_data.json` for accumulated training examples

That's literally it - 3 lines of code and you're collecting training data!