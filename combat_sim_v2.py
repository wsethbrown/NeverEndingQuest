import json
import os
import time
from xp import main as calculate_xp
from openai import OpenAI
# Import model configurations from config.py
from config import (
    OPENAI_API_KEY,
    COMBAT_MAIN_MODEL,
    # COMBAT_SCHEMA_UPDATER_MODEL is not directly used here for a client call,
    # but if it were, it would be imported.
    COMBAT_DIALOGUE_SUMMARY_MODEL
)
import update_player_info
import update_npc_info
import update_encounter
import update_party_tracker

# Updated color constants
SOLID_GREEN = "\033[38;2;0;180;0m"
LIGHT_OFF_GREEN = "\033[38;2;100;180;100m"
SOFT_REDDISH_ORANGE = "\033[38;2;204;102;0m"
RESET_COLOR = "\033[0m"

# Temperature
TEMPERATURE = 1

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

conversation_history_file = "combat_conversation_history.json"
second_model_history_file = "second_model_history.json"
third_model_history_file = "third_model_history.json"

# Note: SOFT_REDDISH_ORANGE and RESET_COLOR were defined twice, keeping one set.
# Note: conversation_history_file, second_model_history_file, third_model_history_file were defined twice.

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
            npc_name = creature['name'] # Assuming name is directly usable or formatted in update_npc
            npc_changes = "Update NPC status after combat."
            update_npc_info.update_npc(npc_name, npc_changes)

    # Update party tracker: remove active combat encounter
    if 'worldConditions' in party_tracker_data and 'activeCombatEncounter' in party_tracker_data['worldConditions']:
        party_tracker_data['worldConditions']['activeCombatEncounter'] = ""

    # Save the updated party_tracker.json file
    with open("party_tracker.json", "w") as file:
        json.dump(party_tracker_data, file, indent=2)

    return updated_player_info, updated_encounter_data, party_tracker_data

def summarize_dialogue(conversation_history_param, location_data, party_tracker_data): # Renamed conversation_history
    print("DEBUG: Activating the third model...")

    dialogue_summary_prompt = [
        {"role": "system", "content": "Your task is to provide a concise summary of the combat encounter in the world's most popular 5th Edition roleplayign game dialogue between the dungeon master running the combat encounter and the player. Focus on capturing the key events, actions, and outcomes of the encounter. Be sure to include the experience points awarded, which will be provided in the conversation history. The summary should be written in a narrative style suitable for presenting to the main dungeon master. Include in your summary any defeated monsters or corpses left behind after combat."},
        {"role": "user", "content": json.dumps(conversation_history_param)}
    ]

    # Generate dialogue summary
    response = client.chat.completions.create(
        model=COMBAT_DIALOGUE_SUMMARY_MODEL, # Use imported model
        temperature=TEMPERATURE,
        messages=dialogue_summary_prompt
    )

    dialogue_summary = response.choices[0].message.content.strip()

    current_location_id = party_tracker_data["worldConditions"]["currentLocationId"]
    print(f"DEBUG: Current location ID: {current_location_id}")

    if location_data and location_data.get("locationId") == current_location_id:
        encounter_id = party_tracker_data["worldConditions"]["activeCombatEncounter"]
        new_encounter = {
            "encounterId": encounter_id,
            "summary": dialogue_summary,
            "impact": "To be determined",
            "worldConditions": {
                "year": int(party_tracker_data["worldConditions"]["year"]),
                "month": party_tracker_data["worldConditions"]["month"],
                "day": int(party_tracker_data["worldConditions"]["day"]),
                "time": party_tracker_data["worldConditions"]["time"]
            }
        }
        if "encounters" not in location_data:
            location_data["encounters"] = []
        location_data["encounters"].append(new_encounter)
        if not location_data.get("adventureSummary"):
            location_data["adventureSummary"] = dialogue_summary
        else:
            location_data["adventureSummary"] += f"\n\n{dialogue_summary}"

        current_area_id = get_current_area_id()
        area_file = f"{current_area_id}.json"
        with open(area_file, "r") as file:
            area_data = json.load(file)
        for i, loc in enumerate(area_data["locations"]):
            if loc["locationId"] == current_location_id:
                area_data["locations"][i] = location_data
                break
        with open(area_file, "w") as file:
            json.dump(area_data, file, indent=2)
        print(f"DEBUG: Encounter {encounter_id} added to {area_file}.")

        conversation_history_param.append({"role": "assistant", "content": f"Combat Summary: {dialogue_summary}"})
        conversation_history_param.append({"role": "user", "content": "The combat has concluded. What would you like to do next?"})

        print(f"DEBUG: Attempting to write to file: {conversation_history_file}")
        try:
            with open(conversation_history_file, "w") as file:
                json.dump(conversation_history_param, file, indent=2)
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
    with open(f"encounter_{encounter_id}.json", "r") as file:
        encounter_data = json.load(file)
    print(f"Updating encounter {encounter_id} with changes: {changes}")
    # Placeholder for actual update logic
    with open(f"encounter_{encounter_id}.json", "w") as file:
        json.dump(encounter_data, file, indent=2)
    return encounter_data

def run_combat_simulation(encounter_id, party_data, location_data_param): # Renamed location_data
    # Using global for these history lists as they are modified and saved globally
    global conversation_history, second_model_history, third_model_history

    print(f"DEBUG: Starting combat simulation for encounter {encounter_id}")

    with open("party_tracker.json", "r") as file:
        party_tracker_data_local = json.load(file) # Use a local var for party_tracker

    try:
        if not location_data_param:
            print(f"ERROR: Invalid location data. Contents: {location_data_param}")
            return "Combat simulation failed due to missing location data", None

        location_info = location_data_param

        conversation_history = [
            {"role": "system", "content": read_prompt_from_file('combat_sim_prompt.txt')},
            {"role": "system", "content": f"Current Combat Encounter: {encounter_id}"},
            {"role": "system", "content": ""},
            {"role": "system", "content": ""},
            {"role": "system", "content": ""}
        ]
        second_model_history = []
        third_model_history = []

        json_file_path = f"encounter_{encounter_id}.json" # Renamed
        with open(json_file_path, "r") as file:
            encounter_data_local = json.load(file) # Use local var

        player_info_local = None # Use local var
        monster_templates = {}
        npc_templates = {}

        for creature in encounter_data_local["creatures"]:
            if creature["type"] == "player":
                player_name = creature["name"].lower().replace(" ", "_")
                player_file = f"{player_name}.json"
                with open(player_file, "r") as file:
                    player_info_local = json.load(file)
            elif creature["type"] == "enemy":
                monster_type = creature["monsterType"]
                if monster_type not in monster_templates:
                    monster_file = f"{monster_type}.json"
                    with open(monster_file, "r") as file:
                        monster_templates[monster_type] = json.load(file)
            elif creature["type"] == "npc":
                # Ensure npc_name is correctly formatted for file access
                npc_file_name_part = creature["name"].lower().replace(" ", "_").split('_')[0] # Handle names like "NPC_1"
                npc_file = f"{npc_file_name_part}.json"
                if npc_file_name_part not in npc_templates: # Check against the base name
                    with open(npc_file, "r") as file:
                        npc_templates[npc_file_name_part] = json.load(file)


        conversation_history[2]["content"] = f"Player Character:\n{json.dumps({k: v for k, v in player_info_local.items() if k not in ['hitpoints', 'maxhitpoints']}, indent=2)}"
        conversation_history[3]["content"] = f"Monster Templates:\n{json.dumps(monster_templates, indent=2)}"
        conversation_history[4]["content"] = f"Location:\n{json.dumps(location_info, indent=2)}"
        conversation_history.append({"role": "system", "content": f"NPC Templates:\n{json.dumps(npc_templates, indent=2)}"})
        conversation_history.append({"role": "system", "content": f"Encounter Details:\n{json.dumps(encounter_data_local, indent=2)}"})

        while True:
            response = client.chat.completions.create(
                model=COMBAT_MAIN_MODEL, # Use imported model
                temperature=TEMPERATURE,
                messages=conversation_history
            )
            ai_response = response.choices[0].message.content.strip()

            if not is_valid_json(ai_response):
                print("DEBUG: Invalid JSON response from AI. Requesting a new response.")
                conversation_history.append({
                    "role": "user",
                    "content": "Your previous response was not a valid JSON object with 'narration' and 'actions' fields. Please provide a valid JSON response."
                })
                continue

            try:
                parsed_response = json.loads(ai_response)
                narration = parsed_response["narration"]
                actions = parsed_response["actions"]
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON parsing error: {str(e)}")
                print("DEBUG: Raw AI response:")
                print(ai_response)
                continue

            conversation_history.append({"role": "assistant", "content": ai_response})
            print(f"Dungeon Master: {SOFT_REDDISH_ORANGE}{narration}{RESET_COLOR}")

            for action in actions:
                if action["action"] == "updatePlayerInfo":
                    player_name_for_update = party_data["partyMembers"][0].lower().replace(" ", "_")
                    changes = action["parameters"]["changes"]
                    try:
                        updated_player_info_action = update_player_info.update_player(player_name_for_update, changes)
                        if updated_player_info_action:
                            player_info_local = updated_player_info_action # Update local player_info
                            print(f"DEBUG: Player info updated successfully")
                    except Exception as e:
                        print(f"ERROR: Failed to update player info: {str(e)}")

                elif action["action"] == "updateNPCInfo":
                    npc_name_for_update = action["parameters"]["npcName"]
                    changes = action["parameters"]["changes"]
                    try:
                        updated_npc_info_action = update_npc_info.update_npc(npc_name_for_update, changes)
                        if updated_npc_info_action:
                            print(f"DEBUG: NPC {npc_name_for_update} info updated successfully")
                    except Exception as e:
                        print(f"ERROR: Failed to update NPC info: {str(e)}")

                elif action["action"] == "updateEncounter":
                    encounter_id_for_update = action["parameters"]["encounterId"]
                    changes = action["parameters"]["changes"]
                    try:
                        updated_encounter_data_action = update_encounter.update_encounter(encounter_id_for_update, changes)
                        if updated_encounter_data_action:
                            encounter_data_local = updated_encounter_data_action # Update local encounter_data
                            print(f"DEBUG: Encounter {encounter_id_for_update} updated successfully")
                    except Exception as e:
                        print(f"ERROR: Failed to update encounter: {str(e)}")

                elif action["action"] == "exit":
                    print("The combat has ended.")
                    xp_narrative, xp_awarded = calculate_xp()
                    print(f"XP Awarded: {xp_narrative}")
                    conversation_history.append({"role": "system", "content": f"XP Awarded: {xp_narrative}"})
                    xp_update_response = f"Update the character's experience points. XP Awarded: {xp_awarded}"
                    
                    # Pass the most current party_tracker_data_local to update_json_schema
                    updated_data_tuple = update_json_schema(xp_update_response, player_info_local, encounter_data_local, party_tracker_data_local)
                    if updated_data_tuple:
                        player_info_local, _, _ = updated_data_tuple # Unpack, encounter and party_tracker are updated on disk

                    dialogue_summary_result = summarize_dialogue(conversation_history, location_data_param, party_tracker_data_local) # Pass local party_tracker

                    with open(conversation_history_file, "w") as file:
                        json.dump(conversation_history, file, indent=2)
                    print("Combat encounter closed. Exiting combat simulation.")
                    return dialogue_summary_result, player_info_local # Return updated local player_info

            with open(conversation_history_file, "w") as file:
                json.dump(conversation_history, file, indent=2)

            player_name_display = party_data["partyMembers"][0]
            player_file_for_stats = f"{player_name_display.lower().replace(' ', '_')}.json"
            with open(player_file_for_stats, "r") as file:
                player_info_for_stats = json.load(file) # Load fresh for stats display

            current_hp = player_info_for_stats["hitPoints"]
            max_hp = player_info_for_stats["maxHitPoints"]
            current_xp = player_info_for_stats.get("experience_points", 0)
            next_level_xp = player_info_for_stats.get("exp_required_for_next_level", 0)

            stats_display = f"{LIGHT_OFF_GREEN}[HP:{current_hp}/{max_hp}][XP:{current_xp}/{next_level_xp}]{RESET_COLOR}"
            player_name_colored = f"{SOLID_GREEN}{player_name_display}{RESET_COLOR}"
            user_input_text = input(f"{stats_display} {player_name_colored}: ")

            hitpoints_info_parts = []
            player_name_hp = player_info_local.get('name', 'Player')
            player_hp = player_info_local.get('hitPoints', 'Unknown')
            player_max_hp = player_info_local.get('maxHitPoints', 'Unknown')
            hitpoints_info_parts.append(f"{player_name_hp}'s current hitpoints: {player_hp}/{player_max_hp}")

            for creature in encounter_data_local["creatures"]:
                if creature["type"] != "player":
                    creature_name = creature.get("name", "Unknown Creature")
                    creature_hp = creature.get("currentHitPoints", "Unknown")
                    creature_max_hp = creature.get("maxHitPoints", "Unknown")
                    hitpoints_info_parts.append(f"{creature_name}'s current hitpoints: {creature_hp}/{creature_max_hp}")
            all_hitpoints_info = "\n".join(hitpoints_info_parts)

            user_input_with_note = f"""Dungeon Master Note: Respond with valid JSON containing a 'narration' field and an 'actions' array. Use 'updatePlayerInfo', 'updateNPCInfo', and 'updateEncounter' actions to record changes in hit points, status, or conditions for any creature in the encounter. Include the 'exit' action when the encounter ends. Ensure your 'actions' array matches all changes described in your 'narration' field. Ask the player to roll for all of their activities unless they say otherwise. Take independent actions and dice rolls for all monster and NPC actions, making updates as necessary. Remember to roleplay NPCs according to their profiles and maintain a turn-based approach, guiding the player through actions one at a time. 

            Current hitpoints for all creatures:
            {all_hitpoints_info}

            Player: {user_input_text}"""
            conversation_history.append({"role": "user", "content": user_input_with_note})

            with open(conversation_history_file, "w") as file:
                json.dump(conversation_history, file, indent=2)

    except Exception as e:
        print(f"ERROR in run_combat_simulation: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Combat simulation failed: {str(e)}", None


def main(): # This main is for standalone testing, ensure return values match if used.
    print("DEBUG: Starting main function in combat_sim_v2")
    with open("party_tracker.json", "r") as file:
        party_tracker_main = json.load(file) # Use local var
    print(f"DEBUG: Loaded party_tracker_main: {party_tracker_main}")

    active_combat_encounter_main = party_tracker_main["worldConditions"].get("activeCombatEncounter") # Use local var
    print(f"DEBUG: Active combat encounter: {active_combat_encounter_main}")

    if not active_combat_encounter_main:
        print("No active combat encounter located.")
        return

    json_file_path_main = f"encounter_{active_combat_encounter_main}.json" # Use local var
    print(f"DEBUG: Encounter file: {json_file_path_main}")

    current_location_id_main = party_tracker_main["worldConditions"]["currentLocationId"] # Use local var
    current_area_id_main = get_current_area_id() # Use local var
    area_file_main = f"{current_area_id_main}.json" # Use local var

    print(f"DEBUG: Current location ID: {current_location_id_main}")
    print(f"DEBUG: Current area ID: {current_area_id_main}")
    print(f"DEBUG: Attempting to load area file: {area_file_main}")

    try:
        with open(area_file_main, "r") as file:
            area_data_main = json.load(file) # Use local var
        print(f"DEBUG: Successfully loaded area data")
        # print(f"DEBUG: Area data contents: {json.dumps(area_data_main, indent=2)}")
    except FileNotFoundError:
        print(f"ERROR: Area file {area_file_main} not found")
        return
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in {area_file_main}")
        return

    location_data_main = next((loc for loc in area_data_main["locations"] if loc["locationId"] == current_location_id_main), None) # Use local var

    if not location_data_main:
        print(f"ERROR: Failed to find location {current_location_id_main} in {area_file_main}")
        # print(f"DEBUG: Available location IDs: {[loc['locationId'] for loc in area_data_main['locations']]}")
        return

    # print(f"DEBUG: Location data: {json.dumps(location_data_main, indent=2)}")

    # Correctly handle the two return values from run_combat_simulation
    dialogue_summary_main, updated_player_info_main = run_combat_simulation(active_combat_encounter_main, party_tracker_main, location_data_main)

    print("Combat simulation completed.")
    print(f"Dialogue Summary: {dialogue_summary_main}")

    # If updated_party_tracker was intended to be returned and used,
    # it would need to be returned by run_combat_simulation and handled here.
    # For now, party_tracker.json is updated on disk by update_json_schema.
    # We can reload it if needed for further operations in this main().
    # with open("party_tracker.json", "r") as file:
    #     updated_party_tracker_main = json.load(file)
    # with open("party_tracker.json", "w") as file: # This was saving the original, not necessarily updated one
    #     json.dump(updated_party_tracker_main, file, indent=2)


if __name__ == "__main__":
    main()