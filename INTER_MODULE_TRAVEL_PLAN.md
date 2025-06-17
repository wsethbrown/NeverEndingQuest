# Inter-Module Travel Implementation Plan

## 🎯 **Objective**
Implement seamless inter-module travel using existing architecture with minimal code changes. Enable players to travel between modules using natural language commands like "I travel to Pigs in the Mountain" with automatic conversation archiving and summary generation.

## 🏗️ **Architecture Overview**

### **Core Concept**
```
Player: "I travel to Pigs in the Mountain"
↓
AI: 1. Archive current conversation (if module changes)
    2. Generate module summary (if leaving module)
    3. Update party_tracker.json (module + starting location)
    4. Generate travel narration (using existing AI stitcher)
    5. Narrate arrival at new module
    6. All in one seamless response
```

### **Implementation Strategy: Option 1 - Extend updatePartyTracker**
- ✅ Uses existing `updatePartyTracker` action (no new actions needed)
- ✅ Leverages existing AI travel narration from module_stitcher.py
- ✅ Uses existing conversation archiving system
- ✅ Simple, elegant, low-code solution

## 📋 **Implementation Steps**

### **Step 1: Backup Everything to GitHub** ✅
- Commit all current work
- Push to remote repository
- Ensure clean state before modifications

### **Step 2: Enhance updatePartyTracker Action Handler**
**File**: `/mnt/c/dungeon_master_v1/action_handler.py`

**Add module change detection logic**:
```python
elif action_type == ACTION_UPDATE_PARTY_NPCS:
    # Existing NPC update logic...
    
elif action_type == "updatePartyTracker":  # Add this new handler
    """Handle party tracker updates with module change detection"""
    
    # Load current party tracker
    current_party_data = safe_json_load("party_tracker.json")
    current_module = current_party_data.get("module", "Unknown")
    
    # Check if module is being changed
    new_module = parameters.get("module")
    if new_module and new_module != current_module:
        print(f"DEBUG: Module change detected: {current_module} -> {new_module}")
        
        # Import campaign manager for auto-archiving
        from campaign_manager import CampaignManager
        campaign_manager = CampaignManager()
        
        # Auto-archive and summarize previous module
        if current_module != "Unknown":
            summary = campaign_manager.handle_cross_module_transition(
                current_module, new_module, current_party_data, conversation_history
            )
            if summary:
                print(f"DEBUG: Archived conversation and generated summary for {current_module}")
    
    # Update party tracker with all provided parameters
    for key, value in parameters.items():
        if key in ["module", "currentLocationId", "currentLocation", "currentAreaId", "currentArea"]:
            current_party_data["worldConditions"][key] = value
        elif key == "module":
            current_party_data["module"] = value
    
    # Save updated party tracker
    safe_json_dump(current_party_data, "party_tracker.json")
    
    return create_return(status="success", needs_update=True)
```

### **Step 3: Update System Prompt for Module Travel Recognition**
**File**: `/mnt/c/dungeon_master_v1/system_prompt.txt`

**Add section after existing location transition guidelines**:
```
## Inter-Module Travel Guidelines

When players request travel to other modules/regions using natural language:

### RECOGNIZE MODULE TRAVEL REQUESTS:
- "I travel to [Module Name]"
- "Let's go to [Region Name]" 
- "I want to visit [Module Name]"
- "Take us to [Module Name]"

### MODULE TRAVEL RESPONSE FORMAT:
Use updatePartyTracker action with module change:

```json
{
  "narration": "[Travel narration] + [Arrival description]",
  "actions": [
    {
      "action": "updatePartyTracker",
      "parameters": {
        "module": "Target_Module_Name",
        "currentLocationId": "A01",
        "currentLocation": "Starting Location Name",
        "currentAreaId": "AREA001", 
        "currentArea": "Starting Area Name"
      }
    },
    {
      "action": "updateTime",
      "parameters": {
        "timeEstimate": 240
      }
    }
  ]
}
```

### MODULE TRAVEL NARRATION:
1. **Travel Description**: Use AI-generated travel narration from world registry
2. **Journey Details**: Describe the path, time taken, terrain changes
3. **Arrival Scene**: Detailed description of arriving at the new module's starting location
4. **Atmospheric Setting**: Set mood and tone for the new adventure

### DEFAULT STARTING LOCATIONS:
If no specific location requested:
- Towns/Villages: Inn or tavern (A01, A02)
- Wilderness: Trail entrance or camp (A01)
- Dungeons: Surface entrance (A01)
- Use world registry data to determine appropriate starting point
```

### **Step 4: Add Module Helper Functions**
**File**: `/mnt/c/dungeon_master_v1/action_handler.py`

**Add utility functions**:
```python
def get_module_starting_location(module_name: str) -> tuple:
    """Get the default starting location for a module"""
    try:
        path_manager = ModulePathManager(module_name)
        area_ids = path_manager.get_area_ids()
        
        if not area_ids:
            return ("A01", "Unknown Location", "AREA001", "Unknown Area")
        
        # Get first area file
        first_area_id = area_ids[0]
        area_file = path_manager.get_area_path(first_area_id)
        area_data = safe_json_load(area_file)
        
        if area_data and "locations" in area_data:
            locations = area_data["locations"]
            if isinstance(locations, list) and locations:
                first_location = locations[0]
                return (
                    first_location.get("locationId", "A01"),
                    first_location.get("name", "Unknown Location"),
                    first_area_id,
                    area_data.get("areaName", "Unknown Area")
                )
        
        return ("A01", "Unknown Location", first_area_id, "Unknown Area")
        
    except Exception as e:
        print(f"Warning: Could not get starting location for {module_name}: {e}")
        return ("A01", "Unknown Location", "AREA001", "Unknown Area")

def get_travel_narration(target_module: str) -> str:
    """Get AI-generated travel narration for module transition"""
    try:
        world_registry = safe_json_load("modules/world_registry.json")
        if world_registry and "modules" in world_registry:
            module_data = world_registry["modules"].get(target_module, {})
            travel_data = module_data.get("travelNarration", {})
            return travel_data.get("travelNarration", 
                f"The party travels to the {target_module} region, where new adventures await.")
    except:
        return f"The party travels to the {target_module} region, where new adventures await."
```

### **Step 5: Update Action Constants**
**File**: `/mnt/c/dungeon_master_v1/action_handler.py`

**Add new action constant**:
```python
ACTION_UPDATE_PARTY_TRACKER = "updatePartyTracker"
```

### **Step 6: Add to Validation Prompt**
**File**: `/mnt/c/dungeon_master_v1/validation_prompt.txt`

**Add validation rules**:
```
"updatePartyTracker": Used when party module or location information needs updating. This action can trigger automatic conversation archiving and module summarization when module changes are detected. Required for inter-module travel. Requires parameters for the specific updates (module, currentLocationId, currentLocation, etc.).
```

### **Step 7: Test Implementation**
1. **Test Module Travel**: Try "I travel to [ModuleName]" commands
2. **Verify Auto-Archiving**: Check that conversation_archives are created
3. **Verify Summaries**: Check that module summaries are generated
4. **Test Return Travel**: Try returning to previous modules
5. **Verify Travel Narration**: Ensure AI uses generated travel descriptions

### **Step 8: Documentation Update**
**File**: `/mnt/c/dungeon_master_v1/README.md`

**Add inter-module travel section**:
```markdown
### 🌍 Inter-Module Travel System

The game supports seamless travel between adventure modules using natural language:

#### **Travel Commands**
- "I travel to [Module Name]"
- "Let's go to [Region Name]"
- "Take us to [Module Name]"

#### **Automatic Features**
- **Conversation Archiving**: Previous module conversations automatically archived
- **Module Summaries**: AI generates chronicle summaries when leaving modules
- **Travel Narration**: Rich, atmospheric descriptions of journeys between regions
- **Return Visits**: Accumulated history preserved for multiple visits to same modules

#### **Example Usage**
```
Player: "I want to travel to the Crystal Peaks"
AI: *Archives current conversation and generates summary*
AI: "The party travels through winding mountain passes..."
AI: *Arrives at Crystal Peaks starting location with full context*
```
```

## 🔄 **Existing Architecture Leveraged**

### **✅ Already Implemented Systems**
1. **Module Stitcher**: AI travel narration generation
2. **Campaign Manager**: Cross-module transition detection and auto-archiving
3. **Conversation Archiving**: Full conversation history preservation
4. **Module Summaries**: AI-generated chronicle summaries
5. **World Registry**: Module tracking and metadata
6. **Sequential Storage**: Numbered archives for multiple visits

### **✅ Integration Points**
- `detect_module_transition()` - Module boundary detection
- `handle_cross_module_transition()` - Auto-archiving and summarization
- `_archive_conversation_history()` - Conversation preservation
- `_generate_module_summary()` - AI chronicle generation
- Module stitcher travel narration data

## 📊 **Expected Outcomes**

### **Player Experience**
- **Natural Commands**: "I travel to [Module]" works seamlessly
- **Rich Narration**: AI-generated atmospheric travel descriptions
- **Preserved History**: Return visits include full accumulated context
- **Seamless Transitions**: No jarring system messages or complex UIs

### **Technical Benefits**
- **Zero New Actions**: Uses existing updatePartyTracker
- **Leverages 95% Existing Code**: Minimal new implementation needed
- **Automatic Archiving**: Previous adventures preserved automatically
- **Module Agnostic**: Works with any module structure

### **DM Benefits**
- **Automatic Management**: Conversation and summary handling automated
- **Rich Context**: AI maintains continuity across modules
- **Simple Commands**: Natural language travel requests
- **Preserved Memory**: Complete adventure history maintained

## 🎯 **Success Criteria**

1. ✅ Player can say "I travel to [Module]" and arrive at correct starting location
2. ✅ Previous module conversation automatically archived
3. ✅ Module summary automatically generated when leaving
4. ✅ Travel narration uses AI-generated atmospheric descriptions
5. ✅ Return visits to modules include accumulated history
6. ✅ System works with any existing or future modules
7. ✅ No new actions required - uses existing updatePartyTracker

## 🚨 **Risk Mitigation**

### **Potential Issues**
- Module name recognition by AI
- Starting location detection failures
- Archive/summary generation errors

### **Safeguards**
- Fallback to default locations (A01)
- Error handling for missing modules
- Graceful degradation if archiving fails
- Clear debug logging for troubleshooting

## 📝 **Implementation Notes**

- **Priority**: High - Core gameplay feature
- **Complexity**: Low - Leverages existing architecture
- **Risk**: Low - Minimal code changes required
- **Testing**: Medium - Multiple module scenarios needed

This plan implements sophisticated inter-module travel using 95% existing code, providing a seamless player experience with automatic conversation management and rich AI-generated narration.