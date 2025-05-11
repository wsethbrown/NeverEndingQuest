import json
import os
import time
from xp import main as calculate_xp
from openai import OpenAI
from config import OPENAI_API_KEY
import update_player_info
import update_npc_info
import update_encounter
import update_party_tracker

# Updated color constants
SOLID_GREEN = "\033[38;2;0;180;0m"  # Slightly darker solid green for player name
LIGHT_OFF_GREEN = "\033[38;2;100;180;100m"  # More muted light green for stats
SOFT_REDDISH_ORANGE = "\033[38;2;204;102;0m"  # Existing color for DM narration
RESET_COLOR = "\033[0m"

# Models
MAIN_MODEL = "gpt-4o-mini"
SCHEMA_UPDATER_MODEL = "gpt-4o-2024-08-06"
DIALOGUE_SUMMARY_MODEL = "gpt-4o-mini"

# Temperature
TEMPERATURE = 1

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

conversation_history_file = "combat_conversation_history.json"
second_model_history_file = "second_model_history.json"
third_model_history_file = "third_model_history.json"

# Updated color constant with softer reddish-orange
SOFT_REDDISH_ORANGE = "\033[38;2;204;102;0m"
RESET_COLOR = "\033[0m"

conversation_history_file = "combat_conversation_history.json"
second_model_history_file = "second_model_history.json"
third_model_history_file = "third_model_history.json"

def get_current_area_id():
    with open("party_tracker.json", "r") as file:
        party_tracker = json.load(file)
    return party_tracker["worldConditions"]["currentAreaId"]


def get_location_data(location_id):
    current_area_id = get_current_area_id()
    print(f"DEBUG: Current area ID: {current_area_id}")
    area_file = f"{current_area_id}.json"
    print(f"DEBUG: Attempting to load area file: {area_file}")
    
    if not os.path.exists(area_file):
        print(f"ERROR: Area file {area_file} does not exist")
        return None

    with open(area_file, "r") as file:
        area_data = json.load(file)
    print(f"DEBUG: Loaded area data: {json.dumps(area_data, indent=2)}")
    
    for location in area_data["locations"]:
        if location["locationId"] == location_id:
            print(f"DEBUG: Found location data for ID {location_id}")
            return location
    
    print(f"ERROR: Location with ID {location_id} not found in area data")
    return None

def is_valid_json(json_string):
    try:
        json_object = json.loads(json_string)
        if not isinstance(json_object, dict):
            return False
        if "narration" not in json_object or not isinstance(json_object["narration"], str):
            return False
        if "actions" not in json_object or not isinstance(json_object["actions"], list):
            return False
        return True
    except json.JSONDecodeError:
        return False

def write_debug_output(content, filename="debug_second_model.json"):
    try:
        with open(filename, "w") as debug_file:
            json.dump(content, debug_file, indent=2)
        #print(f"Debug output written to {filename}")
    except Exception as e:
        print(f"DEBUG: Writing debug output: {str(e)}")

def merge_updates(original_data, updated_data):
    fields_to_update = ['hitPoints', 'equipment', 'attacksAndSpellcasting', 'experience_points']
    
    for field in fields_to_update:
        if field in updated_data:
            if field in ['equipment', 'attacksAndSpellcasting']:
                # For arrays, replace the entire array
                original_data[field] = updated_data[field]
            elif field == 'experience_points':
                # For XP, only update if the new value is greater than the existing value
                if updated_data[field] > original_data.get(field, 0):
                    original_data[field] = updated_data[field]
            else:
                # For simple fields like hitpoints, just update the value
                original_data[field] = updated_data[field]
    
    return original_data

def update_json_schema(ai_response, player_info, encounter_data, party_tracker_data):
    # Extract XP information if present
    xp_info = None
    if "XP Awarded:" in ai_response:
        xp_info = ai_response.split("XP Awarded:")[-1].strip()

    # Update player information, including XP
    player_name = player_info['name'].lower().replace(' ', '_')
    player_changes = f"Update the character's experience points. XP Awarded: {xp_info}"
    updated_player_info = update_player_info.update_player(player_name, player_changes)

    # Update encounter information (monsters only, no XP)
    encounter_id = encounter_data['encounterId']
    encounter_changes = "Combat has ended. Update status of monster creatures as needed."
    updated_encounter_data = update_encounter.update_encounter(encounter_id, encounter_changes)

    # Update NPCs if needed (no XP for NPCs)
    for creature in encounter_data['creatures']:
        if creature['type'] == 'npc':
            npc_name = creature['name']
            npc_changes = "Update NPC status after combat."
            update_npc_info.update_npc(npc_name, npc_changes)

    # Update party tracker: remove active combat encounter
    if 'worldConditions' in party_tracker_data and 'activeCombatEncounter' in party_tracker_data['worldConditions']:
        party_tracker_data['worldConditions']['activeCombatEncounter'] = ""

    # Save the updated party_tracker.json file
    with open("party_tracker.json", "w") as file:
        json.dump(party_tracker_data, file, indent=2)

    return updated_player_info, updated_encounter_data, party_tracker_data

def summarize_dialogue(conversation_history, location_data, party_tracker_data):
    print("DEBUG: Activating the third model...")

    dialogue_summary_prompt = [
        {"role": "system", "content": "Your task is to provide a concise summary of the combat encounter in the world's most popular 5th Edition roleplayign game dialogue between the dungeon master running the combat encounter and the player. Focus on capturing the key events, actions, and outcomes of the encounter. Be sure to include the experience points awarded, which will be provided in the conversation history. The summary should be written in a narrative style suitable for presenting to the main dungeon master. Include in your summary any defeated monsters or corpses left behind after combat."},
        {"role": "user", "content": json.dumps(conversation_history)}
    ]

    # Generate dialogue summary using GPT-4
    response = client.chat.completions.create(
        model=DIALOGUE_SUMMARY_MODEL,
        temperature=TEMPERATURE,
        messages=dialogue_summary_prompt
    )

    dialogue_summary = response.choices[0].message.content.strip()

    # Extract the current location ID from the party tracker data
    current_location_id = party_tracker_data["worldConditions"]["currentLocationId"]

    print(f"DEBUG: Current location ID: {current_location_id}")

    # Check if location_data is the correct location
    if location_data and location_data.get("locationId") == current_location_id:
        # Get the active combat encounter ID from the party tracker
        encounter_id = party_tracker_data["worldConditions"]["activeCombatEncounter"]

        # Create a new encounter entry
        new_encounter = {
            "encounterId": encounter_id,
            "summary": dialogue_summary,
            "impact": "To be determined",  # This field is required by the schema
            "worldConditions": {
                "year": int(party_tracker_data["worldConditions"]["year"]),
                "month": party_tracker_data["worldConditions"]["month"],
                "day": int(party_tracker_data["worldConditions"]["day"]),
                "time": party_tracker_data["worldConditions"]["time"]
            }
        }

        # Append the new encounter to the location's encounters array
        if "encounters" not in location_data:
            location_data["encounters"] = []
        location_data["encounters"].append(new_encounter)

        # Update the adventure summary
        if not location_data.get("adventureSummary"):
            location_data["adventureSummary"] = dialogue_summary
        else:
            location_data["adventureSummary"] += f"\n\n{dialogue_summary}"

        # Update the location.json file with the new encounter
        current_area_id = get_current_area_id()
        area_file = f"{current_area_id}.json"
        
        # Load the entire area data
        with open(area_file, "r") as file:
            area_data = json.load(file)
        
        # Find and update the specific location in the area data
        for i, loc in enumerate(area_data["locations"]):
            if loc["locationId"] == current_location_id:
                area_data["locations"][i] = location_data
                break
        
        # Save the updated area data
        with open(area_file, "w") as file:
            json.dump(area_data, file, indent=2)

        print(f"DEBUG: Encounter {encounter_id} added to {area_file}.")

        # Update conversation history with the combat summary
        conversation_history.append({"role": "assistant", "content": f"Combat Summary: {dialogue_summary}"})
        conversation_history.append({"role": "user", "content": "The combat has concluded. What would you like to do next?"})

        # Save the updated conversation history to the JSON file
        print(f"DEBUG: Attempting to write to file: {conversation_history_file}")
        try:
            with open(conversation_history_file, "w") as file:
                json.dump(conversation_history, file, indent=2)
            print("DEBUG: Conversation history saved successfully")
        except Exception as e:
            print(f"ERROR: Failed to save conversation history. Error: {str(e)}")

        print("Conversation history updated with encounter summary.")
    else:
        print(f"ERROR: Location {current_location_id} not found in location data or location data is incorrect.")

    return dialogue_summary

def read_prompt_from_file(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    with open(file_path, 'r') as file:
        return file.read().strip()

def update_encounter_data(encounter_id, changes):
    # Load the current encounter data
    with open(f"encounter_{encounter_id}.json", "r") as file:
        encounter_data = json.load(file)
    
    # Here you would implement the logic to update the encounter data
    # based on the changes described in the 'changes' parameter
    # This could involve parsing the changes and applying them to the encounter_data

    # For now, let's just print the changes
    print(f"Updating encounter {encounter_id} with changes: {changes}")

    # Save the updated encounter data
    with open(f"encounter_{encounter_id}.json", "w") as file:
        json.dump(encounter_data, file, indent=2)

    return encounter_data

def run_combat_simulation(encounter_id, party_data, location_data):
    global conversation_history, second_model_history, third_model_history

    print(f"DEBUG: Starting combat simulation for encounter {encounter_id}")
    #print(f"DEBUG: Party data: {json.dumps(party_data, indent=2)}")
    #print(f"DEBUG: Location data: {json.dumps(location_data, indent=2)}")

    # Load party tracker data
    with open("party_tracker.json", "r") as file:
        party_tracker_data = json.load(file)

    try:
        if not location_data:
            print(f"ERROR: Invalid location data. Contents: {location_data}")
            return "Combat simulation failed due to missing location data", None
        
        # Use the location data directly, as it should now be a single location object
        location_info = location_data

        # Initialize conversation histories
        conversation_history = [
            {"role": "system", "content": read_prompt_from_file('combat_sim_prompt.txt')},
            {"role": "system", "content": f"Current Combat Encounter: {encounter_id}"},
            {"role": "system", "content": ""},
            {"role": "system", "content": ""},
            {"role": "system", "content": ""}
        ]
        second_model_history = []
        third_model_history = []

        # Load encounter information
        json_file = f"encounter_{encounter_id}.json"
        with open(json_file, "r") as file:
            encounter_data = json.load(file)

        #print(f"DEBUG: Loaded encounter data: {json.dumps(encounter_data, indent=2)}")

        # Extract player and monster information
        player_info = None
        monster_templates = {}
        npc_templates = {}  # New dictionary for NPC templates

        for creature in encounter_data["creatures"]:
            if creature["type"] == "player":
                player_name = creature["name"].lower().replace(" ", "_")
                player_file = f"{player_name}.json"
                with open(player_file, "r") as file:
                    player_info = json.load(file)
            elif creature["type"] == "enemy":
                monster_type = creature["monsterType"]
                if monster_type not in monster_templates:
                    monster_file = f"{monster_type}.json"
                    with open(monster_file, "r") as file:
                        monster_templates[monster_type] = json.load(file)
            elif creature["type"] == "npc":
                npc_name = creature["name"].lower().replace(" ", "_")
                npc_file = f"{npc_name}.json"
                with open(npc_file, "r") as file:
                    npc_templates[npc_name] = json.load(file)

        # Update conversation history with current information
        conversation_history[2]["content"] = f"Player Character:\n{json.dumps({k: v for k, v in player_info.items() if k not in ['hitpoints', 'maxhitpoints']}, indent=2)}"
        conversation_history[3]["content"] = f"Monster Templates:\n{json.dumps(monster_templates, indent=2)}"
        conversation_history[4]["content"] = f"Location:\n{json.dumps(location_info, indent=2)}"
        conversation_history.append({"role": "system", "content": f"NPC Templates:\n{json.dumps(npc_templates, indent=2)}"})
        conversation_history.append({"role": "system", "content": f"Encounter Details:\n{json.dumps(encounter_data, indent=2)}"})

        while True:
            # Get AI's response
            response = client.chat.completions.create(
                model=MAIN_MODEL,
                temperature=TEMPERATURE,
                messages=conversation_history
            )
            ai_response = response.choices[0].message.content.strip()

            # Validate JSON response
            if not is_valid_json(ai_response):
                print("DEBUG: Invalid JSON response from AI. Requesting a new response.")
                conversation_history.append({
                    "role": "user",
                    "content": "Your previous response was not a valid JSON object with 'narration' and 'actions' fields. Please provide a valid JSON response."
                })
                continue

            # Parse the JSON response
            try:
                parsed_response = json.loads(ai_response)
                narration = parsed_response["narration"]
                actions = parsed_response["actions"]
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON parsing error: {str(e)}")
                print("DEBUG: Raw AI response:")
                print(ai_response)
                continue

            # Add the AI's response to the conversation history
            conversation_history.append({"role": "assistant", "content": ai_response})

            # Display only the narration to the user
            print(f"Dungeon Master: {SOFT_REDDISH_ORANGE}{narration}{RESET_COLOR}")

            # Process actions
            for action in actions:
                if action["action"] == "updatePlayerInfo":
                    player_name = party_data["partyMembers"][0].lower().replace(" ", "_")
                    changes = action["parameters"]["changes"]
                    try:
                        updated_player_info = update_player_info.update_player(player_name, changes)
                        if updated_player_info:
                            player_info = updated_player_info
                            print(f"DEBUG: Player info updated successfully")
                    except Exception as e:
                        print(f"ERROR: Failed to update player info: {str(e)}")

                elif action["action"] == "updateNPCInfo":
                    npc_name = action["parameters"]["npcName"]
                    changes = action["parameters"]["changes"]
                    try:
                        updated_npc_info = update_npc_info.update_npc(npc_name, changes)
                        if updated_npc_info:
                            # Update the NPC info in your data structure if needed
                            print(f"DEBUG: NPC {npc_name} info updated successfully")
                    except Exception as e:
                        print(f"ERROR: Failed to update NPC info: {str(e)}")

                elif action["action"] == "updateEncounter":
                    encounter_id = action["parameters"]["encounterId"]
                    changes = action["parameters"]["changes"]
                    try:
                        updated_encounter_data = update_encounter.update_encounter(encounter_id, changes)
                        if updated_encounter_data:
                            encounter_data = updated_encounter_data
                            print(f"DEBUG: Encounter {encounter_id} updated successfully")
                    except Exception as e:
                        print(f"ERROR: Failed to update encounter: {str(e)}")

                elif action["action"] == "exit":
                    print("The combat has ended.")
                    
                    # Calculate XP and process end-of-combat tasks
                    xp_narrative, xp_awarded = calculate_xp()
                    print(f"XP Awarded: {xp_narrative}")

                    # Add XP information to the conversation history
                    conversation_history.append({"role": "system", "content": f"XP Awarded: {xp_narrative}"})

                    # Update character's XP
                    xp_update_response = f"Update the character's experience points. XP Awarded: {xp_awarded}"
                    updated_data = update_json_schema(xp_update_response, player_info, encounter_data, party_tracker_data)
                    if updated_data:
                        player_info, updated_encounter_data, updated_party_tracker = updated_data
                    
                    # Generate dialogue summary
                    dialogue_summary = summarize_dialogue(conversation_history, location_data, party_data)
                    
                    # Save the final conversation history
                    with open(conversation_history_file, "w") as file:
                        json.dump(conversation_history, file, indent=2)

                    print("Combat encounter closed. Exiting combat simulation.")
                    return dialogue_summary, updated_player_info

            # Save the updated conversation history to the JSON file after each turn
            with open(conversation_history_file, "w") as file:
                json.dump(conversation_history, file, indent=2)

            # Get player name from party tracker
            player_name = party_data["partyMembers"][0]  # Assuming the first member is the player

            # Load player data
            player_file = f"{player_name.lower().replace(' ', '_')}.json"
            with open(player_file, "r") as file:
                player_info = json.load(file)

            # Extract player stats
            current_hp = player_info["hitPoints"]
            max_hp = player_info["maxHitPoints"]
            current_xp = player_info.get("experience_points", 0)
            next_level_xp = player_info.get("exp_required_for_next_level", 0)

            # Format player stats with new colors
            stats_display = f"{LIGHT_OFF_GREEN}[HP:{current_hp}/{max_hp}][XP:{current_xp}/{next_level_xp}]{RESET_COLOR}"
            player_name_display = f"{SOLID_GREEN}{player_name}{RESET_COLOR}"

            # Get user input with formatted stats and name
            user_input_text = input(f"{stats_display} {player_name_display}: ")

            # Prepare hitpoints information for all creatures
            hitpoints_info = []

            # Player hitpoints (from player_info)
            player_name = player_info.get('name', 'Player')
            player_hitpoints = player_info.get('hitPoints', 'Unknown')
            player_maxhitpoints = player_info.get('maxHitPoints', 'Unknown')
            hitpoints_info.append(f"{player_name}'s current hitpoints: {player_hitpoints}/{player_maxhitpoints}")

            # Monster and NPC hitpoints from encounter data
            for creature in encounter_data["creatures"]:
                if creature["type"] != "player":  # Skip player character as it's already added
                    creature_name = creature.get("name", "Unknown Creature")
                    creature_hitpoints = creature.get("currentHitPoints", "Unknown")
                    creature_maxhitpoints = creature.get("maxHitPoints", "Unknown")
                    hitpoints_info.append(f"{creature_name}'s current hitpoints: {creature_hitpoints}/{creature_maxhitpoints}")

            # Join all hitpoints information
            all_hitpoints_info = "\n".join(hitpoints_info)

            user_input_with_note = f"""Dungeon Master Note: Respond with valid JSON containing a 'narration' field and an 'actions' array. Use 'updatePlayerInfo', 'updateNPCInfo', and 'updateEncounter' actions to record changes in hit points, status, or conditions for any creature in the encounter. Include the 'exit' action when the encounter ends. Ensure your 'actions' array matches all changes described in your 'narration' field. Ask the player to roll for all of their activities unless they say otherwise. Take independent actions and dice rolls for all monster and NPC actions, making updates as necessary. Remember to roleplay NPCs according to their profiles and maintain a turn-based approach, guiding the player through actions one at a time. 

            Current hitpoints for all creatures:
            {all_hitpoints_info}

            Player: {user_input_text}"""
            conversation_history.append({"role": "user", "content": user_input_with_note})

            # Save the updated conversation history to the JSON file
            with open(conversation_history_file, "w") as file:
                json.dump(conversation_history, file, indent=2)

    except Exception as e:
        print(f"ERROR in run_combat_simulation: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Combat simulation failed: {str(e)}", None

def main():
    print("DEBUG: Starting main function")
    # Read the party tracker data from the JSON file
    with open("party_tracker.json", "r") as file:
        party_tracker_data = json.load(file)
    print(f"DEBUG: Loaded party_tracker_data: {party_tracker_data}")

    # Extract the active combat encounter from the party tracker data
    active_combat_encounter = party_tracker_data["worldConditions"].get("activeCombatEncounter")
    print(f"DEBUG: Active combat encounter: {active_combat_encounter}")

    if not active_combat_encounter:
        print("No active combat encounter located.")
        return

    # Construct the file path for the encounter JSON file
    json_file = f"encounter_{active_combat_encounter}.json"
    print(f"DEBUG: Encounter file: {json_file}")

    # Load location data
    current_location_id = party_tracker_data["worldConditions"]["currentLocationId"]
    current_area_id = get_current_area_id()
    area_file = f"{current_area_id}.json"
    
    print(f"DEBUG: Current location ID: {current_location_id}")
    print(f"DEBUG: Current area ID: {current_area_id}")
    print(f"DEBUG: Attempting to load area file: {area_file}")
    
    try:
        with open(area_file, "r") as file:
            area_data = json.load(file)
        print(f"DEBUG: Successfully loaded area data")
        print(f"DEBUG: Area data contents: {json.dumps(area_data, indent=2)}")
    except FileNotFoundError:
        print(f"ERROR: Area file {area_file} not found")
        return
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in {area_file}")
        return
    
    location_data = next((loc for loc in area_data["locations"] if loc["locationId"] == current_location_id), None)
    
    if not location_data:
        print(f"ERROR: Failed to find location {current_location_id} in {area_file}")
        print(f"DEBUG: Available location IDs: {[loc['locationId'] for loc in area_data['locations']]}")
        return

    print(f"DEBUG: Location data: {json.dumps(location_data, indent=2)}")

    # Run the combat simulation
    dialogue_summary, updated_player_info, updated_encounter_data, updated_party_tracker = run_combat_simulation(active_combat_encounter, party_tracker_data, location_data)

    print("Combat simulation completed.")
    print(f"Dialogue Summary: {dialogue_summary}")

    # Save the updated party tracker data
    with open("party_tracker.json", "w") as file:
        json.dump(updated_party_tracker, file, indent=2)