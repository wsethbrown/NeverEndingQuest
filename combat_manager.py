"""
Combat Manager Module for DungeonMasterAI

Handles combat encounters between players, NPCs, and monsters.

Features:
- Manages turn-based combat with initiative order
- Processes player actions and AI responses
- Generates combat summaries and experience rewards
- Maintains combat logs for debugging and analysis

Combat Logging System:
- Creates per-encounter logs in the combat_logs/{encounter_id}/ directory
- Generates both timestamped and "latest" versions of each log
- Maintains a combined log of all encounters in all_combat_latest.json
- Filters out system messages for cleaner, more readable logs
"""
import json
import os
import time
import re
from xp import main as calculate_xp
from openai import OpenAI
# Import model configurations from config.py
from config import (
    OPENAI_API_KEY,
    COMBAT_MAIN_MODEL,
    # Use the existing validation model instead of COMBAT_VALIDATION_MODEL
    DM_VALIDATION_MODEL, 
    COMBAT_DIALOGUE_SUMMARY_MODEL
)
import update_player_info
import update_npc_info
import update_encounter
import update_party_tracker
# Import the preroll generator
from generate_prerolls import generate_prerolls
# Import safe JSON functions
from encoding_utils import safe_json_load, safe_json_dump

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

# Create a combat_logs directory if it doesn't exist
os.makedirs("combat_logs", exist_ok=True)

# Constants for chat history generation
HISTORY_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

def get_current_area_id():
    party_tracker = safe_json_load("party_tracker.json")
    if not party_tracker:
        print("ERROR: Failed to load party_tracker.json")
        return None
    return party_tracker["worldConditions"]["currentAreaId"]

def get_location_data(location_id):
    from campaign_path_manager import CampaignPathManager
    path_manager = CampaignPathManager()
    
    current_area_id = get_current_area_id()
    print(f"DEBUG: Current area ID: {current_area_id}")
    area_file = path_manager.get_area_path(current_area_id)
    print(f"DEBUG: Attempting to load area file: {area_file}")

    if not os.path.exists(area_file):
        print(f"ERROR: Area file {area_file} does not exist")
        return None

    area_data = safe_json_load(area_file)
    if not area_data:
        print(f"ERROR: Failed to load area file: {area_file}")
        return None
    print(f"DEBUG: Loaded area data: {json.dumps(area_data, indent=2)}")

    for location in area_data["locations"]:
        if location["locationId"] == location_id:
            print(f"DEBUG: Found location data for ID {location_id}")
            return location

    print(f"ERROR: Location with ID {location_id} not found in area data")
    return None

def read_prompt_from_file(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except Exception as e:
        print(f"ERROR: Failed to read prompt file {filename}: {str(e)}")
        return ""

def load_monster_stats(monster_name):
    # Import the path manager
    from campaign_path_manager import CampaignPathManager
    path_manager = CampaignPathManager()
    
    # Get the correct path for the monster file
    monster_file = path_manager.get_monster_path(monster_name)

    monster_stats = safe_json_load(monster_file)
    if not monster_stats:
        print(f"ERROR: Failed to load monster file: {monster_file}")
    return monster_stats

def load_json_file(file_path):
    data = safe_json_load(file_path)
    if data is None:
        # If file doesn't exist or has invalid JSON, return an empty list
        return []
    return data

def save_json_file(file_path, data):
    try:
        safe_json_dump(data, file_path)
    except Exception as e:
        print(f"ERROR: Failed to save {file_path}: {str(e)}")

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
    except Exception as e:
        print(f"DEBUG: Writing debug output: {str(e)}")

def parse_json_safely(text):
    """Extract and parse JSON from text, handling various formats"""
    # First, try to parse as-is
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract from code block
    try:
        match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except json.JSONDecodeError:
        pass

    # If all else fails, try to find any JSON-like structure
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except json.JSONDecodeError:
        pass

    # If we still can't parse it, raise an exception
    raise json.JSONDecodeError("Unable to parse JSON from the given text", text, 0)

def validate_combat_response(response, encounter_data, user_input, conversation_history=None):
    """
    Validate a combat response for accuracy in HP tracking, combat flow, etc.
    Returns True if valid, or a string with the reason for failure if invalid.
    """
    print("DEBUG: Validating combat response...")
    
    # Load validation prompt from file
    validation_prompt = read_prompt_from_file('combat_validation_prompt.txt')
    
    # Start with validation prompt
    validation_conversation = [
        {"role": "system", "content": validation_prompt}
    ]
    
    # Add previous 3 user/assistant pairs for context
    if conversation_history and len(conversation_history) > 6:
        # Get the last 7 messages (3 pairs + current user input)
        # But exclude the current user input since we'll add it separately
        recent_messages = conversation_history[-7:-1]  # Last 6 messages before current
        
        # Filter to only user/assistant messages (no system messages)
        context_messages = [
            msg for msg in recent_messages 
            if msg["role"] in ["user", "assistant"]
        ][-6:]  # Ensure we only get last 6 (3 pairs)
        
        # Add context header and messages
        validation_conversation.append({
            "role": "system", 
            "content": "=== PREVIOUS COMBAT CONTEXT (last 3 exchanges) ==="
        })
        validation_conversation.extend(context_messages)
    
    # Add current validation data
    validation_conversation.extend([
        {"role": "system", "content": "=== CURRENT VALIDATION DATA ==="},
        {"role": "system", "content": f"Encounter Data:\n{json.dumps(encounter_data, indent=2)}"},
        {"role": "user", "content": f"Player Input: {user_input}"},
        {"role": "assistant", "content": response}
    ])

    max_validation_retries = 3
    for attempt in range(max_validation_retries):
        try:
            validation_result = client.chat.completions.create(
                model=DM_VALIDATION_MODEL,
                temperature=0.3,  # Lower temperature for more consistent validation
                messages=validation_conversation
            )

            validation_response = validation_result.choices[0].message.content.strip()
            
            try:
                validation_json = parse_json_safely(validation_response)
                is_valid = validation_json.get("valid", False)
                reason = validation_json.get("reason", "No reason provided")
                recommendation = validation_json.get("recommendation", "")

                # Log validation results
                with open("combat_validation_log.json", "a") as log_file:
                    log_entry = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "valid": is_valid,
                        "reason": reason,
                        "recommendation": recommendation,
                        "response": response
                    }
                    json.dump(log_entry, log_file)
                    log_file.write("\n")

                if is_valid:
                    print("DEBUG: Combat response validation passed")
                    return True
                else:
                    print(f"DEBUG: Combat response validation failed. Reason: {reason}")
                    if recommendation:
                        return {"reason": reason, "recommendation": recommendation}
                    else:
                        return reason
                    
            except json.JSONDecodeError:
                print(f"DEBUG: Invalid JSON from validation model (Attempt {attempt + 1}/{max_validation_retries})")
                print(f"Problematic response: {validation_response}")
                continue
                
        except Exception as e:
            print(f"DEBUG: Validation error: {str(e)}")
            continue
    
    # If we've exhausted all retries and still don't have a valid result
    print("DEBUG: Validation failed after max retries, assuming response is valid")
    return True

def normalize_encounter_status(encounter_data):
    """Normalizes status values in encounter data to lowercase"""
    if not encounter_data or not isinstance(encounter_data, dict):
        return encounter_data
        
    # Convert status values to lowercase
    for creature in encounter_data.get('creatures', []):
        if 'status' in creature:
            creature['status'] = creature['status'].lower()
    
    return encounter_data

def log_conversation_structure(conversation):
    """Log the structure of the conversation history for debugging"""
    print("\nDEBUG: Conversation Structure:")
    print(f"Total messages: {len(conversation)}")
    
    roles = {}
    for i, msg in enumerate(conversation):
        role = msg.get("role", "unknown")
        content_preview = msg.get("content", "")[:50].replace("\n", " ") + "..."
        roles[role] = roles.get(role, 0) + 1
        print(f"  [{i}] {role}: {content_preview}")
    
    print("Message count by role:")
    for role, count in roles.items():
        print(f"  {role}: {count}")
    print()

def summarize_dialogue(conversation_history_param, location_data, party_tracker_data):
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

        from campaign_path_manager import CampaignPathManager
        path_manager = CampaignPathManager()
        current_area_id = get_current_area_id()
        area_file = path_manager.get_area_path(current_area_id)
        area_data = safe_json_load(area_file)
        if not area_data:
            print(f"ERROR: Failed to load area file: {area_file}")
            return dialogue_summary
        
        for i, loc in enumerate(area_data["locations"]):
            if loc["locationId"] == current_location_id:
                area_data["locations"][i] = location_data
                break
        
        if not safe_json_dump(area_data, area_file):
            print(f"ERROR: Failed to save area file: {area_file}")
        print(f"DEBUG: Encounter {encounter_id} added to {area_file}.")

        conversation_history_param.append({"role": "assistant", "content": f"Combat Summary: {dialogue_summary}"})
        conversation_history_param.append({"role": "user", "content": "The combat has concluded. What would you like to do next?"})

        print(f"DEBUG: Attempting to write to file: {conversation_history_file}")
        if not safe_json_dump(conversation_history_param, conversation_history_file):
            print(f"ERROR: Failed to save conversation history")
        else:
            print("DEBUG: Conversation history saved successfully")
        print("Conversation history updated with encounter summary.")
    else:
        print(f"ERROR: Location {current_location_id} not found in location data or location data is incorrect.")
    return dialogue_summary

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
            npc_name = creature['name'].lower().replace(' ', '_').split('_')[0] # Format for file access
            npc_changes = "Update NPC status after combat."
            update_npc_info.update_npc(npc_name, npc_changes)

    # Update party tracker: store last combat encounter before removing active one
    if 'worldConditions' in party_tracker_data and 'activeCombatEncounter' in party_tracker_data['worldConditions']:
        # Save the encounter ID before clearing it
        last_encounter_id = party_tracker_data["worldConditions"]["activeCombatEncounter"]
        if last_encounter_id:  # Only save if not empty
            party_tracker_data["worldConditions"]["lastCompletedEncounter"] = last_encounter_id
        # Clear the active encounter
        party_tracker_data['worldConditions']['activeCombatEncounter'] = ""

    # Save the updated party_tracker.json file
    if not safe_json_dump(party_tracker_data, "party_tracker.json"):
        print("ERROR: Failed to save party_tracker.json")

    return updated_player_info, updated_encounter_data, party_tracker_data

def generate_chat_history(conversation_history, encounter_id):
    """
    Generate a lightweight combat chat history without system messages
    for a specific encounter ID
    """
    # Create a formatted timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime(HISTORY_TIMESTAMP_FORMAT)

    # Create directory for this encounter if it doesn't exist
    encounter_dir = f"combat_logs/{encounter_id}"
    os.makedirs(encounter_dir, exist_ok=True)

    # Create a unique filename based on encounter ID and timestamp
    output_file = f"{encounter_dir}/combat_chat_{timestamp}.json"

    try:
        # Filter out system messages and keep only user and assistant messages
        chat_history = [msg for msg in conversation_history if msg["role"] != "system"]

        # Write the filtered chat history to the output file
        if not safe_json_dump(chat_history, output_file):
            print(f"ERROR: Failed to save chat history to {output_file}")

        # Print statistics
        system_count = len(conversation_history) - len(chat_history)
        total_count = len(conversation_history)
        user_count = sum(1 for msg in chat_history if msg["role"] == "user")
        assistant_count = sum(1 for msg in chat_history if msg["role"] == "assistant")

        print(f"\n{SOFT_REDDISH_ORANGE}Combat chat history updated!{RESET_COLOR}")
        print(f"Encounter ID: {encounter_id}")
        print(f"System messages removed: {system_count}")
        print(f"User messages: {user_count}")
        print(f"Assistant messages: {assistant_count}")
        print(f"Total messages (including system): {total_count}")
        print(f"Output saved to: {output_file}")

        # Also create/update the latest version of this encounter for easy reference
        latest_file = f"{encounter_dir}/combat_chat_latest.json"
        if not safe_json_dump(chat_history, latest_file):
            print(f"ERROR: Failed to save latest chat history")
        print(f"Latest version also saved to: {latest_file}\n")

        # Save a combined latest file for all encounters as well
        all_latest_file = f"combat_logs/all_combat_latest.json"
        try:
            # Load existing all-combat history if it exists
            if os.path.exists(all_latest_file):
                with open(all_latest_file, "r", encoding="utf-8") as f:
                    all_combat_data = json.load(f)
            else:
                all_combat_data = {}

            # Add or update this encounter's data
            all_combat_data[encounter_id] = {
                "timestamp": timestamp,
                "messageCount": len(chat_history),
                "history": chat_history
            }

            # Write the combined file
            with open(all_latest_file, "w", encoding="utf-8") as f:
                json.dump(all_combat_data, f, indent=2)

        except Exception as e:
            print(f"Error updating combined combat log: {str(e)}")

    except Exception as e:
        print(f"Error generating combat chat history: {str(e)}")

def sync_active_encounter():
    """Sync player and NPC data to the active encounter file if one exists"""
    from campaign_path_manager import CampaignPathManager
    path_manager = CampaignPathManager()
    
    # Check if there's an active combat encounter
    try:
        party_tracker = safe_json_load("party_tracker.json")
        if not party_tracker:
            print("ERROR: Failed to load party_tracker.json")
            return
        
        active_encounter_id = party_tracker.get("worldConditions", {}).get("activeCombatEncounter", "")
        if not active_encounter_id:
            # No active encounter, nothing to sync
            return
            
        # Load the encounter file
        encounter_file = f"encounter_{active_encounter_id}.json"
        encounter_data = safe_json_load(encounter_file)
        if not encounter_data:
            print(f"ERROR: Failed to load encounter file: {encounter_file}")
            return {}
            
        # Track if any changes were made
        changes_made = False
            
        # Update player and NPC data in the encounter
        for creature in encounter_data.get("creatures", []):
            if creature["type"] == "player":
                player_file = path_manager.get_player_path(creature['name'].lower().replace(' ', '_'))
                try:
                    player_data = safe_json_load(player_file)
                    if not player_data:
                        print(f"ERROR: Failed to load player file: {player_file}")
                        # Update combat-relevant fields
                        if creature.get("currentHitPoints") != player_data.get("hitPoints"):
                            creature["currentHitPoints"] = player_data.get("hitPoints")
                            changes_made = True
                        if creature.get("maxHitPoints") != player_data.get("maxHitPoints"):
                            creature["maxHitPoints"] = player_data.get("maxHitPoints")
                            changes_made = True
                        if creature.get("status") != player_data.get("status"):
                            creature["status"] = player_data.get("status")
                            changes_made = True
                        if creature.get("conditions") != player_data.get("condition_affected"):
                            creature["conditions"] = player_data.get("condition_affected", [])
                            changes_made = True
                except Exception as e:
                    print(f"ERROR: Failed to sync player data to encounter: {str(e)}")
                    
            elif creature["type"] == "npc":
                npc_name = creature['name'].lower().replace(' ', '_').split('_')[0]
                npc_file = path_manager.get_npc_path(npc_name)
                try:
                    npc_data = safe_json_load(npc_file)
                    if not npc_data:
                        print(f"ERROR: Failed to load NPC file: {npc_file}")
                    else:
                        # Update combat-relevant fields
                        if creature.get("currentHitPoints") != npc_data.get("hitPoints"):
                            creature["currentHitPoints"] = npc_data.get("hitPoints")
                            changes_made = True
                        if creature.get("maxHitPoints") != npc_data.get("maxHitPoints"):
                            creature["maxHitPoints"] = npc_data.get("maxHitPoints")
                            changes_made = True
                        if creature.get("status") != npc_data.get("status"):
                            creature["status"] = npc_data.get("status")
                            changes_made = True
                        if creature.get("conditions") != npc_data.get("condition_affected"):
                            creature["conditions"] = npc_data.get("condition_affected", [])
                            changes_made = True
                except Exception as e:
                    print(f"ERROR: Failed to sync NPC data to encounter: {str(e)}")
        
        # Save the encounter file if changes were made
        if changes_made:
            if not safe_json_dump(encounter_data, encounter_file):
                print(f"ERROR: Failed to save encounter file: {encounter_file}")
            print(f"Active encounter {active_encounter_id} synced with latest character data")
            
    except Exception as e:
        print(f"ERROR in sync_active_encounter: {str(e)}")

def run_combat_simulation(encounter_id, party_tracker_data, location_info):
   """Main function to run the combat simulation"""
   print(f"DEBUG: Starting combat simulation for encounter {encounter_id}")
   
   # Initialize path manager
   from campaign_path_manager import CampaignPathManager
   path_manager = CampaignPathManager()

   # Initialize conversation history with the original structure
   conversation_history = [
       {"role": "system", "content": read_prompt_from_file('combat_sim_prompt.txt')},
       {"role": "system", "content": f"Current Combat Encounter: {encounter_id}"},
       {"role": "system", "content": ""}, # Will hold player data
       {"role": "system", "content": ""}, # Will hold monster templates
       {"role": "system", "content": ""}, # Will hold location info
   ]
   
   # Initialize secondary model histories
   second_model_history = []
   third_model_history = []
   
   # Save empty histories to files to reset them
   save_json_file(conversation_history_file, conversation_history)
   save_json_file(second_model_history_file, second_model_history)
   save_json_file(third_model_history_file, third_model_history)
   
   # Load encounter data
   json_file_path = f"encounter_{encounter_id}.json"
   try:
       encounter_data = safe_json_load(json_file_path)
       if not encounter_data:
           print(f"ERROR: Failed to load encounter file {json_file_path}")
           return None, None
   except Exception as e:
       print(f"ERROR: Failed to load encounter file {json_file_path}: {str(e)}")
       return None, None
   
   # Initialize data containers
   player_info = None
   monster_templates = {}
   npc_templates = {}
   
   # Extract data for all creatures in the encounter
   for creature in encounter_data["creatures"]:
       if creature["type"] == "player":
           player_name = creature["name"].lower().replace(" ", "_")
           player_file = path_manager.get_player_path(player_name)
           try:
               player_info = safe_json_load(player_file)
               if not player_info:
                   print(f"ERROR: Failed to load player file: {player_file}")
                   return None, None
           except Exception as e:
               print(f"ERROR: Failed to load player file {player_file}: {str(e)}")
               return None, None
       
       elif creature["type"] == "enemy":
           monster_type = creature["monsterType"]
           if monster_type not in monster_templates:
               monster_file = path_manager.get_monster_path(monster_type)
               print(f"DEBUG: Attempting to load monster file: {monster_file}")
               try:
                   monster_data = safe_json_load(monster_file)
                   if monster_data:
                       monster_templates[monster_type] = monster_data
                       print(f"DEBUG: Successfully loaded monster: {monster_type}")
                   else:
                       print(f"ERROR: Failed to load monster file: {monster_file}")
               except FileNotFoundError as e:
                   print(f"ERROR: Monster file not found: {monster_file}")
                   print(f"ERROR: {str(e)}")
                   # Check available files for debugging
                   monster_dir = f"{path_manager.campaign_dir}/monsters"
                   if os.path.exists(monster_dir):
                       print(f"DEBUG: Available monster files in {monster_dir}:")
                       for f in os.listdir(monster_dir):
                           print(f"  - {f}")
                   return None, None
               except json.JSONDecodeError as e:
                   print(f"ERROR: Invalid JSON in monster file {monster_file}: {str(e)}")
                   return None, None
               except Exception as e:
                   print(f"ERROR: Failed to load monster file {monster_file}: {str(e)}")
                   print(f"ERROR: Exception type: {type(e).__name__}")
                   import traceback
                   traceback.print_exc()
                   return None, None
       
       elif creature["type"] == "npc":
           # Ensure npc_name is correctly formatted for file access
           npc_file_name_part = creature["name"].lower().replace(" ", "_").split('_')[0] # Handle names like "NPC_1"
           npc_file = path_manager.get_npc_path(npc_file_name_part)
           if npc_file_name_part not in npc_templates: # Check against the base name
               try:
                   npc_data = safe_json_load(npc_file)
                   if npc_data:
                       npc_templates[npc_file_name_part] = npc_data
                   else:
                       print(f"ERROR: Failed to load NPC file: {npc_file}")
               except Exception as e:
                   print(f"ERROR: Failed to load NPC file {npc_file}: {str(e)}")
   
   # Populate the system messages with JSON data
   conversation_history[2]["content"] = f"Player Character:\n{json.dumps({k: v for k, v in player_info.items() if k not in ['hitpoints', 'maxhitpoints']}, indent=2)}"
   conversation_history[3]["content"] = f"Monster Templates:\n{json.dumps(monster_templates, indent=2)}"
   # Verify that we loaded all necessary data
   if not monster_templates and any(c["type"] == "enemy" for c in encounter_data["creatures"]):
       print("ERROR: No monster templates were loaded!")
       return None, None
   
   print(f"DEBUG: Loaded {len(monster_templates)} monster template(s)")
   for k, v in monster_templates.items():
       print(f"  - {k}: {v.get('name', 'Unknown')}")
   
   conversation_history[4]["content"] = f"Location:\n{json.dumps(location_info, indent=2)}"
   conversation_history.append({"role": "system", "content": f"NPC Templates:\n{json.dumps(npc_templates, indent=2)}"})
   conversation_history.append({"role": "system", "content": f"Encounter Details:\n{json.dumps(encounter_data, indent=2)}"})
   
   # Log the conversation structure for debugging
   log_conversation_structure(conversation_history)
   
   # Save the updated conversation history
   save_json_file(conversation_history_file, conversation_history)
   
   # Prepare initial hitpoints info for all creatures
   hitpoints_info_parts = []
   player_name_display = player_info["name"]
   current_hp = player_info.get("hitPoints", 0)
   max_hp = player_info.get("maxHitPoints", 0)
   hitpoints_info_parts.append(f"{player_name_display}'s current hitpoints: {current_hp}/{max_hp}")
   
   for creature in encounter_data["creatures"]:
       if creature["type"] != "player":
           creature_name = creature.get("name", "Unknown Creature")
           creature_hp = creature.get("currentHitPoints", "Unknown")
           
           # Get the actual max HP from the correct source
           if creature["type"] == "npc":
               # For NPCs, look up their true max HP from their character file
               npc_name = creature_name.lower().replace(" ", "_").split('_')[0]
               npc_file = path_manager.get_npc_path(npc_name)
               try:
                   with open(npc_file, "r") as file:
                       npc_data = json.load(file)
                       creature_max_hp = npc_data["maxHitPoints"]
               except Exception as e:
                   print(f"ERROR: Failed to get correct max HP for {creature_name}: {str(e)}")
                   creature_max_hp = creature.get("maxHitPoints", "Unknown")
           else:
               # For monsters, use the encounter data
               creature_max_hp = creature.get("maxHitPoints", "Unknown")
               
           hitpoints_info_parts.append(f"{creature_name}'s current hitpoints: {creature_hp}/{creature_max_hp}")
   all_hitpoints_info = "\n".join(hitpoints_info_parts)
   
   # Generate prerolls for the initial scene
   preroll_text = generate_prerolls(encounter_data)
   
   # Get initial scene description before first user input
   print("DEBUG: Getting initial scene description...")
   initial_prompt = f"""Dungeon Master Note: Respond with valid JSON containing a 'narration' field and an 'actions' array. This is the start of combat, so please describe the scene and set initiative order, but don't take any actions yet. Start off by hooking the player and engaging them for the start of combat the way any world class dungeon master would.

Current hitpoints for all creatures:
{all_hitpoints_info}

{preroll_text}

Player: The combat begins. Describe the scene and the enemies we face."""

   conversation_history.append({"role": "user", "content": initial_prompt})
   save_json_file(conversation_history_file, conversation_history)

   # Get AI response for initial scene with validation and retries
   max_retries = 3
   valid_response = False
   initial_response = None
   
   for attempt in range(max_retries):
       try:
           response = client.chat.completions.create(
               model=COMBAT_MAIN_MODEL,
               temperature=TEMPERATURE,
               messages=conversation_history
           )
           initial_response = response.choices[0].message.content.strip()
           
           # Write raw response to debug file
           with open("debug_initial_response.json", "w") as debug_file:
               json.dump({"raw_initial_response": initial_response}, debug_file, indent=2)
           
           # Add the AI response to conversation history
           conversation_history.append({"role": "assistant", "content": initial_response})
           save_json_file(conversation_history_file, conversation_history)
           
           # Check if the response is valid JSON
           if not is_valid_json(initial_response):
               print(f"DEBUG: Invalid JSON response for initial scene (Attempt {attempt + 1}/{max_retries})")
               if attempt < max_retries - 1:
                   # Add error feedback to conversation history
                   conversation_history.append({
                       "role": "user",
                       "content": "Your previous response was not a valid JSON object with 'narration' and 'actions' fields. Please provide a valid JSON response for the initial scene."
                   })
                   save_json_file(conversation_history_file, conversation_history)
                   continue
               else:
                   print("DEBUG: Max retries exceeded for JSON validation. Using last response.")
                   break
           
           # Parse the JSON response
           parsed_response = json.loads(initial_response)
           narration = parsed_response["narration"]
           actions = parsed_response["actions"]
           
           # Validate the combat logic
           print("DEBUG: Validating combat response...")
           validation_result = validate_combat_response(initial_response, encounter_data, "The combat begins. Describe the scene and the enemies we face.", conversation_history)
           
           if validation_result is True:
               valid_response = True
               print("DEBUG: Combat response validation passed")
               print(f"DEBUG: Response validated successfully on attempt {attempt + 1}")
               break
           else:
               print(f"DEBUG: Response validation failed (Attempt {attempt + 1}/{max_retries})")
               
               # Handle both string and dict validation results
               if isinstance(validation_result, dict):
                   reason = validation_result["reason"]
                   recommendation = validation_result.get("recommendation", "")
                   feedback = f"Your previous response had issues with the combat logic: {reason}"
                   if recommendation:
                       feedback += f"\n\n{recommendation}"
               else:
                   reason = validation_result
                   feedback = f"Your previous response had issues with the combat logic: {reason}"
               
               print(f"Reason: {reason}")
               if attempt < max_retries - 1:
                   # Add error feedback to conversation history
                   conversation_history.append({
                       "role": "user",
                       "content": f"{feedback}. Please correct these issues and provide a valid initial scene description."
                   })
                   save_json_file(conversation_history_file, conversation_history)
                   continue
               else:
                   print("DEBUG: Max retries exceeded for combat validation. Using last response.")
                   break
       except Exception as e:
           print(f"ERROR: Failed to get or validate initial scene response (Attempt {attempt + 1}/{max_retries}): {str(e)}")
           if attempt < max_retries - 1:
               continue
           else:
               print("DEBUG: Max retries exceeded. Using last response if available.")
               break
   
   # Display initial scene if we have a response
   if initial_response:
       try:
           parsed_response = json.loads(initial_response)
           narration = parsed_response["narration"]
           print(f"Dungeon Master: {SOFT_REDDISH_ORANGE}{narration}{RESET_COLOR}")
       except Exception as e:
           print(f"ERROR: Failed to parse initial response: {str(e)}")
   else:
       print("ERROR: Failed to get an initial scene description after multiple attempts")
   
   # Combat loop
   while True:
       # Ensure all character data is synced to the encounter
       sync_active_encounter()
       
       # REFRESH CONVERSATION HISTORY WITH LATEST DATA
       print("DEBUG: Refreshing conversation history with latest character data...")
       
       # Reload player info
       player_name = player_info["name"].lower().replace(" ", "_")
       player_file = path_manager.get_player_path(player_name)
       try:
           player_info = safe_json_load(player_file)
           if not player_info:
               print(f"ERROR: Failed to load player file: {player_file}")
               # Replace player data in conversation history
               conversation_history[2]["content"] = f"Player Character:\n{json.dumps(player_info, indent=2)}"
       except Exception as e:
           print(f"ERROR: Failed to reload player file {player_file}: {str(e)}")
       
       # Reload encounter data
       json_file_path = f"encounter_{encounter_id}.json"
       try:
           encounter_data = safe_json_load(json_file_path)
           if encounter_data:
               # Find and update the encounter data in conversation history
               for i, msg in enumerate(conversation_history):
                   if msg["role"] == "system" and "Encounter Details:" in msg["content"]:
                       conversation_history[i]["content"] = f"Encounter Details:\n{json.dumps(encounter_data, indent=2)}"
                       break
       except Exception as e:
           print(f"ERROR: Failed to reload encounter file {json_file_path}: {str(e)}")
       
       # Reload NPC data
       for creature in encounter_data["creatures"]:
           if creature["type"] == "npc":
               npc_name = creature["name"].lower().replace(" ", "_").split('_')[0]
               npc_file = path_manager.get_npc_path(npc_name)
               try:
                   with open(npc_file, "r") as file:
                       npc_data = json.load(file)
                       # Update the NPC in the templates dictionary
                       npc_templates[npc_name] = npc_data
               except Exception as e:
                   print(f"ERROR: Failed to reload NPC file {npc_file}: {str(e)}")
       
       # Replace NPC templates in conversation history
       for i, msg in enumerate(conversation_history):
           if msg["role"] == "system" and "NPC Templates:" in msg["content"]:
               conversation_history[i]["content"] = f"NPC Templates:\n{json.dumps(npc_templates, indent=2)}"
               break
       
       # Save updated conversation history
       save_json_file(conversation_history_file, conversation_history)
       
       # Display player stats and get input
       player_name_display = player_info["name"]
       current_hp = player_info.get("hitPoints", 0)
       max_hp = player_info.get("maxHitPoints", 0)
       current_xp = player_info.get("experience_points", 0)
       next_level_xp = player_info.get("exp_required_for_next_level", 0)
       current_time_str = party_tracker_data["worldConditions"].get("time", "Unknown")
       
       stats_display = f"{LIGHT_OFF_GREEN}[{current_time_str}][HP:{current_hp}/{max_hp}][XP:{current_xp}/{next_level_xp}]{RESET_COLOR}"
       player_name_colored = f"{SOLID_GREEN}{player_name_display}{RESET_COLOR}"
       
       try:
           user_input_text = input(f"{stats_display} {player_name_colored}: ")
       except EOFError:
           print("ERROR in run_combat_simulation: EOF when reading a line")
           break
       
       # Prepare hitpoints info for all creatures
       hitpoints_info_parts = []
       hitpoints_info_parts.append(f"{player_name_display}'s current hitpoints: {current_hp}/{max_hp}")
       
       for creature in encounter_data["creatures"]:
           if creature["type"] != "player":
               creature_name = creature.get("name", "Unknown Creature")
               creature_hp = creature.get("currentHitPoints", "Unknown")
               
               # FIX: Get the actual max HP from the correct source
               if creature["type"] == "npc":
                   # For NPCs, look up their true max HP from their character file
                   npc_name = creature_name.lower().replace(" ", "_").split('_')[0]
                   npc_file = path_manager.get_npc_path(npc_name)
                   try:
                       with open(npc_file, "r") as file:
                           npc_data = json.load(file)
                           creature_max_hp = npc_data["maxHitPoints"]
                   except Exception as e:
                       print(f"ERROR: Failed to get correct max HP for {creature_name}: {str(e)}")
                       creature_max_hp = creature.get("maxHitPoints", "Unknown")
               else:
                   # For monsters, use the encounter data
                   creature_max_hp = creature.get("maxHitPoints", "Unknown")
                   
               hitpoints_info_parts.append(f"{creature_name}'s current hitpoints: {creature_hp}/{creature_max_hp}")
       all_hitpoints_info = "\n".join(hitpoints_info_parts)
       
       # Generate fresh prerolls for this combat round
       preroll_text = generate_prerolls(encounter_data)
       
       # Format user input with DM note, hitpoints info, and prerolls
       user_input_with_note = f"""Dungeon Master Note: Respond with valid JSON containing a 'narration' field and an 'actions' array. Use 'updatePlayerInfo', 'updateNPCInfo', and 'updateEncounter' actions to record changes in hit points, status, or conditions for any creature in the encounter. Remember to use separate 'updateNPCInfo' actions whenever NPCs take damage or their status changes. Monster changes should be in 'updateEncounter', but NPC changes require their own 'updateNPCInfo' actions.

Important: 
1. The status field for creatures must be lowercase: 'alive', 'dead', 'unconscious', or 'defeated'.
2. Include the 'exit' action when the encounter ends.
3. NPC and monster status updates must match the expected schema values.

Current hitpoints for all creatures:
{all_hitpoints_info}

{preroll_text}

Player: {user_input_text}"""
       
       # Add user input to conversation history
       conversation_history.append({"role": "user", "content": user_input_with_note})
       save_json_file(conversation_history_file, conversation_history)
       
       # Get AI response with validation and retries
       max_retries = 3
       valid_response = False
       ai_response = None
       
       for attempt in range(max_retries):
           try:
               response = client.chat.completions.create(
                   model=COMBAT_MAIN_MODEL,
                   temperature=TEMPERATURE,
                   messages=conversation_history
               )
               ai_response = response.choices[0].message.content.strip()
               
               # Write raw response to debug file
               with open("debug_ai_response.json", "w") as debug_file:
                   json.dump({"raw_ai_response": ai_response}, debug_file, indent=2)
               
               # IMPORTANT CHANGE: Always add the AI response to conversation history
               # even if it fails validation - this ensures the model can learn from mistakes
               conversation_history.append({"role": "assistant", "content": ai_response})
               save_json_file(conversation_history_file, conversation_history)
               
               # Check if the response is valid JSON
               if not is_valid_json(ai_response):
                   print(f"DEBUG: Invalid JSON response from AI (Attempt {attempt + 1}/{max_retries})")
                   if attempt < max_retries - 1:
                       # Add error feedback to conversation history
                       conversation_history.append({
                           "role": "user",
                           "content": "Your previous response was not a valid JSON object with 'narration' and 'actions' fields. Please provide a valid JSON response."
                       })
                       save_json_file(conversation_history_file, conversation_history)
                       continue
                   else:
                       print("DEBUG: Max retries exceeded for JSON validation. Skipping this response.")
                       break
               
               # Parse the JSON response
               parsed_response = json.loads(ai_response)
               narration = parsed_response["narration"]
               actions = parsed_response["actions"]
               
               # Validate the combat logic
               validation_result = validate_combat_response(ai_response, encounter_data, user_input_text, conversation_history)
               
               if validation_result is True:
                   valid_response = True
                   print(f"DEBUG: Response validated successfully on attempt {attempt + 1}")
                   break
               else:
                   print(f"DEBUG: Response validation failed (Attempt {attempt + 1}/{max_retries})")
                   
                   # Handle both string and dict validation results
                   if isinstance(validation_result, dict):
                       reason = validation_result["reason"]
                       recommendation = validation_result.get("recommendation", "")
                       feedback = f"Your previous response had issues with the combat logic: {reason}"
                       if recommendation:
                           feedback += f"\n\n{recommendation}"
                   else:
                       reason = validation_result
                       feedback = f"Your previous response had issues with the combat logic: {reason}"
                   
                   print(f"Reason: {reason}")
                   if attempt < max_retries - 1:
                       # Add error feedback to conversation history
                       conversation_history.append({
                           "role": "user",
                           "content": f"{feedback}. Please correct these issues and try again."
                       })
                       save_json_file(conversation_history_file, conversation_history)
                       continue
                   else:
                       print("DEBUG: Max retries exceeded for combat validation. Using last response.")
                       break
           except Exception as e:
               print(f"ERROR: Failed to get or validate AI response (Attempt {attempt + 1}/{max_retries}): {str(e)}")
               if attempt < max_retries - 1:
                   continue
               else:
                   print("DEBUG: Max retries exceeded. Skipping this response.")
                   break
       
       if not ai_response:
           print("ERROR: Failed to get a valid AI response after multiple attempts")
           continue
       
       # Process the validated response
       try:
           parsed_response = json.loads(ai_response)
           narration = parsed_response["narration"]
           actions = parsed_response["actions"]
       except json.JSONDecodeError as e:
           print(f"DEBUG: JSON parsing error: {str(e)}")
           print("DEBUG: Raw AI response:")
           print(ai_response)
           continue
       
       # Check if this response includes an exit action BEFORE displaying narration
       has_exit_action = False
       for action in actions:
           if action.get("action", "").lower() == "exit":
               has_exit_action = True
               break
       
       # Only display narration if there's no exit action
       if not has_exit_action:
           print(f"Dungeon Master: {SOFT_REDDISH_ORANGE}{narration}{RESET_COLOR}")
       
       # Process actions
       for action in actions:
           action_type = action.get("action", "").lower()
           parameters = action.get("parameters", {})
           
           if action_type == "updateplayerinfo":
               player_name_for_update = player_info["name"].lower().replace(" ", "_")
               changes = parameters.get("changes", "")
               try:
                   updated_player_info = update_player_info.update_player(player_name_for_update, changes)
                   if updated_player_info:
                       player_info = updated_player_info
                       print(f"DEBUG: Player info updated successfully")
               except Exception as e:
                   print(f"ERROR: Failed to update player info: {str(e)}")
           
           elif action_type == "updatenpcinfo":
               npc_name_for_update = parameters.get("npcName", "").lower().replace(' ', '_').split('_')[0] # Format for file access
               changes = parameters.get("changes", "")
               
               # Debug logging for updateNPCInfo transaction
               debug_log = {
                   "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "action_type": action_type,
                   "raw_action": action,
                   "extracted_npc_name": npc_name_for_update,
                   "extracted_changes": changes,
                   "original_parameters": parameters
               }
               
               try:
                   print(f"DEBUG: UpdateNPCInfo transaction starting...")
                   print(f"DEBUG: NPC Name: {npc_name_for_update}")
                   print(f"DEBUG: Changes requested: {changes}")
                   print(f"DEBUG: Raw action object: {json.dumps(action, indent=2)}")
                   
                   updated_npc_info = update_npc_info.update_npc(npc_name_for_update, changes)
                   
                   debug_log["update_result"] = "success" if updated_npc_info else "failed"
                   debug_log["updated_info"] = updated_npc_info if updated_npc_info else None
                   
                   if updated_npc_info:
                       print(f"DEBUG: NPC {npc_name_for_update} info updated successfully")
                   else:
                       print(f"DEBUG: Update failed for NPC {npc_name_for_update}")
               except Exception as e:
                   print(f"ERROR: Failed to update NPC info: {str(e)}")
                   debug_log["error"] = str(e)
               
               # Write debug log to file
               try:
                   with open("npc_update_debug_log.json", "a") as debug_file:
                       json.dump(debug_log, debug_file)
                       debug_file.write("\n")
               except Exception as log_error:
                   print(f"ERROR: Failed to write debug log: {str(log_error)}")
           
           elif action_type == "updateencounter":
               encounter_id_for_update = parameters.get("encounterId", encounter_id)
               changes = parameters.get("changes", "")
               try:
                   updated_encounter_data = update_encounter.update_encounter(encounter_id_for_update, changes)
                   if updated_encounter_data:
                       # Normalize status values to lowercase
                       updated_encounter_data = normalize_encounter_status(updated_encounter_data)
                       encounter_data = updated_encounter_data
                       print(f"DEBUG: Encounter {encounter_id_for_update} updated successfully")
               except Exception as e:
                   print(f"ERROR: Failed to update encounter: {str(e)}")
           
           elif action_type == "exit":
               print("DEBUG: Combat has ended, preparing summary...")
               xp_narrative, xp_awarded = calculate_xp()
               # Still record this information in the conversation history, but don't print it to console
               conversation_history.append({"role": "system", "content": f"XP Awarded: {xp_narrative}"})
               save_json_file(conversation_history_file, conversation_history)
               
               # Update XP for player
               xp_update_response = f"Update the character's experience points. XP Awarded: {xp_awarded}"
               updated_data_tuple = update_json_schema(xp_update_response, player_info, encounter_data, party_tracker_data)
               if updated_data_tuple:
                   player_info, _, _ = updated_data_tuple
               
               # Generate dialogue summary
               dialogue_summary_result = summarize_dialogue(conversation_history, location_info, party_tracker_data)
               
               # Generate chat history for debugging
               generate_chat_history(conversation_history, encounter_id)
               
               print("Combat encounter closed. Exiting combat simulation.")
               return dialogue_summary_result, player_info

       # Save updated conversation history after processing all actions
       save_json_file(conversation_history_file, conversation_history)

def main():
    print("DEBUG: Starting main function in combat_manager")
    
    # Load party tracker
    try:
        party_tracker_data = safe_json_load("party_tracker.json")
        if not party_tracker_data:
            print("ERROR: Failed to load party_tracker.json")
            return
        print(f"DEBUG: Loaded party_tracker: {party_tracker_data}")
    except Exception as e:
        print(f"ERROR: Failed to load party tracker: {str(e)}")
        return
    
    # Get active combat encounter
    active_combat_encounter = party_tracker_data["worldConditions"].get("activeCombatEncounter")
    print(f"DEBUG: Active combat encounter: {active_combat_encounter}")
    
    if not active_combat_encounter:
        print("No active combat encounter located.")
        return
    
    # Get location data
    current_location_id = party_tracker_data["worldConditions"]["currentLocationId"]
    current_area_id = get_current_area_id()
    
    print(f"DEBUG: Current location ID: {current_location_id}")
    print(f"DEBUG: Current area ID: {current_area_id}")
    
    location_data = get_location_data(current_location_id)
    
    if not location_data:
        print(f"ERROR: Failed to find location {current_location_id}")
        return
    
    # Run the combat simulation
    dialogue_summary, updated_player_info = run_combat_simulation(active_combat_encounter, party_tracker_data, location_data)
    
    print("Combat simulation completed.")
    print(f"Dialogue Summary: {dialogue_summary}")

if __name__ == "__main__":
    main()