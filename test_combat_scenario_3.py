#!/usr/bin/env python3
"""
Test Combat Scenario 3: Complex multi-round combat with validation
Testing round tracking and validation with complex scenario
"""

import json

# Test prompt for validation scenario
test_prompt = """
Validate this combat response:

Current encounter state:
- Player: Norn (HP: 19/36)
- Monsters: Shadow (HP: 6/16), Skeleton (HP: 0/13, status: dead)
- Round: 2
- Initiative: Norn (17), Shadow (12), Skeleton (8)

AI Response:
{
  "narration": "The Shadow attempts to drain your strength! Using preroll d20 of 12 + 4 = 16 vs your AC 19, it misses. The skeletal warrior rises again and attacks with its rusty blade! Rolling d20... 18 + 4 = 22, that hits! You take 5 slashing damage. Now it's your turn Norn. The Shadow is wounded but still dangerous, and the skeleton continues its assault. What would you like to do?",
  "combat_round": 2,
  "actions": [
    {
      "action": "updateCharacterInfo",
      "parameters": {
        "characterName": "Norn",
        "changes": "Takes 5 slashing damage from skeleton attack. HP: 14/36"
      }
    }
  ]
}

Check if this response is valid according to combat rules.
"""

# Expected validation result:
# INVALID - Dead skeleton (0 HP) taking actions

print("\nTEST SCENARIO 3: Combat validation test")
print("=" * 50)
print("Testing if validation catches:")
print("- Dead creatures taking actions")
print("- Proper use of prerolls")
print("- Round tracking")
print("- Turn order violations")
print("\nTest Prompt:")
print(test_prompt)
print("\n" + "=" * 50)

# Save test prompt to file
with open('test_combat_validation_prompt.txt', 'w') as f:
    f.write(test_prompt)

print("\nValidation test saved to test_combat_validation_prompt.txt")