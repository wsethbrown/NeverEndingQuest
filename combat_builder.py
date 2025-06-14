import json
import random
import sys
import os
import subprocess
from termcolor import colored
import logging
import shutil
from module_path_manager import ModulePathManager

logging.basicConfig(filename='combat_builder.log', level=logging.DEBUG)

def clear_json_file(file_path):
    try:
        with open(file_path, "w") as f:
            json.dump([], f)
        print(colored(f"Cleared contents of {file_path}", "green"))
    except Exception as e:
        print(colored(f"Error clearing {file_path}: {str(e)}", "red"))

def clear_combat_history_files():
    files_to_clear = [
        "combat_conversation_history.json",
        "second_model_history.json",
        "third_model_history.json"
    ]
    
    for file in files_to_clear:
        clear_json_file(file)

def format_type_name(name):
    return name.lower().replace(' ', '_')

def load_json(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            data = json.load(file)
        logging.debug(f"Successfully loaded JSON from {file_name}")
        return data
    except FileNotFoundError:
        logging.error(f"Error: File {file_name} not found.")
        print(colored(f"Error: File {file_name} not found.", "red"))
        return None
    except json.JSONDecodeError:
        logging.error(f"Error: Invalid JSON in {file_name}.")
        print(colored(f"Error: Invalid JSON in {file_name}.", "red"))
        return None

def backup_player_file(player_file):
    backup_file = f"{player_file}.bak"
    try:
        shutil.copy2(player_file, backup_file)
        logging.debug(f"Backed up player file to {backup_file}")
    except Exception as e:
        logging.error(f"Failed to backup player file: {str(e)}")

def save_json(file_name, data):
    try:
        with open(file_name, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(colored(f"Error saving to {file_name}: {str(e)}", "red"))
        return False

def get_current_area_id():
    with open("party_tracker.json", "r", encoding="utf-8") as file:
        party_tracker = json.load(file)
    return party_tracker["worldConditions"]["currentAreaId"]

def get_current_location():
    party_tracker = load_json("party_tracker.json")
    if not party_tracker:
        print(colored("Error: Failed to load party tracker.", "red"))
        return None
    return party_tracker.get("worldConditions", {}).get("currentLocationId")

def get_next_encounter_number(location):
    party_tracker = load_json("party_tracker.json")
    if not party_tracker:
        print(colored("Error: Failed to load party tracker.", "red"))
        return 1
    
    current_area_id = get_current_area_id()
    path_manager = ModulePathManager()
    location_data = load_json(path_manager.get_area_path(current_area_id))
    if not location_data:
        print(colored(f"Error: Failed to load location data for {current_area_id}.", "red"))
        return 1
    
    location_info = next((loc for loc in location_data.get("locations", []) if loc.get("locationId") == location), None)
    if not location_info:
        print(colored(f"Error: Location {location} not found in location data.", "red"))
        return 1
    
    existing_encounters = [enc for enc in location_info.get("encounters", []) if enc.get("encounterId", "").startswith(f"{location}-E")]
    return len(existing_encounters) + 1

def update_party_tracker(encounter_id):
    party_tracker = load_json("party_tracker.json")
    if not party_tracker:
        return False
    
    party_tracker["worldConditions"]["activeCombatEncounter"] = encounter_id
    if save_json("party_tracker.json", party_tracker):
        return encounter_id
    return False

def load_or_create_monster(monster_type):
    formatted_monster_type = format_type_name(monster_type)
    path_manager = ModulePathManager()
    monster_file = path_manager.get_monster_path(monster_type)
    monster_data = load_json(monster_file)
    if not monster_data:
        print(colored(f"DEBUG: Monster loading ({monster_type}) - attempting creation", "yellow"))
        result = subprocess.run(["python", "monster_builder.py", monster_type], capture_output=True, text=True)
        if result.returncode == 0:
            print(colored(f"DEBUG: Monster builder ({monster_type}) - PASS", "green"))
            if os.path.exists(monster_file):
                monster_data = load_json(monster_file)
                if not monster_data:
                    print(colored(f"Error: Failed to load newly created monster data for {monster_type}", "red"))
                    return None
            else:
                print(colored(f"Error: Monster file {monster_file} was not created", "red"))
                return None
        else:
            print(colored(f"DEBUG: Monster builder ({monster_type}) - FAIL", "red"))
            return None
    return monster_data

def load_or_create_npc(npc_name):
    formatted_npc_name = format_type_name(npc_name)
    path_manager = ModulePathManager()
    npc_file = path_manager.get_character_path(npc_name)
    npc_data = load_json(npc_file)
    if not npc_data:
        print(colored(f"DEBUG: NPC loading ({npc_name}) - attempting creation", "yellow"))
        result = subprocess.run(["python", "npc_builder.py", npc_name], capture_output=True, text=True)
        if result.returncode == 0:
            print(colored(f"DEBUG: NPC builder ({npc_name}) - PASS", "green"))
            if os.path.exists(npc_file):
                npc_data = load_json(npc_file)
                if not npc_data:
                    print(colored(f"Error: Failed to load newly created NPC data for {npc_name}", "red"))
                    return None
            else:
                print(colored(f"Error: NPC file {npc_file} was not created", "red"))
                return None
        else:
            print(colored(f"DEBUG: NPC builder ({npc_name}) - FAIL", "red"))
            return None
    return npc_data

def generate_encounter(encounter_data):
    location = get_current_location()
    if not location:
        return None
    
    encounter_number = get_next_encounter_number(location)
    encounter_id = f"{location}-E{encounter_number}"
    
    encounter = {
        "encounterId": encounter_id,
        "creatures": []
    }

    if "encounterSummary" in encounter_data:
        encounter["encounterSummary"] = encounter_data["encounterSummary"]

    # Add player
    path_manager = ModulePathManager()
    player_file = path_manager.get_character_path(encounter_data['player'])
    logging.debug(f"Attempting to load player data from {player_file}")
    
    backup_player_file(player_file)
    player_data = load_json(player_file)
    
    if not player_data:
        logging.error(f"Failed to load player data from {player_file}")
        print(colored(f"Error: Failed to load player data from {player_file}", "red"))
        # Attempt to load from backup
        backup_file = f"{player_file}.bak"
        player_data = load_json(backup_file)
        if player_data:
            logging.info(f"Loaded player data from backup file {backup_file}")
            print(colored(f"Loaded player data from backup file {backup_file}", "yellow"))
        else:
            return None

    logging.debug(f"Loaded player data: {json.dumps(player_data, indent=2)}")

    player = {
        "name": player_data["name"],
        "type": "player",
        "initiative": random.randint(1, 20),
        "status": player_data.get("status", "alive"),
        "conditions": player_data.get("condition_affected", []),
        "actions": {"actionType": "", "target": ""},
        "currentHitPoints": player_data["hitPoints"],
        "maxHitPoints": player_data["maxHitPoints"],
        "armorClass": player_data["armorClass"]
    }
    encounter["creatures"].append(player)

    # Add monsters
    monster_counts = {}
    for monster_type in encounter_data["monsters"]:
        formatted_monster_type = format_type_name(monster_type)
        monster_data = load_or_create_monster(monster_type)
        if not monster_data:
            return None

        monster_counts[formatted_monster_type] = monster_counts.get(formatted_monster_type, 0) + 1
        
        if monster_counts[formatted_monster_type] > 1:
            monster_name = f"{monster_data['name']}_{monster_counts[formatted_monster_type]}"
        else:
            monster_name = monster_data['name']

        monster = {
            "name": monster_name,
            "type": "enemy",
            "monsterType": formatted_monster_type,
            "initiative": random.randint(1, 20),
            "status": "alive",
            "conditions": [],
            "actions": {"actionType": "", "target": ""},
            "currentHitPoints": monster_data["hitPoints"],
            "maxHitPoints": monster_data["hitPoints"]
        }
        encounter["creatures"].append(monster)

    # Add NPCs
    npc_counts = {}
    for npc_name in encounter_data.get("npcs", []):
        formatted_npc_type = format_type_name(npc_name)
        npc_data = load_or_create_npc(npc_name)
        if not npc_data:
            return None

        npc_counts[formatted_npc_type] = npc_counts.get(formatted_npc_type, 0) + 1
        
        if npc_counts[formatted_npc_type] > 1:
            npc_full_name = f"{npc_data['name']}_{npc_counts[formatted_npc_type]}"
        else:
            npc_full_name = npc_data['name']

        npc = {
            "name": npc_full_name,
            "type": "npc",
            "npcType": formatted_npc_type,
            "initiative": random.randint(1, 20),
            "status": npc_data.get("status", "alive"),
            "conditions": npc_data.get("condition_affected", []),
            "actions": {"actionType": "", "target": ""},
            "currentHitPoints": npc_data.get("hitPoints", 10),
            "maxHitPoints": npc_data.get("maxHitPoints", 10),
            "armorClass": npc_data.get("armorClass", 10)
        }
        # Add the NPC to the encounter's creatures array
        encounter["creatures"].append(npc)

    return encounter

def main():
    logging.debug("Starting combat encounter creation")
    clear_combat_history_files()
    
    # Read input from stdin
    storyteller_input = sys.stdin.read()

    try:
        # Parse the JSON input
        input_data = json.loads(storyteller_input)

        # Extract the encounter data directly from the input
        encounter_data = input_data["parameters"]

        if "player" not in encounter_data or "monsters" not in encounter_data:
            print(colored("Error: Invalid encounter data format. 'player' and 'monsters' are required.", "red"))
            return

        # NPCs are optional, so we don't check for their presence

    except json.JSONDecodeError:
        print(colored("Error: Invalid JSON format in storyteller input.", "red"))
        return
    except KeyError as e:
        print(colored(f"Error: Missing key in JSON structure: {e}", "red"))
        return

    encounter = generate_encounter(encounter_data)
    
    if encounter:
        encounter_file = f"encounter_{encounter['encounterId']}.json"
        logging.debug(f"Saving encounter data: {json.dumps(encounter, indent=2)}")
        if save_json(encounter_file, encounter):
            logging.info(f"Encounter successfully built and saved to {encounter_file}")
            print(colored(f"Encounter successfully built and saved to {encounter_file}", "green"))
            
            updated_encounter_id = update_party_tracker(encounter['encounterId'])
            if updated_encounter_id:
                logging.info(f"Party tracker updated with new combat encounter ID: {updated_encounter_id}")
                print(colored(f"Party tracker updated with new combat encounter ID: {updated_encounter_id}", "green"))
            else:
                logging.error("Failed to update party tracker.")
                print(colored("Failed to update party tracker.", "red"))
        else:
            logging.error(f"Failed to save encounter to {encounter_file}")
            print(colored(f"Error: Failed to save encounter to {encounter_file}", "red"))
    else:
        logging.error("Failed to generate encounter due to previous errors.")
        print(colored("Error: Failed to generate encounter due to previous errors.", "red"))

if __name__ == "__main__":
    main()