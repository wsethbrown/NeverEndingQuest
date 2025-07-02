import json
import random
import sys
import os
import subprocess
from termcolor import colored
import logging
import shutil
from module_path_manager import ModulePathManager
from enhanced_logger import debug, info, warning, error, set_script_name

# Set script name for logging
set_script_name("combat_builder")

logging.basicConfig(filename='modules/logs/combat_builder.log', level=logging.DEBUG)

def clear_json_file(file_path):
    try:
        with open(file_path, "w") as f:
            json.dump([], f)
        print(colored(f"Cleared contents of {file_path}", "green"))
    except Exception as e:
        print(colored(f"Error clearing {file_path}: {str(e)}", "red"))

def clear_combat_history_files():
    files_to_clear = [
        "modules/conversation_history/combat_conversation_history.json",
        "modules/conversation_history/second_model_history.json",
        "modules/conversation_history/third_model_history.json"
    ]
    
    for file in files_to_clear:
        clear_json_file(file)

def format_type_name(name):
    from update_character_info import normalize_character_name
    return normalize_character_name(name)

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
    # Get current module from party tracker for consistent path resolution
    current_module = party_tracker.get("module", "").replace(" ", "_")
    path_manager = ModulePathManager(current_module)
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
    print(f"[COMBAT_BUILDER] Monster load/create: '{monster_type}' -> '{formatted_monster_type}'")
    # Get current module from party tracker for consistent path resolution
    try:
        from encoding_utils import safe_json_load
        party_tracker = safe_json_load("party_tracker.json")
        current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
        path_manager = ModulePathManager(current_module)
    except:
        path_manager = ModulePathManager()  # Fallback to reading from file
    monster_file = path_manager.get_monster_path(monster_type)
    monster_data = load_json(monster_file)
    if not monster_data:
        print(f"[COMBAT_BUILDER] Monster file not found, creating: {monster_file}")
        warning(f"MONSTER_LOADING: Monster loading ({monster_type}) - attempting creation", category="combat_builder")
        result = subprocess.run(["python", "monster_builder.py", monster_type], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[COMBAT_BUILDER] Monster creation successful: {monster_type}")
            info(f"SUCCESS: Monster builder ({monster_type}) - PASS", category="combat_builder")
            if os.path.exists(monster_file):
                monster_data = load_json(monster_file)
                if not monster_data:
                    print(colored(f"Error: Failed to load newly created monster data for {monster_type}", "red"))
                    return None
            else:
                print(colored(f"Error: Monster file {monster_file} was not created", "red"))
                return None
        else:
            print(f"[COMBAT_BUILDER] Monster creation failed: {monster_type}")
            print(f"[COMBAT_BUILDER] Error output: {result.stderr}")
            error(f"FAILURE: Monster builder ({monster_type}) - FAIL", category="combat_builder")
            return None
    else:
        print(f"[COMBAT_BUILDER] Monster loaded from file: {monster_type}")
    return monster_data

def load_or_create_npc(npc_name):
    formatted_npc_name = format_type_name(npc_name)
    print(f"[COMBAT_BUILDER] NPC name normalization: '{npc_name}' -> '{formatted_npc_name}'")
    # Get current module from party tracker for consistent path resolution
    try:
        from encoding_utils import safe_json_load
        party_tracker = safe_json_load("party_tracker.json")
        current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
        path_manager = ModulePathManager(current_module)
    except:
        path_manager = ModulePathManager()  # Fallback to reading from file
    # Use the formatted/normalized name for file path
    npc_file = path_manager.get_character_path(formatted_npc_name)
    npc_data = load_json(npc_file)
    if not npc_data:
        print(f"[COMBAT_BUILDER] NPC file not found, creating: {npc_file}")
        warning(f"NPC_LOADING: NPC loading ({npc_name}) - attempting creation", category="combat_builder")
        # Pass the normalized name to npc_builder.py
        result = subprocess.run(["python", "npc_builder.py", formatted_npc_name], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[COMBAT_BUILDER] NPC creation successful: {npc_name}")
            info(f"SUCCESS: NPC builder ({npc_name}) - PASS", category="combat_builder")
            if os.path.exists(npc_file):
                npc_data = load_json(npc_file)
                if not npc_data:
                    print(colored(f"Error: Failed to load newly created NPC data for {npc_name}", "red"))
                    return None
            else:
                print(colored(f"Error: NPC file {npc_file} was not created", "red"))
                return None
        else:
            print(f"[COMBAT_BUILDER] NPC creation failed: {npc_name}")
            print(f"[COMBAT_BUILDER] Error output: {result.stderr}")
            error(f"FAILURE: NPC builder ({npc_name}) - FAIL", category="combat_builder")
            return None
    else:
        print(f"[COMBAT_BUILDER] NPC loaded from file: {npc_name}")
    return npc_data

def generate_encounter(encounter_data):
    print(f"[COMBAT_BUILDER] Starting encounter generation with data: player={encounter_data.get('player')}, npcs={encounter_data.get('npcs', [])}, monsters={encounter_data.get('monsters', [])}")
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
    # Get current module from party tracker for consistent path resolution
    try:
        from encoding_utils import safe_json_load
        party_tracker = safe_json_load("party_tracker.json")
        current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
        path_manager = ModulePathManager(current_module)
    except:
        path_manager = ModulePathManager()  # Fallback to reading from file
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
        print(f"[COMBAT_BUILDER] Loading/creating monster: {monster_type} -> {formatted_monster_type}")
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
        print(f"[COMBAT_BUILDER] Encounter generated successfully: {encounter['encounterId']}")
        print(f"[COMBAT_BUILDER] Total creatures in encounter: {len(encounter['creatures'])}")
        # Ensure centralized encounters directory exists
        os.makedirs("modules/encounters", exist_ok=True)
        encounter_file = f"modules/encounters/encounter_{encounter['encounterId']}.json"
        logging.debug(f"Saving encounter data: {json.dumps(encounter, indent=2)}")
        if save_json(encounter_file, encounter):
            logging.info(f"Encounter successfully built and saved to {encounter_file}")
            print(colored(f"Encounter successfully built and saved to {encounter_file}", "green"))
            
            print(f"[COMBAT_BUILDER] Updating party tracker with encounter ID: {encounter['encounterId']}")
            updated_encounter_id = update_party_tracker(encounter['encounterId'])
            if updated_encounter_id:
                print(f"[COMBAT_BUILDER] Party tracker update successful")
                logging.info(f"Party tracker updated with new combat encounter ID: {updated_encounter_id}")
                print(colored(f"Party tracker updated with new combat encounter ID: {updated_encounter_id}", "green"))
            else:
                print(f"[COMBAT_BUILDER] Party tracker update failed")
                logging.error("Failed to update party tracker.")
                print(colored("Failed to update party tracker.", "red"))
        else:
            logging.error(f"Failed to save encounter to {encounter_file}")
            print(colored(f"Error: Failed to save encounter to {encounter_file}", "red"))
    else:
        print(f"[COMBAT_BUILDER] Encounter generation failed")
        logging.error("Failed to generate encounter due to previous errors.")
        print(colored("Error: Failed to generate encounter due to previous errors.", "red"))

if __name__ == "__main__":
    main()