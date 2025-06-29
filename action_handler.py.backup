# ============================================================================
# ACTION_HANDLER.PY - COMMAND PATTERN IMPLEMENTATION
# ============================================================================
# 
# ARCHITECTURE ROLE: Action Processing Layer in Command Pattern
# 
# This module implements the Command Pattern for the 5e system, encapsulating
# all game interactions as discrete, typed actions with specific parameters.
# It serves as the central dispatcher for all game state modifications.
# 
# KEY RESPONSIBILITIES:
# - Parse and validate action commands from AI responses
# - Route actions to appropriate subsystem handlers
# - Module transition detection and marker insertion
# - Ensure atomic execution of compound operations
# - Maintain consistency across all game state updates
# - Provide standardized error handling for all actions
# 
# SUPPORTED ACTION TYPES:
# - updateCharacterInfo: Character stat and inventory management
# - transitionLocation: Movement and exploration actions
# - createEncounter: Combat encounter initialization
# - updatePlot: Module narrative progression
# - updateWorldTime: Game time advancement
# - And extensible action framework for future features
# 
# ARCHITECTURAL INTEGRATION:
# - Called by main.py as part of AI response processing
# - Coordinates with various managers (combat, location, character)
# - Uses ModulePathManager for file operations
# - Implements our "Data Integrity Above All" principle
# 
# DESIGN PATTERNS:
# - Command Pattern: Actions as first-class objects
# - Strategy Pattern: Different handlers for different action types
# - Template Method: Consistent action processing pipeline
# ============================================================================

import json
import subprocess
import os
from datetime import datetime
from openai import OpenAI
import config
from location_manager import get_location_data
from module_path_manager import ModulePathManager
from plot_update import update_plot
from encoding_utils import sanitize_text, safe_json_dump, safe_json_load
from status_manager import (
    status_transitioning_location, status_updating_character, status_updating_party,
    status_updating_plot, status_advancing_time, status_processing_levelup
)
from location_path_finder import LocationGraph

# Action type constants
ACTION_CREATE_ENCOUNTER = "createEncounter"
ACTION_UPDATE_ENCOUNTER = "updateEncounter"
ACTION_UPDATE_TIME = "updateTime"
ACTION_UPDATE_PLOT = "updatePlot"
ACTION_EXIT_GAME = "exitGame"
ACTION_TRANSITION_LOCATION = "transitionLocation"
ACTION_LEVEL_UP = "levelUp"
ACTION_UPDATE_CHARACTER_INFO = "updateCharacterInfo"
ACTION_UPDATE_PARTY_NPCS = "updatePartyNPCs"
ACTION_CREATE_NEW_MODULE = "createNewModule"
ACTION_ESTABLISH_HUB = "establishHub"
ACTION_STORAGE_INTERACTION = "storageInteraction"
ACTION_UPDATE_PARTY_TRACKER = "updatePartyTracker"
ACTION_MOVE_BACKGROUND_NPC = "moveBackgroundNPC"
ACTION_SAVE_GAME = "saveGame"
ACTION_RESTORE_GAME = "restoreGame"
ACTION_LIST_SAVES = "listSaves"
ACTION_DELETE_SAVE = "deleteSave"

# Module conversation segmentation has been moved to conversation_utils.py
# to work with the regular conversation update cycle

def validate_location_transition(location_graph, current_location_id, destination_location_id):
    """
    Validate that a location transition is possible using the location graph.
    
    Args:
        location_graph (LocationGraph): Initialized location graph
        current_location_id (str): Current location ID (e.g., "E02")
        destination_location_id (str): Destination location ID (e.g., "B01")
    
    Returns:
        tuple: (bool, str, str) - (is_valid, error_message, area_connectivity_id)
    """
    try:
        # Validate destination location exists
        if not location_graph.validate_location_id_format(destination_location_id):
            return False, f"Destination location '{destination_location_id}' does not exist in module", None
        
        # Use pathfinding to validate that a connected path exists
        success, path, path_message = location_graph.find_path(current_location_id, destination_location_id)
        if not success:
            return False, f"No valid path exists between '{current_location_id}' and '{destination_location_id}': {path_message}", None
        
        # Check if this is a cross-area transition
        is_cross_area = location_graph.is_cross_area_transition(current_location_id, destination_location_id)
        if is_cross_area is None:
            return False, f"Invalid location ID format: current='{current_location_id}', destination='{destination_location_id}'", None
        
        # Generate area connectivity ID if needed (for backward compatibility with location_manager)
        area_connectivity_id = None
        if is_cross_area:
            dest_area_id = location_graph.get_area_id_from_location_id(destination_location_id)
            area_connectivity_id = f"{dest_area_id}-{destination_location_id}"
        
        print(f"DEBUG: Location transition validation passed")
        print(f"DEBUG: Path found: {' -> '.join(path) if path else 'Direct connection'}")
        print(f"DEBUG: Cross-area transition: {is_cross_area}")
        if area_connectivity_id:
            print(f"DEBUG: Generated area connectivity ID: {area_connectivity_id}")
        
        return True, "", area_connectivity_id
        
    except Exception as e:
        return False, f"Location validation failed with exception: {str(e)}", None

def update_party_npcs(party_tracker_data, operation, npc):
    """Update NPC party members (add or remove)"""
    if operation == "add":
        # Get the correct module from party tracker
        module_name = party_tracker_data.get("module", "").replace(" ", "_")
        path_manager = ModulePathManager(module_name)
        npc_file = path_manager.get_character_path(npc['name'])
        if not os.path.exists(npc_file):
            # NPC file doesn't exist, so we need to create it
            try:
                # Get party level as default if no level specified
                default_level = ''
                if not npc.get('level'):
                    # Get the first party member's level as default
                    if party_tracker_data.get("partyMembers"):
                        player_name = party_tracker_data["partyMembers"][0]
                        player_file = path_manager.get_character_path(player_name)
                        if os.path.exists(player_file):
                            try:
                                from encoding_utils import safe_json_load
                                player_data = safe_json_load(player_file)
                                if player_data and 'level' in player_data:
                                    default_level = str(player_data['level'])
                                    print(f"DEBUG: Using party level {default_level} as default for NPC {npc['name']}")
                            except Exception as e:
                                print(f"DEBUG: Could not get party level, using default: {e}")
                
                npc_level = str(npc.get('level', default_level))
                
                # Add this debug line right before the subprocess.run call
                print(f"DEBUG: Calling npc_builder.py with arguments: {npc['name']} {npc.get('race', '')} {npc.get('class', '')} {npc_level} {npc.get('background', '')}")

                subprocess.run([
                    "python", "npc_builder.py",
                    npc['name'],
                    npc.get('race', ''),
                    npc.get('class', ''),
                    npc_level,
                    npc.get('background', '')
                ], check=True)
                print(f"DEBUG: NPC profile created for {npc['name']}")
            except subprocess.CalledProcessError as e:
                print(f"ERROR: Failed to create NPC profile for {npc['name']}: {e}")
                return

        # Now we can add the NPC to the party
        party_tracker_data["partyNPCs"].append(npc)
    elif operation == "remove":
        party_tracker_data["partyNPCs"] = [x for x in party_tracker_data["partyNPCs"] if x["name"] != npc["name"]]

    safe_json_dump(party_tracker_data, "party_tracker.json")
    print(f"DEBUG: Party NPCs updated - {operation} {npc['name']}")

def run_combat_simulation(encounter_id, party_tracker_data, location_data):
    """Run the combat simulation"""
    # Import here to avoid circular imports
    from combat_manager import run_combat_simulation as run_combat
    return run_combat(encounter_id, party_tracker_data, location_data)

def get_module_starting_location(module_name: str) -> tuple:
    """Get the starting location for a module using AI analysis with caching"""
    try:
        # Check world registry for cached starting location
        world_registry_path = "modules/world_registry.json"
        world_registry = safe_json_load(world_registry_path)
        
        if world_registry and 'modules' in world_registry:
            module_data = world_registry['modules'].get(module_name, {})
            cached_start = module_data.get('startingLocation')
            
            if cached_start:
                print(f"DEBUG: Using cached starting location for {module_name}")
                return (
                    cached_start.get('locationId', 'A01'),
                    cached_start.get('locationName', 'Unknown Location'),
                    cached_start.get('areaId', 'AREA001'),
                    cached_start.get('areaName', 'Unknown Area')
                )
        
        # No cached result, use AI to analyze module
        print(f"DEBUG: No cached starting location found, analyzing {module_name} with AI")
        
        path_manager = ModulePathManager(module_name)
        area_ids = path_manager.get_area_ids()
        
        if not area_ids:
            return ("A01", "Unknown Location", "AREA001", "Unknown Area")
        
        # Gather all module data for AI analysis
        module_analysis_data = {
            "moduleName": module_name,
            "areas": {},
            "plotData": None
        }
        
        # Load all area files
        for area_id in area_ids:
            try:
                area_file = path_manager.get_area_path(area_id)
                area_data = safe_json_load(area_file)
                if area_data:
                    # Include key information for AI analysis
                    module_analysis_data["areas"][area_id] = {
                        "areaName": area_data.get("areaName", ""),
                        "areaType": area_data.get("areaType", ""),
                        "areaDescription": area_data.get("areaDescription", ""),
                        "recommendedLevel": area_data.get("recommendedLevel", 1),
                        "dangerLevel": area_data.get("dangerLevel", "unknown"),
                        "locations": area_data.get("locations", [])[:3]  # First 3 locations for analysis
                    }
            except Exception as e:
                print(f"Warning: Could not load area {area_id}: {e}")
                continue
        
        # Load plot data
        try:
            plot_file = path_manager.get_plot_path()
            plot_data = safe_json_load(plot_file)
            if plot_data:
                # Include key plot information
                module_analysis_data["plotData"] = {
                    "mainObjective": plot_data.get("mainObjective", ""),
                    "plotPoints": plot_data.get("plotPoints", [])[:3]  # First 3 plot points
                }
        except Exception as e:
            print(f"Warning: Could not load plot data: {e}")
        
        # Use AI to determine starting location
        starting_location = _ai_analyze_starting_location(module_analysis_data)
        
        # Cache the result in world registry
        if starting_location and world_registry:
            if module_name not in world_registry['modules']:
                world_registry['modules'][module_name] = {}
            
            world_registry['modules'][module_name]['startingLocation'] = {
                'locationId': starting_location[0],
                'locationName': starting_location[1], 
                'areaId': starting_location[2],
                'areaName': starting_location[3],
                'determinedBy': 'AI',
                'timestamp': datetime.now().isoformat()
            }
            
            safe_json_dump(world_registry, world_registry_path)
            print(f"DEBUG: Cached AI-determined starting location for {module_name}")
        
        return starting_location
        
    except Exception as e:
        print(f"Warning: Could not get starting location for {module_name}: {e}")
        return ("A01", "Unknown Location", "AREA001", "Unknown Area")

def _ai_analyze_starting_location(module_data: dict) -> tuple:
    """Use AI to analyze module data and determine the best starting location"""
    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        system_prompt = """You are an expert D&D adventure module analyst. Analyze the provided module data to determine the most logical starting location for player characters entering this adventure module.

ANALYSIS CRITERIA:
1. **Adventure Flow**: Look at plot points (PP001 usually indicates starting area)
2. **Area Types**: Towns/settlements are typical starting points, dungeons/ruins typically aren't
3. **NPCs**: Areas with guides, quest-givers, or friendly NPCs often indicate starting locations
4. **Danger Level**: Lower danger areas are more suitable for arrivals
5. **Logical Narrative**: Where would adventurers most likely arrive or be directed to begin?

RETURN FORMAT:
Respond with ONLY a JSON object in this exact format:
{
  "locationId": "R01",
  "locationName": "Specific Location Name", 
  "areaId": "SR001",
  "areaName": "Area Name",
  "reasoning": "Brief explanation of why this is the starting location"
}

Use the EXACT locationId and areaId from the provided data. Do not create new IDs."""

        user_prompt = f"""Analyze this D&D adventure module to determine the starting location:

MODULE DATA:
{json.dumps(module_data, indent=2)}

Determine the most logical starting location based on adventure flow, area types, NPCs, and narrative logic."""

        response = client.chat.completions.create(
            model=config.DM_MINI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"DEBUG: AI starting location analysis response: {ai_response}")
        
        # Parse AI response - handle markdown code blocks
        json_content = ai_response
        if ai_response.startswith('```json'):
            # Extract JSON from markdown code block
            lines = ai_response.split('\n')
            json_lines = []
            in_json_block = False
            for line in lines:
                if line.strip() == '```json':
                    in_json_block = True
                    continue
                elif line.strip() == '```' and in_json_block:
                    break
                elif in_json_block:
                    json_lines.append(line)
            json_content = '\n'.join(json_lines)
            print(f"DEBUG: Extracted JSON from code block: {json_content}")
        
        try:
            result = json.loads(json_content)
            
            # Validate required fields
            required_fields = ['locationId', 'locationName', 'areaId', 'areaName']
            if all(field in result for field in required_fields):
                print(f"DEBUG: AI determined starting location: {result['areaId']}/{result['locationId']} - {result['locationName']}")
                print(f"DEBUG: AI reasoning: {result.get('reasoning', 'No reasoning provided')}")
                
                return (
                    result['locationId'],
                    result['locationName'],
                    result['areaId'], 
                    result['areaName']
                )
            else:
                print(f"ERROR: AI response missing required fields: {result}")
                
        except json.JSONDecodeError as e:
            print(f"ERROR: Could not parse AI response as JSON: {e}")
            print(f"AI response was: {ai_response}")
        
        # Fallback to first area/location if AI analysis fails
        print("WARNING: AI analysis failed, falling back to first available location")
        return _get_fallback_starting_location(module_data)
        
    except Exception as e:
        print(f"ERROR: AI starting location analysis failed: {e}")
        return _get_fallback_starting_location(module_data)

def _get_fallback_starting_location(module_data: dict) -> tuple:
    """Fallback method to get first available location if AI analysis fails"""
    try:
        areas = module_data.get('areas', {})
        if areas:
            # Get first area
            first_area_id = next(iter(areas.keys()))
            first_area = areas[first_area_id]
            
            locations = first_area.get('locations', [])
            if locations:
                first_location = locations[0]
                return (
                    first_location.get('locationId', 'A01'),
                    first_location.get('name', 'Unknown Location'),
                    first_area_id,
                    first_area.get('areaName', 'Unknown Area')
                )
        
        return ("A01", "Unknown Location", "AREA001", "Unknown Area")
        
    except Exception as e:
        print(f"WARNING: Fallback location detection failed: {e}")
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

def process_action(action, party_tracker_data, location_data, conversation_history):
    """Process an action based on its type
    
    Returns:
        dict: {
            "status": "continue" | "exit" | "needs_response",
            "needs_update": bool,
            "response_data": dict (optional) - data for generating new AI response
        }
    """
    # Import modules here to avoid circular imports
    import location_manager
    from update_world_time import update_world_time
    from plot_update import update_plot
    from update_character_info import update_character_info

    # Helper function to create consistent return values
    def create_return(status="continue", needs_update=False, response_data=None):
        result = {"status": status, "needs_update": needs_update}
        if response_data:
            result["response_data"] = response_data
        return result

    global needs_conversation_history_update
    needs_conversation_history_update = False
    
    action_type = action.get("action")
    parameters = action.get("parameters", {})

    if action_type == ACTION_CREATE_ENCOUNTER:
        print("DEBUG: Creating combat encounter")
        try:
            print(f"DEBUG: Sending to combat_builder.py: {json.dumps(action)}")
            result = subprocess.run(
                ["python", "combat_builder.py"],
                input=json.dumps(action),
                check=True, capture_output=True, text=True
            )
            print("DEBUG: combat_builder.py output:", result.stdout)
            print("DEBUG: combat_builder.py status:", result.stderr)
            print("DEBUG: Combat encounter created successfully")

            if "Encounter successfully built and saved to encounter_" in result.stdout:
                encounter_id = result.stdout.strip().split()[-1].replace(".json", "")

                party_tracker_data["worldConditions"]["activeCombatEncounter"] = encounter_id
                safe_json_dump(party_tracker_data, "party_tracker.json")
                print(f"DEBUG: Updated party tracker with combat encounter ID: {encounter_id}")

                # Reload location data here
                current_location_id = party_tracker_data["worldConditions"]["currentLocationId"]
                current_area_id = party_tracker_data["worldConditions"]["currentAreaId"]
                # Use the reloaded location data for the combat simulation
                reloaded_location_data = get_location_data(current_location_id, current_area_id)


                if reloaded_location_data is None:
                    print(f"ERROR: Failed to load location data for {current_location_id}")
                    return # Or handle error appropriately

                dialogue_summary, updated_player_info = run_combat_simulation(encounter_id, party_tracker_data, reloaded_location_data)


                player_name = next((member for member in party_tracker_data["partyMembers"]), None)
                if player_name and updated_player_info is not None:
                    # Get the correct module from party tracker
                    module_name = party_tracker_data.get("module", "").replace(" ", "_")
                    path_manager = ModulePathManager(module_name)
                    player_file = path_manager.get_character_path(player_name)
                    safe_json_dump(updated_player_info, player_file)
                    print(f"DEBUG: Updated player file for {player_name}")
                else:
                    print("WARNING: Combat simulation did not return valid player info. Player file not updated.")

                # Copy combat summary to main conversation history
                combat_history = safe_json_load("combat_conversation_history.json")
                combat_summary = next((entry for entry in reversed(combat_history) if entry["role"] == "assistant" and "Combat Summary:" in entry["content"]), None)

                if combat_summary:
                    modified_combat_summary = {
                        "role": "user",
                        "content": combat_summary["content"]
                    }
                    conversation_history.append(modified_combat_summary)
                    # Import save_conversation_history from main
                    from main import save_conversation_history
                    save_conversation_history(conversation_history)
                    return create_return(status="needs_response", needs_update=True)
                else:
                    print("ERROR: Combat summary not found in combat conversation history")

        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running combat_builder.py: {e}")
            print("Error output:", e.stderr)
            print("Standard output:", e.stdout)
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()

    elif action_type == ACTION_UPDATE_TIME:
        status_advancing_time()
        time_estimate_str = str(parameters["timeEstimate"])
        update_world_time(time_estimate_str)

    elif action_type == ACTION_UPDATE_PLOT:
        status_updating_plot()
        plot_point_id = parameters["plotPointId"]
        new_status = parameters["newStatus"]
        plot_impact = parameters.get("plotImpact", "")
        plot_filename = "module_plot.json"  # Now using unified plot file
        updated_plot = update_plot(plot_point_id, new_status, plot_impact, plot_filename)

    elif action_type == ACTION_EXIT_GAME:
        conversation_history.append({"role": "user", "content": "Dungeon Master Note: Resume the game, the player has returned."})
        from main import save_conversation_history, exit_game
        save_conversation_history(conversation_history)
        exit_game()
        return create_return(status="exit")

    elif action_type == ACTION_TRANSITION_LOCATION:
        status_transitioning_location()
        new_location_name_or_id = parameters["newLocation"] # This should be a location ID now
        
        # Sanitize location names to prevent encoding issues
        current_location_name = sanitize_text(party_tracker_data["worldConditions"]["currentLocation"])
        current_location_id = party_tracker_data["worldConditions"]["currentLocationId"]
        current_area_name = party_tracker_data["worldConditions"]["currentArea"]
        current_area_id = party_tracker_data["worldConditions"]["currentAreaId"]
        
        # Initialize location graph for validation
        location_graph = LocationGraph()
        location_graph.load_module_data()
        
        # MAP: Convert area ID to entry location ID if needed (TW001 -> TW01)
        if not location_graph.validate_location_id_format(new_location_name_or_id):
            # Try to find entry location for this area ID
            entry_location = location_graph.get_entry_location_for_area(new_location_name_or_id)
            if entry_location:
                print(f"DEBUG: Mapped area ID '{new_location_name_or_id}' to entry location '{entry_location}'")
                new_location_name_or_id = entry_location
        
        # VALIDATE: Check if location transition is valid
        is_valid, error_message, auto_area_connectivity_id = validate_location_transition(
            location_graph, current_location_id, new_location_name_or_id
        )
        
        if not is_valid:
            print(f"ERROR: {error_message}")
            return create_return(
                status="error", 
                needs_update=False,
                response_data={"error_message": f"Path Validation: {error_message}"}
            )
        
        # Debug the exact string values for easier troubleshooting
        print(f"DEBUG: Transitioning from '{current_location_name}' to '{new_location_name_or_id}'")
        print(f"DEBUG: Current location string (hex): {current_location_name.encode('utf-8').hex()}")
        print(f"DEBUG: New location string (hex): {new_location_name_or_id.encode('utf-8').hex()}")
        
        # Use enhanced location manager with auto-generated area connectivity ID
        transition_prompt = location_manager.handle_location_transition(
            current_location_name, 
            new_location_name_or_id, 
            current_area_name, 
            current_area_id, 
            auto_area_connectivity_id
        )

        if transition_prompt:
            # Get the new location ID from party tracker after transition
            # The location manager updates party_tracker.json before we get here
            try:
                updated_party_tracker = safe_json_load("party_tracker.json")
                new_location_name = updated_party_tracker["worldConditions"]["currentLocation"]
                new_location_id = updated_party_tracker["worldConditions"]["currentLocationId"]
                # Include location IDs in the transition message for reliable matching
                conversation_history.append({"role": "user", "content": f"Location transition: {sanitize_text(current_location_name)} ({current_location_id}) to {sanitize_text(new_location_name)} ({new_location_id})"})
            except Exception as e:
                print(f"DEBUG: Could not get updated location IDs: {str(e)}")
                # Fallback to original format if we can't get the IDs
                conversation_history.append({"role": "user", "content": f"Location transition: {sanitize_text(current_location_name)} to {sanitize_text(new_location_name_or_id)}"})
            
            # Save conversation history immediately after adding transition
            from main import save_conversation_history
            save_conversation_history(conversation_history)
            
            # Check for any missing summaries after the transition
            import cumulative_summary
            conversation_history = cumulative_summary.check_and_compact_missing_summaries(
                conversation_history, 
                party_tracker_data
            )
            save_conversation_history(conversation_history)
            
            # CAMPAIGN INTEGRATION: Check for cross-module transitions
            try:
                from campaign_manager import CampaignManager
                campaign_manager = CampaignManager()
                
                # Detect if this is a cross-module transition
                is_cross_module, from_module, to_module = campaign_manager.detect_module_transition(
                    current_location_id, new_location_id
                )
                
                if is_cross_module:
                    print(f"DEBUG: Cross-module transition detected: {from_module} -> {to_module}")
                    
                    # Handle conversation segmentation - summarize current module and add transition marker
                    conversation_history = handle_module_conversation_segmentation(
                        conversation_history, from_module, to_module
                    )
                    save_conversation_history(conversation_history)
                    print(f"DEBUG: Module conversation segmentation complete")
                    
                    # Auto-summarize the module being left and update campaign state
                    summary = campaign_manager.handle_cross_module_transition(
                        from_module, to_module, updated_party_tracker, conversation_history
                    )
                    
                    # Update party tracker module field
                    updated_party_tracker["module"] = to_module
                    safe_json_dump(updated_party_tracker, "party_tracker.json")
                    
                    # Inject accumulated campaign context
                    print(f"DEBUG: Requesting campaign context for module: {to_module}")
                    campaign_context = campaign_manager.get_accumulated_summaries_context(to_module)
                    print(f"DEBUG: Campaign context received - Length: {len(campaign_context) if campaign_context else 0} characters")
                    if campaign_context:
                        conversation_history.append({
                            "role": "system", 
                            "content": f"=== CAMPAIGN CONTEXT ===\n{campaign_context}"
                        })
                        save_conversation_history(conversation_history)
                        print(f"DEBUG: Campaign context injected for {to_module}")
                    else:
                        print(f"DEBUG: No campaign context to inject for {to_module} - context was empty")
                else:
                    print(f"DEBUG: Within-module transition: {current_location_id} -> {new_location_id}")
                    
            except Exception as e:
                print(f"Warning: Campaign transition check failed: {e}")
                # Don't let campaign system errors break location transitions
            
            print("DEBUG: Location transition complete")
            needs_conversation_history_update = True  # Trigger conversation history reload
             # After transition, the current_location_data in the main loop might be stale.
            # We need to ensure the AI response processing uses the *new* location data.
            # This might require process_ai_response to reload location data or for main_game_loop to handle it.
            # For now, let's assume the main loop will reload it before the next AI call.
        else:
            print("ERROR: Failed to handle location transition")
            # Create error message for the AI DM
            error_message = f"""SYSTEM ERROR: Location Transition Failed

The attempted transition to '{new_location_name_or_id}' failed because this location does not exist or is not connected from the current location '{current_location_name}'.

Please use a valid location that exists in the current area ({current_area_id}) and is connected to the current location. Check the map data and connectivity information to ensure valid transitions."""
            
            # Append error to conversation history
            conversation_history.append({"role": "user", "content": error_message})
            
            # Import necessary functions from main
            from main import save_conversation_history
            save_conversation_history(conversation_history)
            
            # Return signal to get new AI response
            return create_return(status="needs_response", needs_update=True)

    elif action_type == ACTION_LEVEL_UP:
        entity_name = parameters.get("entityName")
        new_level = parameters.get("newLevel")

        with open("leveling_info.txt", "r", encoding="utf-8") as file:
            leveling_info = file.read()

        dm_note = f"Leveling Dungeon Master Guidance: Proceed with leveling up the player character or the party NPC given the 5th Edition role playing game rules. Only level the player or the party NPC one level at a time to ensure no mistakes are made. Use the 'updateCharacterInfo' action for both player characters and NPCs. Include the character name and all changes. If you are leveling up a player character, you must ask the player for important decisions and choices they would have control over. After the player has provided the needed information then use the 'updateCharacterInfo' to pass all changes to the character sheet and include the experience goal for the next level. Do not update the character's information in segments. \n\n{leveling_info}"
        conversation_history.append({"role": "user", "content": dm_note})
        return create_return(status="needs_response", needs_update=True)

    elif action_type == ACTION_UPDATE_CHARACTER_INFO:
        status_updating_character()
        print(f"DEBUG: Processing updateCharacterInfo action")
        changes = parameters.get("changes")
        
        # Validate changes parameter
        if not changes or not isinstance(changes, (str, dict)):
            print(f"ERROR: Invalid changes parameter: {changes} (type: {type(changes)})")
            return create_return(status="continue", needs_update=False)
        
        # Convert dict to string if needed
        if isinstance(changes, dict):
            changes = json.dumps(changes)
        
        character_name = parameters.get("characterName")
        
        # Backward compatibility: if no characterName provided, try legacy parameters
        if not character_name:
            # Try npcName first (for NPC updates)
            character_name = parameters.get("npcName")
            if not character_name:
                # Fall back to player name from party tracker
                character_name = next((member.lower() for member in party_tracker_data["partyMembers"]), None)
        
        if character_name:
            print(f"DEBUG: Updating character info for {character_name}")
            try:
                success = update_character_info(character_name, changes)
                if success:
                    print(f"DEBUG: Character info updated successfully")
                    needs_conversation_history_update = True
                else:
                    print(f"ERROR: Failed to update character info for {character_name}")
            except Exception as e:
                print(f"ERROR: Failed to update character info: {str(e)}")
        else:
            print("ERROR: No character name provided and no player found in party tracker.")


    elif action_type == ACTION_UPDATE_PARTY_NPCS:
        operation = parameters["operation"]
        npc = parameters["npc"]
        update_party_npcs(party_tracker_data, operation, npc)

    elif action_type == ACTION_UPDATE_ENCOUNTER:
        print(f"DEBUG: Processing updateEncounter action")
        encounter_id = parameters.get("encounterId")
        changes = parameters.get("changes")
        
        if encounter_id and changes:
            try:
                # Import the update_encounter function
                from update_encounter import update_encounter
                
                # Update the encounter
                updated_encounter = update_encounter(encounter_id, changes)
                
                if updated_encounter:
                    print(f"DEBUG: Encounter {encounter_id} updated successfully")
                    needs_conversation_history_update = True
                else:
                    print(f"ERROR: Failed to update encounter {encounter_id}")
            except Exception as e:
                print(f"ERROR: Exception while updating encounter: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print(f"ERROR: Missing required parameters for updateEncounter. encounterId: {encounter_id}, changes: {changes}")

    elif action_type == ACTION_CREATE_NEW_MODULE:
        print(f"DEBUG: Processing createNewModule action")
        try:
            # Pass ALL parameters directly from AI to module builder
            # The AI is fully in control of module creation
            from module_builder import ai_driven_module_creation
            
            # Check if this is a single narrative parameter (new format)
            # or multiple parameters (old format)
            if len(parameters) == 1 and isinstance(list(parameters.values())[0], str):
                # Single narrative parameter - new format
                narrative = list(parameters.values())[0]
                parameters = {"narrative": narrative}
            
            # Let the module builder handle ALL parameter validation
            # This makes the system fully agentic - AI decides everything
            success, module_name = ai_driven_module_creation(parameters)
            
            if success:
                # Module name is now returned from the AI parser
                print(f"DEBUG: Module '{module_name}' created successfully")
                
                # Auto-integrate with module stitcher
                try:
                    from module_stitcher import ModuleStitcher
                    stitcher = ModuleStitcher()
                    # Run stitcher in fully autonomous mode
                    integrated_modules = stitcher.scan_and_integrate_new_modules()
                    print(f"DEBUG: Module '{module_name}' integrated into world registry")
                    print(f"DEBUG: Integration summary: {integrated_modules}")
                except Exception as e:
                    print(f"WARNING: Module created but stitching failed: {e}")
                
                # Reset processing status to ready
                try:
                    from status_manager import status_ready
                    status_ready()
                    print("DEBUG: Status reset to ready")
                except Exception as e:
                    print(f"DEBUG: Error resetting status: {e}")
                
                # Signal module creation complete
                dm_note = f"Dungeon Master Note: New module '{module_name}' has been successfully created and integrated into the world. You may now guide the party to this new adventure."
                conversation_history.append({"role": "user", "content": dm_note})
                
                # Save conversation history
                from main import save_conversation_history
                save_conversation_history(conversation_history)
                
                needs_conversation_history_update = True
            else:
                print(f"ERROR: Failed to create module")
                
                # Reset status even on failure  
                try:
                    from status_manager import status_ready
                    status_ready()
                    print("DEBUG: Status reset after failure")
                except Exception as e:
                    print(f"DEBUG: Error resetting status after failure: {e}")
                
        except Exception as e:
            print(f"ERROR: Exception while creating module: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Reset status on exception
            try:
                from status_manager import status_ready  
                status_ready()
                print("DEBUG: Status reset after exception")
            except Exception as status_e:
                print(f"DEBUG: Error resetting status after exception: {status_e}")

    elif action_type == ACTION_ESTABLISH_HUB:
        print(f"DEBUG: Processing establishHub action")
        try:
            # Extract hub parameters
            hub_name = parameters.get('hubName')
            hub_type = parameters.get('hubType', 'settlement')
            description = parameters.get('description', '')
            services = parameters.get('services', [])
            ownership = parameters.get('ownership', 'party')
            
            if hub_name:
                # Import campaign manager
                from campaign_manager import CampaignManager
                campaign_manager = CampaignManager()
                
                # Establish the hub
                hub_data = {
                    "hubType": hub_type,
                    "description": description, 
                    "services": services,
                    "ownership": ownership
                }
                
                campaign_manager.establish_hub(hub_name, hub_data)
                
                print(f"DEBUG: Hub '{hub_name}' established successfully")
                
                # Add DM note about hub establishment
                dm_note = f"Dungeon Master Note: '{hub_name}' has been established as a hub location. The party can now return here from other adventures."
                conversation_history.append({"role": "user", "content": dm_note})
                
                needs_conversation_history_update = True
            else:
                print(f"ERROR: Missing required parameter 'hubName' for establishHub action")
                
        except Exception as e:
            print(f"ERROR: Exception while establishing hub: {str(e)}")
            import traceback
            traceback.print_exc()

    elif action_type == ACTION_STORAGE_INTERACTION:
        print(f"DEBUG: Processing storageInteraction action")
        try:
            # Import storage modules
            from storage_processor import process_storage_request
            from storage_manager import execute_storage_operation
            
            # Get storage description from parameters
            storage_description = parameters.get("description", "")
            character_name = parameters.get("characterName", "")
            
            # Fallback to party member if no character specified
            if not character_name:
                character_name = next((member for member in party_tracker_data["partyMembers"]), None)
                
            if not character_name:
                print(f"ERROR: No character name provided for storage interaction")
                return create_return(status="continue", needs_update=False)
                
            if not storage_description:
                print(f"ERROR: No storage description provided")
                return create_return(status="continue", needs_update=False)
                
            print(f"DEBUG: Processing storage request for {character_name}: '{storage_description}'")
            
            # Process natural language description into operation
            processor_result = process_storage_request(storage_description, character_name)
            
            if not processor_result.get("success"):
                print(f"ERROR: Storage processor failed: {processor_result.get('error')}")
                
                # Add error message to conversation
                error_message = f"Storage Error: {processor_result.get('error', 'Unknown error processing storage request')}"
                conversation_history.append({"role": "user", "content": error_message})
                needs_conversation_history_update = True
                return create_return(status="needs_response", needs_update=True)
                
            # Execute the validated storage operation
            operation = processor_result["operation"]
            print(f"DEBUG: Executing storage operation: {operation}")
            
            execution_result = execute_storage_operation(operation)
            
            if execution_result.get("success"):
                print(f"DEBUG: Storage operation successful: {execution_result.get('message')}")
                
                # Add success message to conversation
                success_message = f"Storage: {execution_result.get('message')}"
                conversation_history.append({"role": "user", "content": success_message})
                needs_conversation_history_update = True
                
            else:
                print(f"ERROR: Storage operation failed: {execution_result.get('error')}")
                
                # Add error message to conversation
                error_message = f"Storage Error: {execution_result.get('error', 'Unknown error executing storage operation')}"
                conversation_history.append({"role": "user", "content": error_message})
                needs_conversation_history_update = True
                
        except Exception as e:
            print(f"ERROR: Exception while processing storage interaction: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Add error message to conversation
            error_message = f"Storage System Error: An unexpected error occurred while processing your storage request."
            conversation_history.append({"role": "user", "content": error_message})
            needs_conversation_history_update = True

    elif action_type == ACTION_UPDATE_PARTY_TRACKER:
        print(f"DEBUG: Processing updatePartyTracker action")
        try:
            # Load current party tracker
            current_party_data = safe_json_load("party_tracker.json")
            if not current_party_data:
                current_party_data = party_tracker_data.copy() if party_tracker_data else {}
            
            current_module = current_party_data.get("module", "Unknown")
            
            # Check if module is being changed
            new_module = parameters.get("module")
            if new_module and new_module != current_module:
                print(f"DEBUG: Module change detected: {current_module} -> {new_module}")
                
                # Insert module transition marker immediately when module change is detected
                transition_text = f"Module transition: {current_module} to {new_module}"
                transition_message = {
                    "role": "user",
                    "content": transition_text
                }
                conversation_history.append(transition_message)
                print(f"DEBUG: Inserted module transition marker: '{transition_text}'")
                
                # Import campaign manager for auto-archiving
                from campaign_manager import CampaignManager
                campaign_manager = CampaignManager()
                
                # Auto-archive and summarize previous module
                if current_module != "Unknown":
                    print(f"DEBUG: Auto-archiving conversation and generating summary for {current_module}")
                    summary = campaign_manager.handle_cross_module_transition(
                        current_module, new_module, current_party_data, conversation_history
                    )
                    if summary:
                        print(f"DEBUG: Successfully archived conversation and generated summary for {current_module}")
                    else:
                        print(f"DEBUG: No summary generated for {current_module}")
                
                # Auto-update to starting location if not explicitly provided
                if ("currentAreaId" not in parameters and 
                    "currentLocationId" not in parameters):
                    try:
                        location_id, location_name, area_id, area_name = get_module_starting_location(new_module)
                        print(f"DEBUG: Auto-setting starting location for {new_module}: {location_name} [{location_id}] in {area_name} [{area_id}]")
                        
                        # Add starting location to parameters for processing below
                        parameters["currentLocationId"] = location_id
                        parameters["currentLocation"] = location_name
                        parameters["currentAreaId"] = area_id
                        parameters["currentArea"] = area_name
                    except Exception as e:
                        print(f"WARNING: Could not auto-set starting location for {new_module}: {e}")
            
            # Update party tracker with all provided parameters
            for key, value in parameters.items():
                if key in ["currentLocationId", "currentLocation", "currentAreaId", "currentArea"]:
                    if "worldConditions" not in current_party_data:
                        current_party_data["worldConditions"] = {}
                    current_party_data["worldConditions"][key] = value
                elif key == "module":
                    current_party_data["module"] = value
                else:
                    # Handle any other party tracker fields
                    current_party_data[key] = value
            
            # Save updated party tracker
            safe_json_dump(current_party_data, "party_tracker.json")
            print(f"DEBUG: Party tracker updated successfully")
            # Always reload conversation history to pick up changes
            needs_conversation_history_update = True
            
        except Exception as e:
            print(f"ERROR: Exception while updating party tracker: {str(e)}")
            import traceback
            traceback.print_exc()

    elif action_type == ACTION_MOVE_BACKGROUND_NPC:
        print(f"DEBUG: Processing moveBackgroundNPC action")
        try:
            # Extract parameters
            npc_name = parameters.get("npcName")
            context = parameters.get("context", "")
            current_location = parameters.get("currentLocation")
            
            if not npc_name:
                print(f"ERROR: Missing required parameter 'npcName' for moveBackgroundNPC action")
                return create_return(status="continue", needs_update=False)
            
            # Process the NPC movement
            success = move_background_npc(npc_name, context, current_location, party_tracker_data)
            
            if success:
                print(f"DEBUG: Successfully processed movement for NPC: {npc_name}")
                needs_conversation_history_update = True
            else:
                print(f"ERROR: Failed to process movement for NPC: {npc_name}")
                
        except Exception as e:
            print(f"ERROR: Exception while processing moveBackgroundNPC: {str(e)}")
            import traceback
            traceback.print_exc()

    elif action_type == ACTION_SAVE_GAME:
        print("DEBUG: Processing save game action")
        try:
            from save_game_manager import SaveGameManager
            
            # Extract parameters
            description = parameters.get("description", "")
            save_mode = parameters.get("saveMode", "essential")  # "essential" or "full"
            
            # Create save game
            manager = SaveGameManager()
            success, message = manager.create_save_game(description, save_mode)
            
            if success:
                print(f"DEBUG: Save game created successfully: {message}")
                # Add success message to conversation
                save_message = f"Game saved successfully! {message}"
                conversation_history.append({"role": "system", "content": save_message})
                needs_conversation_history_update = True
            else:
                print(f"ERROR: Failed to save game: {message}")
                # Add error message to conversation  
                error_message = f"Failed to save game: {message}"
                conversation_history.append({"role": "system", "content": error_message})
                needs_conversation_history_update = True
                
        except Exception as e:
            print(f"ERROR: Exception while processing saveGame: {str(e)}")
            import traceback
            traceback.print_exc()

    elif action_type == ACTION_RESTORE_GAME:
        print("DEBUG: Processing restore game action")
        try:
            from save_game_manager import SaveGameManager
            
            # Extract parameters
            save_folder = parameters.get("saveFolder")
            
            if not save_folder:
                print("ERROR: Missing required parameter 'saveFolder' for restoreGame action")
                error_message = "Error: No save folder specified for restore operation"
                conversation_history.append({"role": "system", "content": error_message})
                needs_conversation_history_update = True
                return create_return(needs_update=needs_conversation_history_update)
            
            # Restore save game
            manager = SaveGameManager()
            success, message = manager.restore_save_game(save_folder)
            
            if success:
                print(f"DEBUG: Save game restored successfully: {message}")
                # Add success message to conversation
                restore_message = f"Game restored successfully! {message}\nRestarting game session..."
                conversation_history.append({"role": "system", "content": restore_message})
                needs_conversation_history_update = True
                # Return special status to indicate game should restart
                return create_return(status="restart", needs_update=needs_conversation_history_update)
            else:
                print(f"ERROR: Failed to restore game: {message}")
                # Add error message to conversation
                error_message = f"Failed to restore game: {message}"
                conversation_history.append({"role": "system", "content": error_message})
                needs_conversation_history_update = True
                
        except Exception as e:
            print(f"ERROR: Exception while processing restoreGame: {str(e)}")
            import traceback
            traceback.print_exc()

    elif action_type == ACTION_LIST_SAVES:
        print("DEBUG: Processing list saves action")
        try:
            from save_game_manager import SaveGameManager
            
            # Get list of save games
            manager = SaveGameManager()
            saves = manager.list_save_games()
            
            if saves:
                save_list_text = "Available save games:\n"
                for i, save in enumerate(saves, 1):
                    save_date = save.get("save_date_readable", "Unknown date")
                    description = save.get("description", "No description")
                    save_mode = save.get("save_mode", "unknown")
                    module = save.get("module", "Unknown")
                    save_folder = save.get("save_folder", "Unknown")
                    
                    save_list_text += f"{i}. {save_folder}\n"
                    save_list_text += f"   Date: {save_date}\n"
                    save_list_text += f"   Module: {module}\n"
                    save_list_text += f"   Mode: {save_mode}\n"
                    save_list_text += f"   Description: {description}\n\n"
            else:
                save_list_text = "No save games found."
            
            print(f"DEBUG: Found {len(saves)} save games")
            conversation_history.append({"role": "system", "content": save_list_text})
            needs_conversation_history_update = True
                
        except Exception as e:
            print(f"ERROR: Exception while processing listSaves: {str(e)}")
            import traceback
            traceback.print_exc()

    elif action_type == ACTION_DELETE_SAVE:
        print("DEBUG: Processing delete save action")
        try:
            from save_game_manager import SaveGameManager
            
            # Extract parameters
            save_folder = parameters.get("saveFolder")
            
            if not save_folder:
                print("ERROR: Missing required parameter 'saveFolder' for deleteSave action")
                error_message = "Error: No save folder specified for delete operation"
                conversation_history.append({"role": "system", "content": error_message})
                needs_conversation_history_update = True
                return create_return(needs_update=needs_conversation_history_update)
            
            # Delete save game
            manager = SaveGameManager()
            success, message = manager.delete_save_game(save_folder)
            
            if success:
                print(f"DEBUG: Save game deleted successfully: {message}")
                conversation_history.append({"role": "system", "content": message})
                needs_conversation_history_update = True
            else:
                print(f"ERROR: Failed to delete save game: {message}")
                conversation_history.append({"role": "system", "content": f"Error: {message}"})
                needs_conversation_history_update = True
                
        except Exception as e:
            print(f"ERROR: Exception while processing deleteSave: {str(e)}")
            import traceback
            traceback.print_exc()

    else:
        print(f"WARNING: Unknown action type: {action_type}")
    
    return create_return(needs_update=needs_conversation_history_update)

def move_background_npc(npc_name, context, current_location_hint=None, party_tracker_data=None):
    """
    AI-driven function to handle NPC movement/status changes with atomic safety
    
    Args:
        npc_name (str): Name of the NPC to move/update
        context (str): Narrative context explaining what happened to the NPC
        current_location_hint (str, optional): Hint about current location if not found automatically
        party_tracker_data (dict, optional): Party tracker data for module context
        
    Returns:
        bool: True if successful, False otherwise
    """
    import json
    import copy
    import shutil
    import os
    import time
    import threading
    from datetime import datetime
    from file_operations import safe_write_json, safe_read_json
    
    print(f"DEBUG: moveBackgroundNPC called for {npc_name}")
    print(f"DEBUG: Context: {context}")
    
    # File locking for atomic operations (similar to updateCharacterInfo)
    lock = threading.Lock()
    
    with lock:
        try:
            # Get module context
            if not party_tracker_data:
                party_tracker_data = safe_read_json("party_tracker.json")
                if not party_tracker_data:
                    print("ERROR: Could not load party tracker data")
                    return False
            
            module_name = party_tracker_data.get("module", "").replace(" ", "_")
            if not module_name:
                print("ERROR: No current module found in party tracker")
                return False
                
            path_manager = ModulePathManager(module_name)
            
            # Find the NPC in area files
            npc_location = find_npc_in_areas(npc_name, path_manager, current_location_hint)
            if not npc_location:
                print(f"ERROR: Could not find NPC '{npc_name}' in any location")
                return False
                
            area_file, location_id, npc_data = npc_location
            print(f"DEBUG: Found {npc_name} in {area_file} at location {location_id}")
            
            # Load area data with backup
            area_data = safe_read_json(area_file)
            if not area_data:
                print(f"ERROR: Could not load area data from {area_file}")
                return False
                
            # Create backup
            backup_path = create_area_backup(area_file)
            if not backup_path:
                print("WARNING: Could not create backup, proceeding anyway")
            
            # Get party NPCs for validation
            party_npcs = party_tracker_data.get("partyNPCs", [])
            
            # Retry loop with fallback system
            ai_decision = None
            max_attempts = 5
            
            for attempt in range(1, max_attempts + 1):
                print(f"DEBUG: AI decision attempt {attempt}/{max_attempts}")
                
                # Get AI decision on what to do with the NPC
                ai_decision = get_ai_npc_movement_decision(
                    npc_name, context, npc_data, area_data, location_id, module_name, party_npcs, attempt
                )
                
                if ai_decision:
                    # Validate the AI decision
                    validation_result = validate_npc_movement_decision(ai_decision, area_data, location_id, party_npcs)
                    if validation_result["valid"]:
                        print(f"DEBUG: AI decision validated successfully on attempt {attempt}")
                        break
                    else:
                        print(f"DEBUG: AI decision validation failed on attempt {attempt}: {validation_result['reason']}")
                        if attempt == max_attempts:
                            print("ERROR: Max attempts reached, AI could not generate valid decision")
                            return False
                        else:
                            # Add validation feedback to context for retry
                            context += f"\n\nPREVIOUS ATTEMPT FAILED: {validation_result['reason']}"
                else:
                    print(f"DEBUG: AI could not generate decision on attempt {attempt}")
                    if attempt == max_attempts:
                        print("ERROR: Max attempts reached, AI could not determine appropriate action")
                        return False
            
            if not ai_decision:
                print("ERROR: AI could not determine appropriate action after all attempts")
                return False
                
            print(f"DEBUG: Final AI decision: {ai_decision.get('action')} - {ai_decision.get('reasoning', 'No reasoning')}")
            
            # Execute the AI decision with surgical updates
            success = execute_npc_movement_decision(ai_decision, area_data, location_id, npc_name, path_manager)
            
            if success:
                # Save updated area data
                if safe_write_json(area_file, area_data):
                    print(f"DEBUG: Successfully updated area file {area_file}")
                    # Clean up old backups
                    cleanup_old_area_backups(area_file)
                    return True
                else:
                    print(f"ERROR: Failed to save updated area data")
                    # Restore from backup if save failed
                    if backup_path and os.path.exists(backup_path):
                        try:
                            shutil.copy2(backup_path, area_file)
                            print("DEBUG: Restored area file from backup due to save failure")
                        except Exception as e:
                            print(f"ERROR: Could not restore from backup: {e}")
                    return False
            else:
                print("ERROR: Failed to execute NPC movement decision")
                return False
                
        except Exception as e:
            print(f"ERROR: Exception in move_background_npc: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def find_npc_in_areas(npc_name, path_manager, location_hint=None):
    """Find an NPC in area files, returning (area_file, location_id, npc_data)"""
    import glob
    import os
    from file_operations import safe_read_json
    
    # Get all area files in the module, excluding backup files
    area_pattern = f"{path_manager.module_dir}/areas/*.json"
    all_files = glob.glob(area_pattern)
    
    # Filter out backup files (_BU.json) and backup copies (.backup_*)
    area_files = []
    for file_path in all_files:
        filename = os.path.basename(file_path)
        # Skip backup files
        if filename.endswith('_BU.json') or '.backup_' in filename:
            print(f"DEBUG: Skipping backup file: {filename}")
            continue
        area_files.append(file_path)
    
    print(f"DEBUG: Searching {len(area_files)} active area files (excluded {len(all_files) - len(area_files)} backup files)")
    
    for area_file in area_files:
        try:
            area_data = safe_read_json(area_file)
            if not area_data:
                continue
                
            # Search through all locations in this area
            for location in area_data.get("locations", []):
                location_id = location.get("locationId", "")
                
                # If location hint provided, check if this matches
                if location_hint and location_hint != location_id:
                    continue
                    
                # Search NPCs in this location
                for npc in location.get("npcs", []):
                    if npc.get("name", "").lower() == npc_name.lower():
                        return (area_file, location_id, npc)
                        
        except Exception as e:
            print(f"WARNING: Could not search area file {area_file}: {e}")
            continue
    
    return None

def get_ai_npc_movement_decision(npc_name, context, npc_data, area_data, location_id, module_name, party_npcs=None, attempt=1):
    """Use AI to determine what to do with the NPC based on context"""
    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Get available locations for potential moves
        available_locations = []
        for location in area_data.get("locations", []):
            loc_id = location.get("locationId", "")
            loc_name = location.get("name", "")
            if loc_id and loc_name and loc_id != location_id:
                available_locations.append(f"{loc_id} ({loc_name})")
        
        # Check if this is a party NPC vs background NPC
        party_npc_names = [npc.get("name", "").lower() for npc in (party_npcs or [])]
        is_party_npc = npc_name.lower() in party_npc_names
        
        # Load and validate against location schema
        from jsonschema import validate, ValidationError
        import json
        
        try:
            with open("loca_schema.json", "r") as f:
                location_schema = json.load(f)
        except Exception as e:
            print(f"WARNING: Could not load location schema: {e}")
            location_schema = None
        
        system_prompt = f"""You are an expert D&D narrative manager specialized in NPC movement and status changes. Your job is to make intelligent decisions about background NPCs based on narrative context while maintaining strict game world consistency.

CRITICAL DISTINCTIONS:
- BACKGROUND NPCs: NPCs found in location files who are not traveling with the party
- PARTY NPCs: NPCs actively traveling with and assisting the party (managed separately)
- This action is ONLY for BACKGROUND NPCs - NPCs who exist in specific locations

CURRENT NPC CLASSIFICATION:
- {npc_name} is {'a PARTY NPC (ERROR - use updatePartyNPCs instead)' if is_party_npc else 'a BACKGROUND NPC (correct for this action)'}

AVAILABLE ACTIONS FOR BACKGROUND NPCs:
1. "remove" - Remove NPC from location entirely
   - Use for: Captured and taken elsewhere, fled permanently, left the area
   - Result: NPC disappears from location, may add location description update
   
2. "update_status" - Keep NPC in location but change their description  
   - Use for: Death, injury, status change, but NPC remains in place
   - Result: NPC description updated, location may be updated too
   
3. "move" - Move NPC to different location within same area
   - Use for: NPC relocated to another nearby location
   - Result: NPC moves between locations, descriptions updated

SCHEMA VALIDATION REQUIREMENTS:
All NPC objects must maintain this exact structure:
{{
  "name": "string (required)",
  "description": "string (required)", 
  "attitude": "string (required)"
}}

CONTEXT INFORMATION:
- Module: {module_name}
- Current Location: {location_id}
- Available Target Locations: {', '.join(available_locations) if available_locations else 'None (cannot use move action)'}
- Attempt: {attempt}/5

RESPONSE FORMAT (JSON only):
{{
  "action": "remove|update_status|move",
  "reasoning": "Brief explanation of decision based on narrative context",
  "newDescription": "Updated NPC description if action is update_status (required field, max 500 chars)",
  "newAttitude": "Updated attitude if action is update_status (required field)", 
  "newLocation": "Target location ID if action is move (must match available locations exactly)",
  "locationUpdate": "Brief addition to location description explaining change (optional, max 200 chars)"
}}

DECISION GUIDELINES WITH EXAMPLES:

CAPTURE SCENARIO:
Context: "Rusk was captured by the party and taken to Thornwood"
Decision: "remove" - Rusk is no longer at this location
Reasoning: "Captured and removed from area by party"

DEATH SCENARIO:  
Context: "The merchant was killed by bandits"
Decision: "update_status" - Body remains in location
New Description: "The merchant's lifeless body lies sprawled among scattered goods..."
New Attitude: "Dead"
Location Update: "Signs of violence and blood stain the ground"

RELOCATION SCENARIO:
Context: "Elen went to report to the watchtower"  
Decision: "move" - IF watchtower location exists in available locations
New Location: "WT01" (only if this exact ID exists)
Reasoning: "Moved to fulfill duty obligations"

INJURY SCENARIO:
Context: "The guard was wounded but survived the attack"
Decision: "update_status" - Guard stays but is injured
New Description: "A wounded guard with bandaged arms, still determined despite recent injuries..."
New Attitude: "Cautious but resilient"

IMPORTANT VALIDATION RULES:
- NEVER move party NPCs (they travel with the party automatically)
- ONLY use exact location IDs from the available locations list
- ALWAYS provide required fields: newDescription and newAttitude for update_status
- Keep descriptions realistic and immersive
- Maintain narrative consistency with established world"""

        user_prompt = f"""Background NPC Movement Decision Request:

NPC Name: {npc_name}
Current Description: {npc_data.get('description', 'No description available')}
Current Attitude: {npc_data.get('attitude', 'No attitude specified')}
Narrative Context: {context}
Current Location: {location_id}

Based on this narrative context, determine the most appropriate action for this background NPC. Consider the story implications and choose the action that best maintains narrative consistency.

Remember: This is a background NPC management action, not party NPC management."""

        response = client.chat.completions.create(
            model=config.NPC_INFO_UPDATE_MODEL,  # Use claude-sonnet-4-20250514 as specified
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7  # As specified by user
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"DEBUG: AI movement decision response: {ai_response}")
        
        # Parse JSON response
        import re
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            print("ERROR: No valid JSON found in AI response")
            return None
            
    except Exception as e:
        print(f"ERROR: AI decision failed: {str(e)}")
        return None

def validate_npc_movement_decision(decision, area_data, location_id, party_npcs):
    """Validate AI decision against schema and game rules"""
    try:
        # Check required fields
        if not isinstance(decision, dict):
            return {"valid": False, "reason": "Decision must be a JSON object"}
            
        action = decision.get("action")
        if action not in ["remove", "update_status", "move"]:
            return {"valid": False, "reason": f"Invalid action '{action}'. Must be: remove, update_status, or move"}
        
        # Validate action-specific requirements
        if action == "update_status":
            if not decision.get("newDescription"):
                return {"valid": False, "reason": "update_status action requires newDescription field"}
            if not decision.get("newAttitude"):
                return {"valid": False, "reason": "update_status action requires newAttitude field"}
            
            # Check length limits
            if len(decision.get("newDescription", "")) > 500:
                return {"valid": False, "reason": "newDescription must be 500 characters or less"}
                
        elif action == "move":
            new_location = decision.get("newLocation")
            if not new_location:
                return {"valid": False, "reason": "move action requires newLocation field"}
                
            # Check if target location exists
            valid_locations = [loc.get("locationId") for loc in area_data.get("locations", [])]
            if new_location not in valid_locations:
                return {"valid": False, "reason": f"Target location '{new_location}' does not exist. Valid locations: {valid_locations}"}
        
        # Check location update length
        location_update = decision.get("locationUpdate", "")
        if location_update and len(location_update) > 200:
            return {"valid": False, "reason": "locationUpdate must be 200 characters or less"}
        
        # Schema validation - check NPC structure requirements
        if action == "update_status":
            # Simulate the NPC object that would be created
            test_npc = {
                "name": "test",
                "description": decision.get("newDescription"),
                "attitude": decision.get("newAttitude")
            }
            
            # Basic validation
            for field in ["name", "description", "attitude"]:
                if not test_npc.get(field):
                    return {"valid": False, "reason": f"NPC object missing required field: {field}"}
                if not isinstance(test_npc[field], str):
                    return {"valid": False, "reason": f"NPC field '{field}' must be a string"}
        
        return {"valid": True, "reason": "Decision validated successfully"}
        
    except Exception as e:
        return {"valid": False, "reason": f"Validation error: {str(e)}"}

def execute_npc_movement_decision(decision, area_data, location_id, npc_name, path_manager):
    """Execute the AI's decision with surgical updates to area data"""
    try:
        action = decision.get("action")
        
        # Find the location and NPC in area data
        target_location = None
        npc_index = None
        
        for location in area_data.get("locations", []):
            if location.get("locationId") == location_id:
                target_location = location
                # Find NPC index
                for i, npc in enumerate(location.get("npcs", [])):
                    if npc.get("name", "").lower() == npc_name.lower():
                        npc_index = i
                        break
                break
        
        if not target_location or npc_index is None:
            print("ERROR: Could not find location or NPC in area data")
            return False
        
        if action == "remove":
            # Remove NPC from location
            target_location["npcs"].pop(npc_index)
            print(f"DEBUG: Removed {npc_name} from {location_id}")
            
            # Update location description if provided
            location_update = decision.get("locationUpdate")
            if location_update:
                current_desc = target_location.get("description", "")
                target_location["description"] = f"{current_desc} {location_update}".strip()
                
        elif action == "update_status":
            # Update NPC description and attitude
            new_description = decision.get("newDescription")
            new_attitude = decision.get("newAttitude")
            
            if new_description:
                target_location["npcs"][npc_index]["description"] = new_description
                print(f"DEBUG: Updated description for {npc_name}")
            
            if new_attitude:
                target_location["npcs"][npc_index]["attitude"] = new_attitude
                print(f"DEBUG: Updated attitude for {npc_name}")
                
            # Update location description if provided
            location_update = decision.get("locationUpdate")
            if location_update:
                current_desc = target_location.get("description", "")
                target_location["description"] = f"{current_desc} {location_update}".strip()
                    
        elif action == "move":
            # Move NPC to different location
            new_location_id = decision.get("newLocation")
            if not new_location_id:
                print("ERROR: Move action specified but no target location provided")
                return False
                
            # Find target location
            target_new_location = None
            for location in area_data.get("locations", []):
                if location.get("locationId") == new_location_id:
                    target_new_location = location
                    break
                    
            if not target_new_location:
                print(f"ERROR: Target location {new_location_id} not found")
                return False
                
            # Move NPC
            npc_to_move = target_location["npcs"].pop(npc_index)
            target_new_location["npcs"].append(npc_to_move)
            print(f"DEBUG: Moved {npc_name} from {location_id} to {new_location_id}")
            
            # Update both location descriptions if provided
            location_update = decision.get("locationUpdate")
            if location_update:
                # Update source location
                current_desc = target_location.get("description", "")
                target_location["description"] = f"{current_desc} {location_update}".strip()
        
        else:
            print(f"ERROR: Unknown action: {action}")
            return False
            
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to execute decision: {str(e)}")
        return False

def create_area_backup(area_file):
    """Create timestamped backup of area file"""
    import shutil
    import os
    from datetime import datetime
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{area_file}.backup_npc_move_{timestamp}"
        shutil.copy2(area_file, backup_name)
        print(f"DEBUG: Created area backup: {os.path.basename(backup_name)}")
        return backup_name
    except Exception as e:
        print(f"ERROR: Could not create area backup: {e}")
        return None

def cleanup_old_area_backups(area_file, max_backups=5):
    """Clean up old area backup files"""
    import os
    
    try:
        directory = os.path.dirname(area_file)
        base_name = os.path.basename(area_file)
        
        backup_files = []
        for file in os.listdir(directory):
            if file.startswith(f"{base_name}.backup_npc_move_") and file.endswith(".json"):
                backup_path = os.path.join(directory, file)
                mtime = os.path.getmtime(backup_path)
                backup_files.append((mtime, backup_path))
        
        # Sort by modification time (newest first) and remove old ones
        backup_files.sort(reverse=True)
        if len(backup_files) > max_backups:
            for _, old_backup in backup_files[max_backups:]:
                try:
                    os.remove(old_backup)
                    print(f"DEBUG: Removed old backup: {os.path.basename(old_backup)}")
                except Exception as e:
                    print(f"WARNING: Could not remove old backup: {e}")
                    
    except Exception as e:
        print(f"WARNING: Backup cleanup failed: {e}")