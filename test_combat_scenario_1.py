#!/usr/bin/env python3
"""
Test Combat Scenario 1: Basic combat with prerolls
Testing if the AI correctly uses prerolls and waits for player confirmation
"""

import json
import subprocess
import sys

# Test prompt simulating combat with a single enemy
test_prompt = """
You are running a combat encounter. Here is the scenario:

Player Character: Norn (Fighter, Level 4, AC 19, HP 19/36)
Monster: Shadow (AC 12, HP 16)
Location: Ruined Chapel

Initiative Order:
1. Norn (17)
2. Shadow (10)

Prerolled dice for this encounter:
d20 rolls: [15, 8, 19, 12, 6, 20, 11, 14, 9, 17]
d8 rolls: [4, 7, 2, 8, 5, 3, 6, 1]
d4 rolls: [2, 4, 1, 3, 2, 4]

The combat has just begun. It is Norn's turn.

Remember to:
1. Use prerolls from the appropriate pools
2. Wait for player confirmation before taking their action
3. Track combat rounds separately
4. Include all required JSON fields
"""

# Expected behavior:
# 1. AI should describe the scene
# 2. AI should ask Norn what they want to do
# 3. AI should NOT roll or take action for Norn yet
# 4. AI should include combat_round: 1

print("TEST SCENARIO 1: Basic combat with prerolls")
print("=" * 50)
print("Testing if AI:")
print("- Uses prerolls correctly")
print("- Waits for player confirmation")
print("- Tracks combat rounds")
print("- Follows new JSON format")
print("\nTest Prompt:")
print(test_prompt)
print("\n" + "=" * 50)

# Save test prompt to file for manual testing
with open('test_combat_prompt_1.txt', 'w') as f:
    f.write(test_prompt)

print("\nTest prompt saved to test_combat_prompt_1.txt")
print("To test manually, copy this prompt to the combat simulation")