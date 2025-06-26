# Thornwood Module Corrections Plan

Based on the review in claude.txt, the following inconsistencies need to be corrected in the BU files:

## Main Issues Identified:

### 1. "Rescue the Lost" (SQ004) Narrative Conflict
- **Problem**: Multiple versions of Scout Neris exist in different locations
- **Solution**: 
  - Remove healthy "Scout Neris" from Rangers' Outpost (RO04)
  - Remove lone "Wounded Scout Neris" from Ambush Site (TW01)
  - Remove lone "Rescued Merchant Lira" from Captive Camp (TW03)
  - Create new location TW06 - Wolf's Den Cave where both NPCs are found together

### 2. Silver Bell Network (SQ001) Quest Grounding
- **Problem**: Only one of three towers explicitly placed in locations
- **Solution**: Add the other two towers as "Features" in RO001_BU.json:
  - North Tower (stolen clapper) at Scout's Watch (RO04)
  - West Tower (shattered crystal) at Forgotten Waystation (RO05)

### 3. Module Context Synchronization
- **Problem**: Context file has outdated mappings and reflects the "multiple Neris" issue
- **Solution**: Update plot_scopes and consolidate NPC entries to match unified narrative

### 4. Minor Data Polish
- **Problem**: Inconsistent room types and climate/terrain fields
- **Solution**: 
  - Update room types in TW001_BU.json (e.g., "hall" to "clearing")
  - Standardize climate and terrain fields across all area files

## Files to Modify:
- RO001_BU.json
- TW001_BU.json
- module_context_BU.json

## Expected Outcome:
A complete and narratively consistent adventure module with proper quest grounding and NPC placement.