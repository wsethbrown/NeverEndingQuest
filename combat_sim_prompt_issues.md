# Combat Simulation Prompt Issues Found

## Major Issues Identified:

### 1. **Missing `combat_round` field in ALL examples**
- None of the existing examples include the required `combat_round` field
- This violates our new JSON structure requirement

### 2. **Examples asking for dice rolls when prerolls should be used**
- Multiple examples say "Rolling a d20..." without clarifying if prerolls exist
- Examples don't follow our rule: only ask for rolls when NO prerolls available

### 3. **Incorrect action types**
- Example uses `"action": "modify"` which doesn't exist
- Should be `updateEncounter` or `updateCharacterInfo`

### 4. **Using deprecated `updateNPCInfo`**
- Many examples still use `updateNPCInfo` 
- Should use `updateCharacterInfo` with characterName parameter

### 5. **Wrong status field values**
- Example uses 'Alive' and 'Dead' (capitalized)
- Should be lowercase: 'alive', 'dead', 'unconscious'

### 6. **Not following turn confirmation requirement**
- Some examples show player actions without first asking what they want to do
- Violates our TURN CONFIRMATION REQUIREMENT

## Examples of Issues:

### Issue 1: Exit action example (line 259)
```json
// WRONG - Missing combat_round, wrong action type
{
  "narration": "...",
  "actions": [
    {
      "action": "modify",  // WRONG ACTION TYPE
      "parameters": {
        "modificationDetails": "..."
      }
    }
  ]
}
```

### Issue 2: CRITICAL EXAMPLE (line 291)
```json
// WRONG - Missing combat_round, uses updateNPCInfo
{
  "narration": "...",
  "actions": [
    {
      "action": "updateNPCInfo",  // DEPRECATED
      "parameters": {
        "npcName": "Elara",
        "changes": "..."
      }
    }
  ]
}
```

### Issue 3: Examples showing dice rolls without clarifying preroll usage
- Line 294: "Rolling a d20... 16!"
- Should clarify: "Using prerolled d20 of 16" OR "Please roll a d20"

## Fixes Needed:
1. Add `combat_round` to all examples
2. Replace all `updateNPCInfo` with `updateCharacterInfo`
3. Fix the `modify` action to `updateEncounter`
4. Ensure status fields use lowercase
5. Clarify preroll usage in all dice examples