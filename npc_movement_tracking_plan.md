# NPC Movement and Status Tracking Enhancement Plan

## Problem Identified

The current system lacks proper protocols for tracking NPC movement, removal, and status changes during gameplay. This leads to continuity errors where NPCs appear in locations they should no longer be present.

### Evidence from Recent Issues:

**From claude.txt debug log:**
- Line 10: Validation failed trying to use invalid `updatePartyNPCs` action
- Line 32: `Error: Could not load character data for Rusk`
- Line 34: `ERROR: Failed to update character info for Rusk`

**Story Context Problem:**
- Rusk was captured and interrogated at Rangers' Command Post
- AI tried to remove/update Rusk's status but failed due to missing character data
- Rusk likely still appears as "present" in location data despite story progression
- No clear mechanism exists to handle NPC removal or status changes

## Current System Gaps

### 1. Missing NPC Status Management
- No standardized way to mark NPCs as "captured", "moved", "escaped", or "eliminated"
- No tracking of NPC location changes during story events
- Location NPC lists remain static despite story progression

### 2. Inadequate Character Data Handling
- NPCs referenced in location files may not have corresponding character files
- `updateCharacterInfo` fails when character data doesn't exist
- No fallback mechanism for NPCs without full character sheets

### 3. Location Data Inconsistency  
- NPCs removed from story still listed as present in location data
- No automatic updating of location NPC lists when status changes
- No notation of where NPCs went or why they're absent

### 4. Validation System Gaps
- Validation allows references to NPCs who should no longer be present
- No checking of NPC status consistency across locations
- Missing protocols for NPC movement between areas

## Proposed Solution Framework

### Phase 1: NPC Status Tracking System

#### 1.1 Enhanced Character Status Fields
Add to character data structure:
```json
{
  "status": "active|captured|moved|eliminated|absent",
  "currentLocation": "RO01",
  "statusReason": "Captured during interrogation",
  "statusDate": "1492 Springmonth 1",
  "movedTo": "secure_holding|capital|unknown",
  "removedFromPlay": false
}
```

#### 1.2 NPC Movement Action Protocol
Create standardized process for NPC status changes:
1. Use `updateCharacterInfo` to update NPC status
2. Include removal reason and destination
3. Update location NPC lists automatically
4. Add status notation to location descriptions

### Phase 2: Location Data Synchronization

#### 2.1 Dynamic NPC List Management
- Automatically remove NPCs from location lists when status changes
- Add "absent NPCs" section noting who was removed and why
- Update location descriptions to reflect NPC absence

#### 2.2 NPC Presence Validation
- Validate NPC references against current status
- Prevent AI from referencing moved/captured NPCs as present
- Suggest appropriate replacements or note absences

### Phase 3: AI Instruction Enhancement

#### 3.1 NPC Movement Protocols
Add to system prompts:
```
When NPCs are captured, moved, killed, or otherwise removed:
1. Use updateCharacterInfo to change status to appropriate value
2. Include clear reason for status change
3. Specify where NPC went (if applicable)
4. Update narrative to reflect absence in future interactions
```

#### 3.2 Validation Rules Enhancement
```
NPC CONTINUITY VALIDATION:
- Check NPC status before allowing interactions
- NPCs with status "captured|moved|eliminated" cannot be referenced as present
- Require status updates when story events affect NPC presence
- Validate location NPC lists against current NPC statuses
```

### Phase 4: Error Handling Improvements

#### 4.1 Missing Character Data Handling
- Create lightweight NPC records for location-only characters
- Implement fallback character creation for validation failures
- Add NPC type classification (major|minor|background)

#### 4.2 Graceful Status Management
- Handle character data errors without breaking gameplay
- Provide clear error messages for NPC management failures
- Log NPC status changes for debugging and continuity tracking

## Implementation Priority

### High Priority (Immediate):
1. Fix Rusk's status inconsistency 
2. Add NPC status tracking to character data
3. Update validation to check NPC presence consistency

### Medium Priority:
1. Implement automatic location NPC list updates
2. Add AI instructions for NPC movement protocols
3. Create missing character data fallbacks

### Low Priority (Future Enhancement):
1. Build comprehensive NPC movement history tracking
2. Add automated location description updates
3. Implement cross-location NPC consistency checking

## Expected Benefits

✅ **Prevents Continuity Errors**: NPCs won't appear where they shouldn't be  
✅ **Improves Immersion**: Story progression properly reflected in world state  
✅ **Reduces Validation Failures**: Clear protocols for NPC status management  
✅ **Enhanced AI Guidance**: Better instructions for handling NPC changes  
✅ **Error Prevention**: Graceful handling of missing/invalid character data  

## Test Cases for Validation

1. **Captured NPC**: Rusk captured → status updated → removed from location → validation prevents future references
2. **Moved NPC**: Scout transferred → location updated → new location shows NPC present
3. **Eliminated NPC**: Bandit killed → status updated → location reflects absence
4. **Returned NPC**: Character leaves and returns → status tracking maintains continuity

---

*Created: 2025-06-25*  
*Priority: High - Affects core gameplay continuity*