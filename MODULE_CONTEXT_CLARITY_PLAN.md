# Module Context Clarity Plan - Revised Approach

## Problem Summary

The module builder is creating NPCs named after party members (Norn, Elen) and reusing existing locations (Harrow's Hollow) because:
1. The narrative generator mentions current location and party members
2. Module builders don't understand these are CURRENT context, not NEW content to create
3. No clear distinction between "where party is NOW" vs "where module should be SET"

## Revised Solution: Context Clarity Through Better Prompts

### 1. Update Module Creation Prompt (module_creation_prompt.txt)

**Add Context Clarification Section:**
```
CONTEXT UNDERSTANDING FOR MODULE CREATION:
When the narrative mentions specific names and places, understand:
- Character names (like Norn, Elen) = CURRENT PARTY MEMBERS who will PLAY this adventure
- Location names (like Harrow's Hollow) = WHERE THEY ARE NOW, not where to set the module
- Your task: Create a NEW location they will TRAVEL TO for this adventure

NARRATIVE GENERATION RULES:
Option A (Preferred): Avoid mentioning current location entirely
   Example: "The party hears rumors of [new adventure] to the [direction]"
   
Option B: Clearly separate current from new
   Example: "While in [current location], the party learns of troubles in [NEW PLACE]"
   
NEVER write: "[Party] investigates [current location]" - this implies the module is set there!

The module you create should be a DESTINATION, not the current location.
```

### 2. Update Module Builder Prompts

**File:** `module_builder.py`

**Add Party Context Handling:**
```python
def build_module(self, initial_concept: str):
    # Get current party members for context
    party_members = self.get_party_members()
    
    # Create context header for all generators
    context_header = f"""
CRITICAL CONTEXT INFORMATION:
===========================
PARTY MEMBERS (Heroes who will PLAY this adventure): {', '.join(party_members)}
- These are the PLAYER CHARACTERS
- Do NOT create NPCs with these names
- They are the protagonists, not residents of your locations

LOCATION CONTEXT:
- The party is CURRENTLY elsewhere (not in your module)  
- Create a NEW location they will TRAVEL TO
- This should be a completely different place from their current location
===========================
"""
```

### 3. Update Generator Prompts

**Files to Update:**
- `module_generator.py`
- `location_generator.py` 
- `plot_generator.py`
- `area_generator.py`

**Add to Each Generator's System Prompt:**
```
MODULE INDEPENDENCE RULES:
1. This module represents a NEW DESTINATION
2. Party members listed in context are PLAYERS, not NPCs
3. Create all-new locations, not variations of existing ones
4. If you see "Harrow's Hollow" in the concept, that's where they START, not where to build

NPC CREATION RULES:
- Check party member list - NEVER use those names for NPCs
- Create unique NPCs with original names and roles
- Example: If "Norn" is a party member, do NOT create "Norn the merchant"

LOCATION CREATION RULES:  
- This is a NEW place the party has never been
- Give it a unique name and identity
- It should feel distinct from their starting location
```

### 4. Fix Hardcoded Party Names

**File:** `module_builder.py` line 212

**Current:**
```python
if not party_names:
    party_names = ["Norn", "Elen"]
```

**Change to:**
```python
if not party_names:
    party_names = []  # Empty - let each module detect its own party
    # Log this for debugging
    self.log("No party members detected - module will use generic references")
```

### 5. Add Validation Layer

**File:** `module_builder.py`

**Add Validation Function:**
```python
def validate_no_party_contamination(self, generated_content: Dict, party_members: List[str]) -> List[str]:
    """
    Check that party member names aren't used as NPCs
    Returns list of warnings if issues found
    """
    warnings = []
    party_names_lower = [name.lower() for name in party_members]
    
    # Check NPCs in all locations
    for area in generated_content.get('areas', {}).values():
        for location in area.get('locations', []):
            for npc in location.get('npcs', []):
                npc_name_lower = npc.get('name', '').lower()
                for party_name in party_names_lower:
                    if party_name in npc_name_lower:
                        warnings.append(f"WARNING: NPC '{npc['name']}' shares name with party member '{party_name}'")
    
    return warnings
```

### 6. Update Area Generator for Better Descriptions

**File:** `area_generator.py`

Since we found hardcoded area descriptions like "medium settlement where civilization meets the frontier", ensure the area generator creates unique descriptions:

```python
# In the prompt for area generation
area_prompt = f"""
Create a unique area description for {area_name}.
This is a NEW location in a NEW module - make it distinctive.
Avoid generic phrases like "where civilization meets the frontier".
Give it character that reflects the module's themes.
"""
```

## Implementation Priority

### Phase 1: Immediate Fixes
1. **Update module_creation_prompt.txt** with clear context rules
2. **Fix hardcoded party names** fallback
3. **Add context header** to module builder

### Phase 2: Generator Updates  
1. **Update all generator prompts** with party/location awareness
2. **Add validation function** to check for contamination
3. **Fix area description generation** to avoid hardcoded templates

### Phase 3: Testing
1. **Test with current party** (Norn, Elen) to ensure no NPC contamination
2. **Verify new locations** are unique, not variations of Harrow's Hollow
3. **Check area descriptions** are varied and thematic

## Expected Results

### Before:
- Narrative: "Norn and Elen investigate the river near Harrow's Hollow"
- Result: Module creates "Norn (village reeve)" NPC in "Harrow's Hollow" area

### After:
- Narrative: "The party hears of mysterious happenings along a distant river"
- OR: "From Harrow's Hollow, the party must journey to [NEW LOCATION]"
- Result: Module creates unique NPCs in a completely new location

## Key Differences from Original Plan

1. **No Name Stripping**: Keep party names in concept but add clear context
2. **Explicit Context Headers**: Tell generators what names/places mean
3. **Narrative Guidance**: Help AI narrator avoid location confusion
4. **Validation Instead of Sanitization**: Check output rather than modify input

## Files to Modify

1. **`/mnt/c/dungeon_master_v1/module_creation_prompt.txt`**
   - Add context understanding rules
   - Guide narrative generation

2. **`/mnt/c/dungeon_master_v1/module_builder.py`**
   - Add context headers for generators
   - Fix hardcoded party names
   - Add validation function

3. **`/mnt/c/dungeon_master_v1/module_generator.py`**
   - Add party/location awareness to prompts

4. **`/mnt/c/dungeon_master_v1/location_generator.py`**
   - Emphasize not using party names for NPCs

5. **`/mnt/c/dungeon_master_v1/area_generator.py`**
   - Ensure unique area descriptions (already fixed by agent)

This approach maintains narrative flow while ensuring clear separation between current campaign context and new module content.