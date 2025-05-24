import json
import subprocess
import os
from location_manager import get_location_data
from campaign_path_manager import CampaignPathManager
from plot_update import update_plot

# Action type constants
ACTION_CREATE_ENCOUNTER = "createEncounter"
ACTION_UPDATE_TIME = "updateTime"
ACTION_UPDATE_PLOT = "updatePlot"
ACTION_EXIT_GAME = "exitGame"
ACTION_TRANSITION_LOCATION = "transitionLocation"
ACTION_LEVEL_UP = "levelUp"
ACTION_UPDATE_PLAYER_INFO = "updatePlayerInfo"
ACTION_UPDATE_NPC_INFO = "updateNPCInfo"
ACTION_UPDATE_PARTY_NPCS = "updatePartyNPCs"

def update_party_npcs(party_tracker_data, operation, npc):
    """Update NPC party members (add or remove)"""
    if operation == "add":
        path_manager = CampaignPathManager()
        npc_file = path_manager.get_npc_path(npc['name'])
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

    with open("party_tracker.json", "w", encoding="utf-8") as file:
        json.dump(party_tracker_data, file, indent=2)
    print(f"DEBUG: Party NPCs updated - {operation} {npc['name']}")

def run_combat_simulation(encounter_id, party_tracker_data, location_data):
    """Run the combat simulation"""
    # Import here to avoid circular imports
    from combat_manager import run_combat_simulation as run_combat
    return run_combat(encounter_id, party_tracker_data, location_data)

def process_action(action, party_tracker_data, location_data, conversation_history):
    """Process an action based on its type"""
    # Import modules here to avoid circular imports
    import location_manager
    from update_world_time import update_world_time
    from plot_update import update_plot
    import update_player_info
    import update_npc_info

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
                with open("party_tracker.json", "w", encoding="utf-8") as file:
                    json.dump(party_tracker_data, file, indent=2)
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
                    path_manager = CampaignPathManager()
                    player_file = path_manager.get_player_path(player_name)
                    with open(player_file, "w", encoding="utf-8") as file:
                        json.dump(updated_player_info, file, indent=2)
                    print(f"DEBUG: Updated player file for {player_name}")
                else:
                    print("WARNING: Combat simulation did not return valid player info. Player file not updated.")

                # Copy combat summary to main conversation history
                with open("combat_conversation_history.json", "r", encoding="utf-8") as combat_file:
                    combat_history = json.load(combat_file)
                    combat_summary = next((entry for entry in reversed(combat_history) if entry["role"] == "assistant" and "Combat Summary:" in entry["content"]), None)

                if combat_summary:
                    modified_combat_summary = {
                        "role": "user",
                        "content": combat_summary["content"]
                    }
                    conversation_history.append(modified_combat_summary)
                    # Import save_conversation_history and get_ai_response from main
                    from main import save_conversation_history, get_ai_response, process_ai_response
                    save_conversation_history(conversation_history)
                    new_response = get_ai_response(conversation_history)
                    process_ai_response(new_response, party_tracker_data, reloaded_location_data, conversation_history)
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
        time_estimate_str = str(parameters["timeEstimate"])
        update_world_time(time_estimate_str)

    elif action_type == ACTION_UPDATE_PLOT:
        plot_point_id = parameters["plotPointId"]
        new_status = parameters["newStatus"]
        plot_impact = parameters.get("plotImpact", "")
        plot_filename = "campaign_plot.json"  # Now using unified plot file
        updated_plot = update_plot(plot_point_id, new_status, plot_impact, plot_filename)

    elif action_type == ACTION_EXIT_GAME:
        conversation_history.append({"role": "user", "content": "Dungeon Master Note: Resume the game, the player has returned."})
        from main import save_conversation_history, exit_game
        save_conversation_history(conversation_history)
        exit_game()

    elif action_type == ACTION_TRANSITION_LOCATION:
        new_location_name_or_id = parameters["newLocation"] # This could be a name or an ID
        area_connectivity_id = parameters.get("areaConnectivityId")
        current_location_name = party_tracker_data["worldConditions"]["currentLocation"]
        current_area_name = party_tracker_data["worldConditions"]["currentArea"]
        current_area_id = party_tracker_data["worldConditions"]["currentAreaId"]
        
        # Debug the exact string values for easier troubleshooting
        print(f"DEBUG: Transitioning from '{current_location_name}' to '{new_location_name_or_id}'")
        print(f"DEBUG: Current location string (hex): {current_location_name.encode('utf-8').hex()}")
        print(f"DEBUG: New location string (hex): {new_location_name_or_id.encode('utf-8').hex()}")
        
        # Use enhanced location manager with robust string matching
        transition_prompt = location_manager.handle_location_transition(
            current_location_name, 
            new_location_name_or_id, 
            current_area_name, 
            current_area_id, 
            area_connectivity_id
        )

        if transition_prompt:
            conversation_history.append({"role": "user", "content": f"Location transition: {current_location_name} to {new_location_name_or_id}"}) # Use the provided name/ID
            print("DEBUG: Location transition complete")
             # After transition, the current_location_data in the main loop might be stale.
            # We need to ensure the AI response processing uses the *new* location data.
            # This might require process_ai_response to reload location data or for main_game_loop to handle it.
            # For now, let's assume the main loop will reload it before the next AI call.
        else:
            print("ERROR: Failed to handle location transition")

    elif action_type == ACTION_LEVEL_UP:
        entity_name = parameters.get("entityName")
        new_level = parameters.get("newLevel")

        with open("leveling_info.txt", "r", encoding="utf-8") as file:
            leveling_info = file.read()

        dm_note = f"Leveling Dungeon Master Guidance: Proceed with leveling up the player character or the party NPC given the 5th Edition role playing game rules. Only level the player or the party NPC one level at a time to ensure no mistakes are made. If you are leveling up a party NPC then pass all changes at once using the 'updateNPCInfo' action and use the narration to narrate the party NPCs growth. If you are leveling up a player character then you must ask the player for important decisions and choices they would have control over. After the player has provided the needed information then use the 'updatePlayerInfo' to pass all changes to the players character sheet and include the experience goal for the next level. Do not update the player's information in segements. \n\n{leveling_info}"
        conversation_history.append({"role": "user", "content": dm_note})
        # Import get_ai_response and process_ai_response from main
        from main import get_ai_response, process_ai_response
        new_response = get_ai_response(conversation_history)
        return process_ai_response(new_response, party_tracker_data, location_data, conversation_history) # Pass location_data

    elif action_type == ACTION_UPDATE_PLAYER_INFO:
        print(f"DEBUG: Processing updatePlayerInfo action")
        changes = parameters["changes"]
        player_name = next((member.lower() for member in party_tracker_data["partyMembers"]), None)

        if player_name:
            print(f"DEBUG: Updating player info for {player_name}")
            try:
                updated_player_info = update_player_info.update_player(player_name, changes)
                print(f"DEBUG: Player info updated successfully")
                needs_conversation_history_update = True
            except Exception as e:
                print(f"ERROR: Failed to update player info: {str(e)}")
        else:
            print("ERROR: No player found in the party tracker data.")

    elif action_type == ACTION_UPDATE_NPC_INFO:
        print(f"DEBUG: Processing updateNPCInfo action")
        changes = parameters["changes"]
        npc_name = parameters["npcName"]

        print(f"DEBUG: Updating NPC info for {npc_name}")
        try:
            updated_npc_info = update_npc_info.update_npc(npc_name, changes)
            print(f"DEBUG: NPC info updated successfully")
            needs_conversation_history_update = True
        except Exception as e:
            print(f"ERROR: Failed to update NPC info: {str(e)}")

    elif action_type == ACTION_UPDATE_PARTY_NPCS:
        operation = parameters["operation"]
        npc = parameters["npc"]
        update_party_npcs(party_tracker_data, operation, npc)

    else:
        print(f"WARNING: Unknown action type: {action_type}")
    
    return needs_conversation_history_update