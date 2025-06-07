#!/usr/bin/env python3
"""
Test Combat Scenario 2: Player action response
Testing if the AI correctly processes player action with prerolls
"""

import json

# Test prompt simulating player's response to attack
test_prompt = """
The player responds: "I attack the Shadow with my longsword"

Current State:
- It is still Norn's turn
- Shadow has AC 12, HP 16
- Norn has +5 attack bonus, 1d8+3 damage with longsword
- This is combat round 1

Prerolled dice remaining:
d20 rolls: [15, 8, 19, 12, 6, 20, 11, 14, 9, 17] (none used yet)
d8 rolls: [4, 7, 2, 8, 5, 3, 6, 1] (none used yet)

Remember to:
1. Use the first d20 (15) for Norn's attack roll
2. If hit, use the first d8 (4) for damage
3. Then continue to Shadow's turn
4. Complete the full round before stopping
"""

# Expected behavior:
# 1. AI uses d20 roll of 15 + 5 = 20 (hit)
# 2. AI uses d8 roll of 4 + 3 = 7 damage
# 3. Shadow takes 7 damage (16 - 7 = 9 HP remaining)
# 4. AI continues to Shadow's turn using next prerolls
# 5. AI completes round and returns to player

print("\nTEST SCENARIO 2: Player action with prerolls")
print("=" * 50)
print("Testing if AI:")
print("- Uses correct prerolls in order")
print("- Calculates damage correctly")
print("- Continues through full round")
print("- Updates monster HP properly")
print("\nTest Prompt:")
print(test_prompt)
print("\n" + "=" * 50)

# Save test prompt to file
with open('test_combat_prompt_2.txt', 'w') as f:
    f.write(test_prompt)

print("\nTest prompt saved to test_combat_prompt_2.txt")