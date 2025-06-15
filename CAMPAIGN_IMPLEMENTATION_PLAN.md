# Campaign Management System Implementation Plan

## Overview
Add minimal campaign management to connect modules while preserving your existing module-centric architecture. Focus on context management and continuity without rebuilding systems.

## Core Design Principles
- **Minimal Changes**: Extend existing systems, don't replace them
- **Token Budget**: 65k total context (Campaign 5k + Module Summaries 10k + Active Module 45k + Character 5k)
- **Hub-and-Spoke**: Keep of Doom becomes central hub after completion
- **Backward Compatible**: All existing modules continue to work unchanged

## Updated File Structure
```
modules/
├── campaign.json                    # NEW: Campaign state and progression
├── campaign_summaries/              # NEW: Compressed module summaries
│   ├── Village_summary.json         # PLACEHOLDER: Future intro module
│   ├── Keep_of_Doom_summary.json
│   └── [module]_summary.json
├── Village/                         # PLACEHOLDER: Future level 1 intro module
├── Keep_of_Doom/                    # EXISTING: Unchanged 
└── [future_modules]/
```

## New Components

### 1. modules/campaign.json (5kb)
```json
{
  "campaignName": "Chronicles of the Haunted Realm",
  "currentModule": "Keep_of_Doom", 
  "hubModule": null,
  "completedModules": ["Village"],
  "availableModules": ["Cursed_Mines", "Ancient_Library", "Merchant_Road"],
  "worldState": {
    "keepOwnership": false,
    "majorDecisions": [],
    "crossModuleRelationships": {
      "elen": {
        "status": "companion",
        "metInModule": "Village", 
        "currentLocation": "with_party"
      }
    },
    "unlockedAreas": [],
    "hubEstablished": false
  },
  "campaignLevel": 3,
  "totalSessionCount": 12,
  "tokenBudget": {
    "campaignContext": 5000,
    "moduleSummaries": 10000,
    "activeModule": 45000,
    "characterData": 5000
  }
}
```

### 2. Enhanced party_tracker.json
Add campaign fields to existing structure:
```json
{
  "module": "Keep_of_Doom",
  "campaign": "Chronicles_of_the_Haunted_Realm",
  "crossModuleData": {
    "elenRelationship": "companion",
    "keepDeededTo": "party",
    "originModule": "Village"
  },
  // ... existing fields unchanged
  "partyMembers": ["norn"],
  "partyNPCs": [
    {
      "name": "Elen",
      "role": "Scout and Ranger",
      "joinedInModule": "Village",
      "status": "active"
    }
  ]
}
```

### 3. Module Summary System
Generate 1000-token summaries when modules complete:

**modules/campaign_summaries/Keep_of_Doom_summary.json**
```json
{
  "moduleName": "Keep_of_Doom",
  "completionDate": "2025-06-15",
  "summary": "The party successfully cleared Shadowfall Keep of its curse, rescued Scout Elen who became a trusted companion, and acquired the deed to the keep through heroic actions. Sir Garran Vael was laid to rest, the shadow relic was [destroyed/bound], and the village of Harrow's Hollow was saved.",
  "keyDecisions": [
    "Saved Scout Elen",
    "Acquired keep deed",
    "Resolved curse peacefully"
  ],
  "consequences": {
    "keepOwnership": true,
    "elenCompanion": true,
    "villageReputation": "heroic"
  },
  "unlockedModules": ["Keep_Restoration", "Village_Defense", "Ancient_Library"],
  "tokens": 987
}
```

## Implementation Strategy

### Phase 1: Campaign Context Manager
- **New file**: `campaign_manager.py` - handles campaign state and module transitions
- **Extend**: `conversation_utils.py` - include campaign context in AI messages  
- **Extend**: `party_tracker.json` with campaign fields
- **Token allocation**: Campaign context limited to 5k tokens

### Phase 2: Module Completion Detection
- Detect module completion via quest status in `party_tracker.json`
- Generate module summary using existing AI summarization system
- Update campaign state and unlock new modules
- Move completed module to summary format

### Phase 3: Inter-Module Continuity
- Character data persistence (already works)
- Cross-module NPC tracking (Elen's journey from Village → Keep of Doom → future modules)
- Consequence propagation (Keep ownership affects future restoration/defense modules)

## Token Management Strategy
```
Active Context Breakdown:
- Campaign State: 2k tokens (current status, world state)
- Campaign Overview: 3k tokens (major decisions, relationships)
- Completed Module Summaries: 10k tokens (10 modules × 1k each)
- Active Module Full Context: 45k tokens (current location files)
- Character Sheets: 5k tokens (party + active NPCs)
TOTAL: 65k tokens (within OpenAI limits)
```

## Integration Points

### Existing Systems (No Changes)
- Module structure remains identical
- ModulePathManager works unchanged
- Character/combat/location systems untouched
- All existing files and schemas preserved

### Minimal Extensions
- Add campaign context to conversation history
- Detect module completion via existing quest completion
- Use existing AI summarization for module compression
- Store campaign files in `modules/` directory for easy access

## Campaign Flow Example

### Village (Placeholder) → Keep of Doom
1. Complete Village module (meet Elen, get hook to keep)
2. Generate summary: "Party met Scout Elen in village, learned of haunted keep threat"
3. Update campaign: `availableModules += ["Keep_of_Doom"]`
4. Start Keep of Doom with campaign context about Elen relationship

### Keep of Doom → Hub Establishment  
1. Complete Keep of Doom (acquire deed, save Elen)
2. Generate summary: "Party cleared keep curse, saved Elen as companion, owns property deed"
3. Update campaign: `hubModule = "Keep_of_Doom"`, `keepOwnership = true`
4. Unlock hub-based modules: Keep_Restoration, Village_Defense, Ancient_Library

### Future Module Connections
- **Keep ownership** unlocks restoration and defense quests
- **Elen relationship** affects all ranger/scouting modules
- **Village reputation** influences merchant and political modules
- **Hub location** becomes launch point for regional adventures

## Files to Create
1. `modules/campaign.json` - Campaign state management
2. `modules/campaign_summaries/` directory
3. `campaign_manager.py` - Campaign logic and transitions
4. `CAMPAIGN_IMPLEMENTATION_PLAN.md` - This document for reference

## Files to Modify
1. `party_tracker.json` - Add campaign fields
2. `conversation_utils.py` - Include campaign context
3. `main.py` - Detect module completion and trigger transitions

This plan creates a rich campaign experience while keeping changes minimal and working within your existing module-centric architecture. The placeholder Village module can be developed later, and the system supports unlimited future module expansion.