# Expected Combat Responses with New System

## Scenario 1: Initial Combat Turn (EXPECTED CORRECT RESPONSE)

```json
{
  "narration": "The ancient chapel's shadows seem to writhe and coalesce as a dark form emerges from behind a toppled pew. The Shadow, a creature of pure darkness, glides silently toward you, its form rippling with malevolent energy. The temperature drops noticeably as it approaches, and you can feel the chill of the grave emanating from its insubstantial form.\n\nYou grip your longsword tighter, ready for battle. The Shadow hovers just out of reach, waiting for an opening.\n\nIt's your turn, Norn. You face the Shadow in this ruined chapel. What would you like to do?",
  "combat_round": 1,
  "actions": []
}
```

**Why this is correct:**
- ✓ Describes the scene engagingly
- ✓ Asks for player action
- ✓ Does NOT roll dice or take actions
- ✓ Includes combat_round: 1
- ✓ Waits for player input

## Scenario 2: After Player Declares Attack (EXPECTED CORRECT RESPONSE)

```json
{
  "narration": "You swing your longsword at the Shadow with practiced precision. Using the prerolled d20 of 15, plus your attack bonus of +5, your total attack roll is 20 - easily hitting the Shadow's AC of 12!\n\nYour blade cuts through the creature's ethereal form. Using the prerolled d8 of 4, plus your damage modifier of +3, you deal 7 points of slashing damage to the Shadow. It recoils, its form flickering as your blessed steel disrupts its essence.\n\nThe Shadow retaliates, reaching out with tendrils of darkness to drain your life force. Using the prerolled d20 of 8, plus its attack bonus of +4, it rolls a total of 12. The attack misses your AC of 19 as you deflect the grasping shadows with your shield.\n\nThe round ends with the Shadow wounded but still dangerous, hovering before you in the dim chapel light.\n\nRound 2 begins. It's your turn again, Norn. The Shadow has taken 7 damage and appears weakened. What would you like to do?",
  "combat_round": 2,
  "actions": [
    {
      "action": "updateEncounter",
      "parameters": {
        "encounterId": "C03-E1",
        "changes": "Shadow takes 7 slashing damage from Norn's longsword attack. HP reduced from 16 to 9."
      }
    }
  ]
}
```

**Why this is correct:**
- ✓ Uses prerolls in correct order (d20: 15, d8: 4)
- ✓ Calculates correctly (15+5=20 to hit, 4+3=7 damage)
- ✓ Continues to monster's turn
- ✓ Completes full round before stopping
- ✓ Increments combat_round to 2
- ✓ Updates encounter with damage
- ✓ Returns to player with clear prompt

## Scenario 3: Validation of Bad Response (EXPECTED VALIDATION RESULT)

```json
{
  "valid": false,
  "reason": "INVALID: Dead creature taking actions. The Skeleton has 0 HP and status 'dead' but is described as 'rising again and attacking' in the narration. Dead creatures cannot take any actions in combat. The skeleton's attack roll and damage should not have occurred.",
  "recommendation": "The combat should flow as follows: 1) Shadow attacks Norn (miss with roll of 16 vs AC 19), 2) Skip skeleton's turn entirely as it is dead, 3) Return to Norn's turn for round 2. No damage should be dealt to Norn from the skeleton."
}
```

**Why this validation is correct:**
- ✓ Catches dead creature acting
- ✓ Provides detailed explanation
- ✓ Specifies exact violation
- ✓ Gives clear recommendation

## Common Issues Our Changes Should Prevent:

### Before Changes:
- AI would use wrong dice from pools
- AI would assume player actions without confirmation
- AI would skip asking for player input
- Validation would give vague "No reason provided"

### After Changes:
- Clear preroll usage instructions
- Explicit turn confirmation requirement
- Separate round tracking reduces complexity
- Required detailed validation explanations