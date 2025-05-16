import json
from jsonschema import validate, ValidationError
from openai import OpenAI
import time
import re
import copy
# Import model configuration from config.py
from config import OPENAI_API_KEY, ENCOUNTER_UPDATE_MODEL
from campaign_path_manager import CampaignPathManager

# ANSI escape codes
ORANGE = "\033[38;2;255;165;0m"
RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

# Constants
TEMPERATURE = 0.7

client = OpenAI(api_key=OPENAI_API_KEY)

def load_encounter_schema():
    with open("encounter_schema.json", "r") as schema_file:
        return json.load(schema_file)

def update_encounter(encounter_id, changes, max_retries=3):
    # Load the current encounter info and schema
    path_manager = CampaignPathManager()
    with open(f"encounter_{encounter_id}.json", "r") as file:
        encounter_info = json.load(file)

    original_info = copy.deepcopy(encounter_info)  # Keep a copy of the original info
    schema = load_encounter_schema()

    for attempt in range(max_retries):
        # Prepare the prompt for the AI
        prompt = [
            {"role": "system", "content": """You are an assistant that updates encounter information in a 5th Edition roleplaying game. Given the current encounter information and a description of changes, you must return only the updated sections as a JSON object. Do not include unchanged fields. Your response should be a valid JSON object representing only the modified parts of the encounter data. 

Focus only on updating the monster information within the 'creatures' array. Do not modify player or NPC data.

Here's an example of a proper JSON structure for updates:

Input: The orc took 8 damage and is now bloodied.
Output: {
  "creatures": [
    {
      "name": "Orc",
      "type": "enemy",
      "currentHitPoints": 7,
      "status": "alive"
    }
  ]
}

Remember to only update monster information and leave player and NPC data unchanged."""},
            {"role": "user", "content": f"Current encounter info: {json.dumps(encounter_info)}\n\nChanges to apply: {changes}\n\nRespond with ONLY the updated JSON object representing the changed sections of the encounter data, with no additional text or explanation."}
        ]

        # Get AI's response
        response = client.chat.completions.create(
            model=ENCOUNTER_UPDATE_MODEL,
            temperature=TEMPERATURE,
            messages=prompt
        )

        ai_response = response.choices[0].message.content.strip()

        # Write the raw AI response to a debug file
        with open("debug_encounter_update.json", "w") as debug_file:
            json.dump({"raw_ai_response": ai_response}, debug_file, indent=2)

        print(f"{ORANGE}DEBUG: Raw AI response written to debug_encounter_update.json{RESET}")

        # Remove markdown code blocks if present
        ai_response = re.sub(r'```json\n|\n```', '', ai_response)

        try:
            updates = json.loads(ai_response)

            # Apply updates to the encounter_info
            encounter_info = update_nested_dict(encounter_info, updates)

            # Now sync player and NPC information from their respective files
            for creature in encounter_info["creatures"]:
                if creature["type"] == "player":
                    player_file = path_manager.get_player_path(creature['name'].lower().replace(' ', '_'))
                    try:
                        with open(player_file, "r") as file:
                            player_data = json.load(file)
                            # Only sync combat-relevant state
                            creature["currentHitPoints"] = player_data.get("hitPoints", creature.get("currentHitPoints", 0))
                            creature["maxHitPoints"] = player_data.get("maxHitPoints", creature.get("maxHitPoints", 0))
                            creature["status"] = player_data.get("status", creature.get("status", "alive"))
                            creature["conditions"] = player_data.get("condition_affected", [])
                            # Copy armorClass if it exists in player data
                            if "armorClass" in player_data:
                                creature["armorClass"] = player_data["armorClass"]
                    except Exception as e:
                        print(f"{RED}ERROR: Failed to sync player data from {player_file}: {str(e)}{RESET}")
                        
                elif creature["type"] == "npc":
                    npc_name = creature['name'].lower().replace(' ', '_').split('_')[0]
                    npc_file = path_manager.get_npc_path(npc_name)
                    try:
                        with open(npc_file, "r") as file:
                            npc_data = json.load(file)
                            # Only sync combat-relevant state
                            creature["currentHitPoints"] = npc_data.get("hitPoints", creature.get("currentHitPoints", 0))
                            creature["maxHitPoints"] = npc_data.get("maxHitPoints", creature.get("maxHitPoints", 0))
                            creature["status"] = npc_data.get("status", creature.get("status", "alive"))
                            creature["conditions"] = npc_data.get("condition_affected", [])
                            # Copy armorClass if it exists in NPC data
                            if "armorClass" in npc_data:
                                creature["armorClass"] = npc_data["armorClass"]
                    except Exception as e:
                        print(f"{RED}ERROR: Failed to sync NPC data from {npc_file}: {str(e)}{RESET}")

            # Validate the updated info against the schema
            validate(instance=encounter_info, schema=schema)

            # If we reach here, validation was successful
            print(f"{GREEN}DEBUG: Successfully updated and validated encounter info on attempt {attempt + 1}{RESET}")

            # Compare original and updated info
            diff = compare_json(original_info, encounter_info)
            print(f"{ORANGE}DEBUG: Changes made:{RESET}")
            print(json.dumps(diff, indent=2))

            # Save the updated encounter info
            with open(f"encounter_{encounter_id}.json", "w") as file:
                json.dump(encounter_info, file, indent=2)

            print(f"{ORANGE}DEBUG: Encounter {encounter_id} information updated{RESET}")
            return encounter_info

        except json.JSONDecodeError as e:
            print(f"{ORANGE}DEBUG: AI response is not valid JSON. Error: {e}. Retrying...{RESET}")
        except ValidationError as e:
            print(f"{RED}ERROR: Updated info does not match the schema. Error: {e}. Retrying...{RESET}")

        # If we've reached the maximum number of retries, return the original encounter info
        if attempt == max_retries - 1:
            print(f"{RED}ERROR: Failed to update encounter info after {max_retries} attempts. Returning original encounter info.{RESET}")
            return original_info

        # Wait for a short time before retrying
        time.sleep(1)

    # This line should never be reached, but just in case:
    return original_info

def update_nested_dict(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = update_nested_dict(d.get(k, {}), v)
        elif isinstance(v, list):
            if k not in d:
                d[k] = []
            for item in v:
                if isinstance(item, dict):
                    existing = next((i for i in d[k] if i.get('name') == item.get('name')), None)
                    if existing:
                        update_nested_dict(existing, item)
                    else:
                        d[k].append(item)
                else:
                    if item not in d[k]:
                        d[k].append(item)
        else:
            d[k] = v
    return d

def compare_json(old, new):
    diff = {}
    for key in new:
        if key not in old:
            diff[key] = new[key]
        elif old[key] != new[key]:
            if isinstance(new[key], dict):
                nested_diff = compare_json(old[key], new[key])
                if nested_diff:
                    diff[key] = nested_diff
            elif isinstance(new[key], list):
                # This is the original simpler list diffing.
                if key not in diff: # This line was problematic as diff[key] might not be a list
                    diff[key] = [] # Initialize diff[key] as a list if it's not already
                # The original code for list diffing was complex and potentially buggy.
                # A common simple approach if lists differ is just to show the new list.
                # Or, if the AI is meant to return the whole new list if it's changed, then
                # the update_nested_dict should just replace d[k] = v for lists.
                # Given the prompt, AI should return *only modified sections*.
                # If 'creatures' is returned, it's likely the new state of modified creatures.
                # For simplicity and to revert to original intent, if lists are different,
                # we can just indicate the new list.
                if old[key] != new[key]: # A simple check if lists are different
                    diff[key] = new[key] # Store the new list as the difference
            else:
                diff[key] = new[key]
    return diff