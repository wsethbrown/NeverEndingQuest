# Fix Module Builder Context Contamination Plan

## Problem Analysis

The module builder is inappropriately using current party members (Norn, Elen) and existing locations (Harrow's Hollow) when creating new modules. Investigation revealed several key issues:

### Issues Identified:

1. **Hardcoded Party Names**: Module builder has `party_names = ["Norn", "Elen"]` as fallback (line 212 in module_builder.py)
2. **Raw Concept Contamination**: Concept text mentioning "Norn and Elen are called to investigate" gets passed directly to AI generators
3. **No Context Separation**: Generators receive full narrative including specific party member names and existing locations
4. **NPCs Created from Context**: Location generator creates NPCs like "Norn (village reeve)" because it sees these names in concept text
5. **Location Recycling**: New modules reference existing campaign locations like "Harrow's Hollow"

### Root Cause:
The AI narrator's concept includes current campaign context (party members, locations) which gets passed unsanitized to the module builder, causing new modules to reference existing campaign elements instead of creating standalone adventures.

### Evidence from Generated Module:
- Created area "HH002" named "Harrow's Hollow" (recycling existing location)
- Generated NPC "Norn (village reeve)" (duplicating existing party member)
- Themes mention "characters arrive in Harrow's Hollow" (not a new adventure start)
- Multiple plot hooks reference existing campaign elements

## Solution Plan

### 1. Create Concept Sanitization Function
**File:** `module_builder.py`

**Function:** `sanitize_concept_for_new_module(concept: str) -> str`

**Purpose:** 
- Strip current party/location references from concept text
- Extract core adventure themes while removing specific character names
- Replace location-specific references with generic terms
- Preserve atmospheric and thematic elements

**Implementation:**
```python
def sanitize_concept_for_new_module(self, concept: str) -> str:
    """
    Transform current-campaign narrative into generic adventure concept
    Removes specific party members, locations, and campaign references
    """
    # Remove specific character names (Norn, Elen, etc.)
    # Replace location names with generic terms
    # Extract core themes and atmosphere
    # Return sanitized concept suitable for new module generation
```

### 2. Add Generic Adventure Prompt Template
**File:** `module_builder.py`

**Purpose:** Create standardized template that focuses on adventure themes rather than current party context

**Template Structure:**
```
GENERIC ADVENTURE TEMPLATE:
- Core Theme: [extracted from concept]
- Adventure Type: [dungeon/wilderness/urban/mixed]
- Atmosphere: [extracted mood and tone]
- Plot Hooks: [generalized from concept]
- Level Range: [specified range]

IMPORTANT: This is a STANDALONE adventure. Do not reference:
- Existing party members by name
- Current campaign locations
- Ongoing storylines from other modules
```

### 3. Fix Hardcoded Party Names
**File:** `module_builder.py` line 212

**Current Issue:**
```python
if not party_names:
    party_names = ["Norn", "Elen"]  # PROBLEM: Hardcoded current party
```

**Fix:**
```python
if not party_names:
    party_names = []  # Empty list - new modules shouldn't reference current party
    # OR use generic placeholder names if needed: ["Adventurer_1", "Adventurer_2"]
```

### 4. Update Module Generation Prompts
**Files:** `module_generator.py`, `location_generator.py`, `plot_generator.py`

**Add Instructions:**
- Explicit warnings against using current campaign character names
- Emphasis on creating NEW, unique characters and locations
- Guidelines for creating standalone adventures
- Instructions to avoid referencing existing campaign elements

**Prompt Additions:**
```
CRITICAL INSTRUCTIONS:
- This is a NEW, STANDALONE adventure module
- Do NOT use existing character names from current campaign
- Do NOT reference existing locations (Harrow's Hollow, etc.)
- CREATE unique NPCs with original names
- DESIGN new settlements with distinct identities
- ENSURE this adventure can be played independently
```

### 5. Add Context Isolation Layer
**File:** `module_builder.py`

**Function:** `extract_adventure_essence(concept: str) -> Dict[str, str]`

**Purpose:** Transform current-campaign narrative into isolated adventure elements

**Process:**
1. **Extract Core Elements:**
   - Adventure theme (horror, mystery, exploration, etc.)
   - Setting type (riverside, underground, forest, etc.)
   - Atmosphere descriptors (haunting, mysterious, ancient, etc.)
   - Conflict type (curse, invasion, corruption, etc.)

2. **Filter Out Specifics:**
   - Character names (Norn, Elen → generic adventurers)
   - Location names (Harrow's Hollow → riverside settlement)
   - Campaign references (existing modules, ongoing plots)

3. **Create Generic Framework:**
   - "A [THEME] adventure where adventurers investigate [MYSTERY]"
   - "Set in a [SETTING_TYPE] environment with [ATMOSPHERE]"
   - "Features [CONFLICT_TYPE] that threatens [GENERIC_LOCATION]"

### 6. Module Builder Flow Update
**File:** `module_builder.py` - `build_module()` method

**New Process:**
```python
def build_module(self, initial_concept: str):
    # Step 0: Sanitize concept for new module generation
    sanitized_concept = self.sanitize_concept_for_new_module(initial_concept)
    
    # Step 1: Extract adventure essence
    adventure_essence = self.extract_adventure_essence(sanitized_concept)
    
    # Step 2: Create generic adventure template
    generic_template = self.create_generic_template(adventure_essence)
    
    # Step 3: Generate module with isolated context
    self.module_data = self.module_gen.generate_module(generic_template, context=self.context)
    
    # Continue with existing steps...
```

### 7. Testing and Validation
**Create Test Cases:**
1. **Input:** Concept mentioning "Norn and Elen investigate Harrow's Hollow river mystery"
2. **Expected Output:** New module with unique location and NPCs, no references to Norn/Elen/Harrow's Hollow
3. **Verify:** Generated NPCs have original names, locations are distinct from existing campaign

## Implementation Priority

### Phase 1: Immediate Fixes (High Priority)
1. Remove hardcoded party names fallback
2. Add basic concept sanitization function
3. Update generator prompts with isolation instructions

### Phase 2: Enhanced Context Separation (Medium Priority)
1. Implement adventure essence extraction
2. Create generic adventure template system
3. Add comprehensive filtering for campaign-specific references

### Phase 3: Testing and Refinement (Low Priority)
1. Create automated tests for context isolation
2. Refine sanitization algorithms based on results
3. Add debug logging for concept transformation process

## Expected Results After Implementation

### Before (Current Issues):
- New modules reference "Harrow's Hollow"
- NPCs named "Norn (village reeve)", "Elen (river guide)"
- Adventures feel like extensions of current campaign
- Context contamination from existing storylines

### After (Fixed System):
- New modules have unique, standalone locations
- NPCs have original names fitting the new adventure
- Adventures are self-contained and independent
- Clean separation between existing campaign and new modules
- Proper thematic coherence without context bleeding

## Files to Modify

1. **`/mnt/c/dungeon_master_v1/module_builder.py`**
   - Add sanitization functions
   - Fix hardcoded party names
   - Update build process flow

2. **`/mnt/c/dungeon_master_v1/module_generator.py`**
   - Add isolation instructions to prompts
   - Enhance new-adventure guidelines

3. **`/mnt/c/dungeon_master_v1/location_generator.py`**
   - Add warnings against existing character names
   - Emphasize creating unique NPCs

4. **`/mnt/c/dungeon_master_v1/plot_generator.py`**
   - Ensure plot references don't leak campaign context
   - Focus on standalone adventure narratives

This plan addresses the root cause of context contamination and ensures new modules are truly independent adventures rather than extensions of the current campaign.