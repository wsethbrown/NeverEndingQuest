# Simple AI-Autonomous Module Creation System

## Overview
Enable the AI DM to autonomously create new adventure modules during natural conversation flow, using all accumulated party information to generate contextually appropriate adventures.

## Core Components

### 1. Enhanced AI System Prompt
**Location**: `system_prompt.txt` or main system prompt

**Add New Capability**:
```
"When the current module is complete and no other adventures are available, you may 
autonomously create a new adventure module by calling createNewModule. Base the new 
adventure on the party's journey, interests, and current level. Include:

Required Parameters:
- concept: Brief adventure concept based on party's story/interests
- num_areas: Number of areas (1-3, recommend 2 for most adventures)
- locations_per_area: Locations per area (8-15 recommended)
- module_name: Descriptive name for the adventure
- level_range: Appropriate for current party level (+/- 1 level)
- adventure_type: dungeon/wilderness/urban/mixed based on party preferences
- plot_themes: Key themes based on party's previous adventures

Example: createNewModule("Ancient ruins discovered near the cursed forest", 2, 12, "Ruins_of_Shadowmere", {3,5}, "dungeon", "undead,ancient magic,mystery")
```

### 2. Module Builder Enhancement
**Location**: Modify `module_builder.py`

**New Function**:
```python
def ai_driven_module_creation(concept, num_areas, locations_per_area, 
                            module_name, level_range, adventure_type, plot_themes):
    # Create BuilderConfig from AI parameters
    # Use concept and themes to guide generation
    # Auto-generate appropriate content
    # Return success/failure status
```

**Key Changes**:
- Accept single comprehensive input instead of interactive prompts
- Use AI-provided concept to guide all generation decisions
- Make reasonable defaults for any missing parameters
- Auto-integrate with existing world via module_stitcher

### 3. Action Handler Integration
**Location**: `action_handler.py`

**New Action**:
```python
def handle_createNewModule(params):
    # Parse AI-provided parameters
    # Call enhanced module_builder
    # Auto-integrate via module_stitcher
    # Update world registry
    # Return status to AI
```

### 4. Simple Completion Detection
**Location**: `main.py` or `campaign_manager.py`

**Minimal Check**:
- After each action, check if current module plot is complete
- Check if other modules are available in world registry
- If both conditions met, add context note to AI about module creation availability

## Implementation Details

### AI Parameters Schema
```
createNewModule(
    concept: "Adventure concept based on party history",
    num_areas: 1-3 (default 2),
    locations_per_area: 8-15 (default 12), 
    module_name: "Descriptive_Name",
    level_range: {min: X, max: Y},
    adventure_type: "dungeon|wilderness|urban|mixed",
    plot_themes: "theme1,theme2,theme3"
)
```

### Module Builder Flexibility
- Use concept to generate module description and world map
- Use plot_themes to guide area generation and monster selection
- Use adventure_type to determine area types and structure
- Auto-calculate appropriate difficulty based on level_range
- Make smart defaults: if num_areas missing, use 2; if locations missing, use 12

### Integration Flow
```
Player Action → Check Module Complete → Add AI Context Note → 
AI Decides to Create → AI Calls createNewModule → Module Builder Generates → 
Auto-Stitch → Auto-Backup → World Registry Update → AI Continues Naturally
```

## Technical Changes

### Files to Modify:
1. **System Prompt**: Add createNewModule capability description
2. **action_handler.py**: Add createNewModule action handler
3. **module_builder.py**: Add ai_driven_module_creation function
4. **main.py**: Add simple completion detection context note

### New Dependencies:
- Module builder must accept single parameter input
- Action handler must parse and validate AI parameters
- Automatic integration with existing module_stitcher

## Example AI Behavior
```
Player: "Well, we've solved the mystery of the haunted village!"
AI: "Indeed! The villagers are safe and the curse is lifted. As you stand in the 
village square, you notice ancient maps in the elder's home showing unexplored 
ruins to the east..." 

[AI calls: createNewModule("Mysterious ancient ruins with magical artifacts", 2, 10, "Ancient_Spire_Ruins", {3,5}, "dungeon", "ancient magic,puzzles,treasure")]

AI: "The elder mentions legends of the Ancient Spire Ruins, where powerful 
artifacts are said to be hidden. The path east beckons with new adventure..."
```

## Benefits
- **Zero Player Interruption**: Seamless natural conversation flow
- **Contextual Adventures**: AI uses all party history to create relevant content
- **Minimal Complexity**: Single function call with smart defaults
- **Autonomous Operation**: AI handles everything without prompting
- **Flexible Parameters**: Module builder adapts to any AI input

This approach treats module creation as just another AI action, like updating plot or transitioning locations, keeping the experience completely seamless.

## Implementation Priority
1. Enhance system prompt with createNewModule capability
2. Add action handler for createNewModule
3. Modify module_builder.py to accept AI parameters
4. Add completion detection context notes
5. Test with complete module scenario

## Success Criteria
- AI can autonomously create modules during natural conversation
- Generated modules integrate seamlessly with existing world
- No player interruption or explicit prompting required
- Module creation feels like natural story progression
- All existing safety and backup systems continue to work