import json
import re

def extract_actions(text):
    actions = []
    start = 0
    while True:
        start = text.find('{', start)
        if start == -1:
            break
        
        # Find the matching closing brace
        brace_count = 1
        end = start + 1
        while brace_count > 0 and end < len(text):
            if text[end] == '{':
                brace_count += 1
            elif text[end] == '}':
                brace_count -= 1
            end += 1
        
        if brace_count == 0:
            json_str = text[start:end]
            try:
                action_data = json.loads(json_str)
                if "actions" in action_data and isinstance(action_data["actions"], list):
                    actions.extend(action_data["actions"])
                    print(f"DEBUG: Extracted action: {json_str}")
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                print(f"Problematic JSON string: {json_str}")
        
        start = end

    return actions

def process_actions(actions):
    for action_data in actions:
        if "action" not in action_data:
            print(f"WARNING: Invalid action format: {action_data}")
            continue

        action_type = action_data["action"]
        print(f"Action activated: {action_type}")

        if action_type == "updatePlayerInfo":
            changes = action_data["parameters"]["changes"]
            print(f"Player info would be updated with: {changes}")

# The text you shared
text = '''Norn, your thorough search pays off. In the hidden compartment behind the slightly ajar panel, you find a small cache of valuable items. Among the trinkets and tools, you discover:

- **50 Gold Pieces**: A small pouch filled with glittering coins.
- **A Jeweled Dagger**: A finely crafted dagger with a jeweled hilt.
- **A Scroll of Identify**: A magical scroll that can identify the properties of a magical item.

---

{
  "actions": [
    {
      "action": "updatePlayerInfo",
      "parameters": {
        "changes": "Added 50 Gold Pieces, Jeweled Dagger, and Scroll of Identify to inventory"
      }
    }
  ]
}'''

# Process the text
actions = extract_actions(text)
process_actions(actions)