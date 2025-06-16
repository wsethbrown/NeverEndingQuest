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
        print(f"DEBUG: Cross-area transition: {is_cross_area}")
        if area_connectivity_id:
            print(f"DEBUG: Generated area connectivity ID: {area_connectivity_id}")
        
        return True, "", area_connectivity_id
        
    except Exception as e:
        return False, f"Location validation failed with exception: {str(e)}", None

def update_party_npcs(party_tracker_data, operation, npc):
    """Update NPC party members (add or remove)"""
    if operation == "add":
        path_manager = ModulePathManager()
        npc_file = path_manager.get_character_path(npc['name'])
        if not os.path.exists(npc_file):
            # NPC file doesn't exist, so we need to create it
            try:
                # Add this debug line right before the subprocess.run call
                print(f"DEBUG: Calling npc_builder.py with arguments: {npc['name']} {npc.get('race', '')} {npc.get('class', '')} {str(npc.get('level', ''))} {npc.get('background', '')}")

                subprocess.run([
                    "python", "npc_builder.py",
                    npc['name'],
                    npc.get('race', ''),
                    npc.get('class', ''),
                    str(npc.get('level', '')),
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
                    path_manager = ModulePathManager()
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
        
        # VALIDATE: Check if location transition is valid
        is_valid, error_message, auto_area_connectivity_id = validate_location_transition(
            location_graph, current_location_id, new_location_name_or_id
        )
        
        if not is_valid:
            print(f"ERROR: {error_message}")
            return create_return(
                status="error", 
                needs_update=False,
                response_data={"error_message": error_message}
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
                    
                    # Auto-summarize the module being left and update campaign state
                    summary = campaign_manager.handle_cross_module_transition(
                        from_module, to_module, updated_party_tracker, conversation_history
                    )
                    
                    # Update party tracker module field
                    updated_party_tracker["module"] = to_module
                    safe_json_dump(updated_party_tracker, "party_tracker.json")
                    
                    # Inject accumulated campaign context
                    campaign_context = campaign_manager.get_accumulated_summaries_context(to_module)
                    if campaign_context:
                        conversation_history.append({
                            "role": "system", 
                            "content": f"=== CAMPAIGN CONTEXT ===\n{campaign_context}"
                        })
                        save_conversation_history(conversation_history)
                        print(f"DEBUG: Campaign context injected for {to_module}")
                    
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

    else:
        print(f"WARNING: Unknown action type: {action_type}")
    
    return create_return(needs_update=needs_conversation_history_update)