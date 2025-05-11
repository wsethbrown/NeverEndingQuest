import json
import subprocess
import os
import re
from openai import OpenAI
from datetime import datetime, timedelta
from termcolor import colored

# Import other necessary modules
from combat_sim_v2 import run_combat_simulation
from plot_update import update_plot
from player_stats import get_player_stat
from update_world_time import update_world_time
from conversation_utils import update_conversation_history, update_character_data
import update_player_info
import update_npc_info

from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

# Model Configuration
MAIN_MODEL = "gpt-4o-mini"
SUMMARIZATION_MODEL = "gpt-4o-2024-08-06"
VALIDATION_MODEL = "gpt-4o-mini"
#MAIN_MODEL = "gpt-4o-2024-05-13"
#MAIN_MODEL = "gpt-4o-mini"
TEMPERATURE = 0.8

SOLID_GREEN = "\033[38;2;0;180;0m"  # Slightly darker solid green for player name
LIGHT_OFF_GREEN = "\033[38;2;100;180;100m"  # More muted light green for stats
RESET_COLOR = "\033[0m"

json_file = "conversation_history.json"

needs_conversation_history_update = False

def summarize_conversation(conversation_history, messages_per_summary=9):
    # Find all summary messages and the last system message
    summary_indices = [i for i, msg in enumerate(conversation_history) 
                       if msg['role'] == 'user' and msg['content'].startswith("Summary of previous interactions:")]
    last_system_index = max((i for i, msg in enumerate(conversation_history) if msg['role'] == 'system'), default=-1)
    
    if not summary_indices:
        start_index = last_system_index + 1
    else:
        start_index = summary_indices[0]
    
    messages_to_summarize = conversation_history[start_index:]
    
    if len(messages_to_summarize) <= messages_per_summary:
        return conversation_history  # Not enough new messages to summarize
    
    # Combine all existing summaries
    combined_summary = ""
    for idx in summary_indices:
        combined_summary += conversation_history[idx]['content'].replace("Summary of previous interactions: ", "") + " "
    
    # Find the next set of messages to summarize
    end_index = start_index + messages_per_summary
    while end_index < len(conversation_history) and conversation_history[end_index]['role'] != 'assistant':
        end_index += 1
    
    if end_index == len(conversation_history):
        return conversation_history  # No complete set of messages to summarize
    
    new_messages_to_summarize = conversation_history[start_index:end_index]
    
    # Prepare the summarization prompt
    summarization_prompt = """
    You are a historian who is summarizing a 5th Edition campaign adventure to pass onto other Dungeon Masters and record the parties adventures. Your task is to create concise but engaging summaries of scenes, focusing on key actions, character interactions, and relevant environmental descriptions. The summaries should maintain the narrative flow while capturing the essential points of interest, particularly character decisions, skill checks, and encounters.
    Instructions:
    1. Narrative Focus: Extract and summarize the essential elements of the scene. This includes the setting description, key actions taken by characters, and any interactions between them or with NPCs/monsters. Maintain a flow that reads like a cohesive story, but keep it concise and to the point.
    2. Character Actions & Decisions: Highlight any skill checks, important decisions, or actions made by the players. Include any results from these actions (e.g., successful searches, combat outcomes, treasure discoveries).
    3. Encounters & Combat: Briefly describe any combat encounters, including the initiation, actions taken by characters, and the outcome of the encounter (e.g., monster defeated, experience gained).
    4. Environment & Setting: Mention key environmental details or atmospheric elements (e.g., dim light, ancient stone, mysterious aura) that set the tone of the scene, but do not focus on them in excessive detail.
    5. Concise and Clear: The summary should be short, generally around one or two paragraphs, avoiding unnecessary repetition or verbose details.
    6. Party Interactions: Capture important interactions and dynamics between party members, such as conversations, support, disagreements, or suggestions that impact the group's decisions or mood.
    7. Be sure to document the beginning and ending dates/times of the history you're summarizing if the date/times are available.
    8. Do not include in your summary any actions involving the player leaving or rejoining the game.
    """
    
    user_prompt = f"""Previous summary:
    {combined_summary}
    
    Please summarize the following new conversation, incorporating relevant details from the previous summary:
    """
    
    for msg in new_messages_to_summarize:
        user_prompt += f"\n{msg['role'].upper()}: {msg['content']}"
    
    # Get AI summary
    summary_response = client.chat.completions.create(
        model=SUMMARIZATION_MODEL,
        temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": summarization_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    new_summary = summary_response.choices[0].message.content.strip()
    
    # Replace summarized messages with new summary
    new_conversation_history = (
        conversation_history[:last_system_index + 1] +
        [{"role": "user", "content": f"Summary of previous interactions: {new_summary}"}] +
        conversation_history[end_index:]
    )
    
    return new_conversation_history

def needs_summarization(conversation_history, threshold=80):
    summary_indices = [i for i, msg in enumerate(conversation_history) 
                       if msg['role'] == 'user' and msg['content'].startswith("Summary of previous interactions:")]
    last_system_index = max((i for i, msg in enumerate(conversation_history) if msg['role'] == 'system'), default=-1)
    
    if not summary_indices:
        start_index = last_system_index + 1
    else:
        start_index = summary_indices[-1] + 1
    
    return len(conversation_history) - start_index > threshold

# Add this new function near the top of the file
def exit_game():
    print("Fond farewell until we meet again!")
    exit()

def get_npc_stat(npc_name, stat_name, time_estimate):
    print(f"DEBUG: get_npc_stat called for {npc_name}, stat: {stat_name}")
    npc_file = f"{npc_name.lower().replace(' ', '_')}.json"
    try:
        with open(npc_file, "r") as file:
            npc_stats = json.load(file)
    except FileNotFoundError:
        print(f"{npc_file} not found. Stat retrieval failed.")
        return "NPC stat not found"
    except json.JSONDecodeError:
        print(f"{npc_file} has an invalid JSON format. Stat retrieval failed.")
        return "NPC stat not found"

    stat_value = None
    modifier_value = None

    if npc_stats:
        if stat_name.lower() in npc_stats["abilities"]:
            stat_value = npc_stats["abilities"][stat_name.lower()]
            modifier_value = (stat_value - 10) // 2

    if stat_value is not None and modifier_value is not None:
        # Update the world time based on the time estimate (in minutes)
        update_world_time(time_estimate)

        return f"NPC's {stat_name.capitalize()}: {stat_value} (Modifier: {modifier_value})"
    else:
        return "NPC stat not found"

def parse_json_safely(text):
    # First, try to parse as-is
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract from code block
    json_content = extract_json_from_codeblock(text)
    try:
        return json.loads(json_content)
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

def validate_ai_response(primary_response, user_input, validation_prompt, conversation_history, party_tracker_data):
    # Get the last two messages from the conversation history
    last_two_messages = conversation_history[-2:]
    
    # Ensure we have at least two messages
    while len(last_two_messages) < 2:
        last_two_messages.insert(0, {"role": "assistant", "content": "Previous context not available."})
    
    # Get location data from party tracker
    current_location_id = party_tracker_data["worldConditions"]["currentLocationId"]
    current_area_id = party_tracker_data["worldConditions"]["currentAreaId"]
    
    # Load the area data
    area_file = f"{current_area_id}.json"
    try:
        with open(area_file, "r") as file:
            area_data = json.load(file)
        location_data = next((loc for loc in area_data["locations"] if loc["locationId"] == current_location_id), None)
    except (FileNotFoundError, json.JSONDecodeError):
        location_data = None
    
    # Create the location details message
    if location_data:
        location_details = f"Location Details: {location_data['description']} {location_data.get('dmInstructions', '')}"
    else:
        location_details = "Location Details: Not available."
    
    validation_conversation = [
        {"role": "system", "content": validation_prompt},
        {"role": "system", "content": location_details},
        last_two_messages[0],
        last_two_messages[1],
        {"role": "assistant", "content": primary_response}
    ]
    
    max_validation_retries = 3
    for attempt in range(max_validation_retries):
        validation_result = client.chat.completions.create(
            model=VALIDATION_MODEL,
            temperature=TEMPERATURE,
            messages=validation_conversation
        )
        
        validation_response = validation_result.choices[0].message.content.strip()
        
        try:
            validation_json = parse_json_safely(validation_response)
            is_valid = validation_json.get("valid", False)
            reason = validation_json.get("reason", "No reason provided")
            
            # Log only failed validations to prompt_validation.json
            if not is_valid:
                log_entry = {
                    "prompt": validation_conversation,
                    "response": validation_response,
                    "reason": reason
                }
                
                with open("prompt_validation.json", "a") as log_file:
                    json.dump(log_entry, log_file)
                    log_file.write("\n")  # Add a newline for better readability
                
                print(f"DEBUG: Validation failed. Reason: {reason}")
                return reason  # Return the failure reason
            else:
                print("DEBUG: Validation passed successfully")
                return True  # Return True for successful validation
        
        except json.JSONDecodeError:
            print(f"DEBUG: Invalid JSON from validation model (Attempt {attempt + 1}/{max_validation_retries})")
            print(f"Problematic response: {validation_response}")
            continue  # Retry the validation
    
    # If we've exhausted all retries and still don't have a valid JSON response
    print("DEBUG: Validation model consistently produced invalid JSON. Assuming primary response is valid.")
    return True

def load_validation_prompt():
    with open("validation_prompt.txt", "r") as file:
        return file.read().strip()

def update_party_npcs(party_tracker_data, operation, npc):
    if operation == "add":
        npc_file = f"{npc['name'].lower().replace(' ', '_')}.json"
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
    
    with open("party_tracker.json", "w") as file:
        json.dump(party_tracker_data, file, indent=2)
    print(f"DEBUG: Party NPCs updated - {operation} {npc['name']}")

def load_json_file(file_path):
    try:
        if file_path.endswith('.txt'):
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        else:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
    except FileNotFoundError:
        print(f"DEBUG: Welcome to the world! Creating {file_path} for the first time.")
        return None
    except json.JSONDecodeError:
        print(f"DEBUG: Invalid JSON in {file_path}.")
        return None
    except UnicodeDecodeError:
        print(f"DEBUG: Unable to decode {file_path} using UTF-8 encoding.")
        return None

def get_location_info(location_name, current_area, current_area_id):
    area_file = f"map_{current_area_id}.json"
    area_data = load_json_file(area_file)
    if area_data and "locations" in area_data:
        for location in area_data["locations"]:
            if location["name"] == location_name:
                return location
    return None

def truncate_dm_notes(conversation_history):
    for message in conversation_history:
        if message["role"] == "user" and message["content"].startswith("Dungeon Master Note:"):
            parts = message["content"].split("Player:", 1)
            if len(parts) == 2:
                date_time = re.search(r"Current date and time: ([^.]+)", parts[0])
                if date_time:
                    message["content"] = f"Dungeon Master Note: {date_time.group(0)}. Player:{parts[1]}"
    return conversation_history

def update_world_conditions(current_conditions, new_location, current_area, current_area_id):
    current_time = datetime.strptime(current_conditions["time"], "%H:%M:%S")
    new_time = (current_time + timedelta(hours=1)).strftime("%H:%M:%S")

    location_info = get_location_info(new_location, current_area, current_area_id)
    
    if location_info:
        return {
            "year": current_conditions["year"],
            "month": current_conditions["month"],
            "day": current_conditions["day"],
            "time": new_time,
            "weather": location_info.get("weatherConditions", ""),
            "season": current_conditions["season"],
            "dayNightCycle": "Day" if 6 <= int(new_time[:2]) < 18 else "Night",
            "moonPhase": current_conditions["moonPhase"],
            "currentLocation": new_location,
            "currentLocationId": location_info["locationId"],
            "currentArea": current_area,
            "currentAreaId": current_area_id,
            "majorEventsUnderway": current_conditions["majorEventsUnderway"],
            "politicalClimate": "",
            "activeEncounter": "",
            "activeCombatEncounter": current_conditions.get("activeCombatEncounter", "")
        }
    else:
        return current_conditions

def handle_location_transition(current_location, new_location, current_area, current_area_id, area_connectivity_id=None):
    print(f"DEBUG: Handling location transition from '{current_location}' to '{new_location}'")
    print(f"DEBUG: Current area: '{current_area}', Current area ID: '{current_area_id}'")
    print(f"DEBUG: Area Connectivity ID provided: '{area_connectivity_id}'")
    
    party_tracker = load_json_file("party_tracker.json")
    if party_tracker:
        print("DEBUG: Successfully loaded party_tracker.json")
        
        # Correct file naming convention
        current_area_file = f"{current_area_id}.json"
        print(f"DEBUG: Searching for current location in file: {current_area_file}")
        current_area_data = load_json_file(current_area_file)
        
        if current_area_data and "locations" in current_area_data:
            current_location_info = next((loc for loc in current_area_data["locations"] if loc["name"] == current_location), None)
            print(f"DEBUG: Current location info: {current_location_info}")
        else:
            print(f"ERROR: Failed to load current area data or 'locations' not found in {current_area_file}")
            return None
        
        if area_connectivity_id:
            print(f"DEBUG: Transitioning to new area with ID: {area_connectivity_id}")
            new_area_file = f"{area_connectivity_id}.json"
            new_area_data = load_json_file(new_area_file)
            if new_area_data and "locations" in new_area_data:
                new_location_info = next((loc for loc in new_area_data["locations"] if loc["name"] == new_location), None)
                if new_location_info:
                    print(f"DEBUG: New location '{new_location}' found in new area {area_connectivity_id}")
                else:
                    print(f"DEBUG: New location '{new_location}' not found in new area {area_connectivity_id}")
                    return None
            else:
                print(f"DEBUG: Failed to load new area data or 'locations' not found in {new_area_file}")
                return None
        else:
            new_location_info = next((loc for loc in current_area_data["locations"] if loc["name"] == new_location), None)
        
        print(f"DEBUG: New location info: {new_location_info}")
    
    if current_location_info:
        print(f"DEBUG: Attempting to update current_location.json")
        try:
            with open("current_location.json", "w") as file:
                json.dump(current_location_info, file, indent=2)
            print("DEBUG: Successfully updated current_location.json")
        except Exception as e:
            print(f"ERROR: Failed to update current_location.json. Error: {str(e)}")

        try:
            print("DEBUG: Running adv_summary.py to update area JSON")
            result = subprocess.run(["python", "adv_summary.py", "conversation_history.json", "current_location.json", current_location, current_area_id], 
                        check=True, capture_output=True, text=True)
            print("DEBUG: adv_summary.py output:", result.stdout)
            print("DEBUG: adv_summary.py debug info:", result.stderr)
            print("DEBUG: adv_summary.py completed successfully")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Error occurred while running adv_summary.py: {e}")
            print("ERROR: Error output:", e.stderr)
            print("ERROR: Standard output:", e.stdout)

        if party_tracker and new_location_info:
            print("DEBUG: Updating party_tracker with new location information")
            party_tracker["worldConditions"] = update_world_conditions(party_tracker["worldConditions"], new_location, current_area, current_area_id)
            party_tracker["worldConditions"]["currentLocation"] = new_location
            
            if area_connectivity_id:
                party_tracker["worldConditions"]["currentArea"] = new_area_data.get("areaName", "Unknown Area")
                party_tracker["worldConditions"]["currentAreaId"] = area_connectivity_id
            
            party_tracker["worldConditions"]["currentLocationId"] = new_location_info["locationId"]
            party_tracker["worldConditions"]["weatherConditions"] = new_location_info.get("weatherConditions", "")
            
            print(f"DEBUG: Attempting to update party_tracker.json")
            try:
                with open("party_tracker.json", "w") as file:
                    json.dump(party_tracker, file, indent=2)
                print("DEBUG: Successfully updated party_tracker.json")
            except Exception as e:
                print(f"ERROR: Failed to update party_tracker.json. Error: {str(e)}")

        return f"Describe the immediate surroundings and any notable features or encounters in {new_location}, based on its recent history and current state."
    else:
        print(f"ERROR: Could not find information for current location: {current_location}")
        return None

def process_conversation_history(history):
    print(f"DEBUG: Processing conversation history")
    for message in history:
        if message["role"] == "user" and message["content"].startswith("Leveling Dungeon Master Guidance"):
            message["content"] = "DM Guidance: Proceed with leveling up the player character or the party NPC given the 5th Edition role playing game rules. Only level the player character or party NPC one level at a time to ensure no mistakes are made. If you are leveling up a party NPC then pass all changes at once using the 'updateNPCInfo' action. If you are leveling up a player character then you must ask the player for important decisions and choices they would have control over. After the player has provided the needed information then use the 'updatePlayerInfo' to pass all changes to the players character sheet and include the experience goal for the next level. Do not update the player's information in segements."
    print(f"DEBUG: Conversation history processing complete")
    return history

def get_location_data(location_id, area_id):
    area_file = f"{area_id}.json"
    try:
        with open(area_file, "r") as file:
            area_data = json.load(file)
        for location in area_data["locations"]:
            if location["locationId"] == location_id:
                return location
        print(f"ERROR: Location {location_id} not found in {area_file}")
    except FileNotFoundError:
        print(f"ERROR: Area file {area_file} not found")
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in {area_file}")
    return None

def process_action(action, party_tracker_data, location_data, conversation_history):
    global needs_conversation_history_update
    action_type = action.get("action")
    parameters = action.get("parameters", {})

    if action_type == "createEncounter":
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
                with open("party_tracker.json", "w") as file:
                    json.dump(party_tracker_data, file, indent=2)
                print(f"DEBUG: Updated party tracker with combat encounter ID: {encounter_id}")
                
                # Reload location data here
                current_location_id = party_tracker_data["worldConditions"]["currentLocationId"]
                current_area_id = party_tracker_data["worldConditions"]["currentAreaId"]
                location_data = get_location_data(current_location_id, current_area_id)
                
                if location_data is None:
                    print(f"ERROR: Failed to load location data for {current_location_id}")
                    return
                
                #print(f"DEBUG: Location data before combat simulation: {json.dumps(location_data, indent=2)}")
                
                dialogue_summary, updated_player_info = run_combat_simulation(encounter_id, party_tracker_data, location_data)

                player_name = next((member.lower() for member in party_tracker_data["partyMembers"]), None)
                if player_name and updated_player_info is not None:
                    player_file = f"{player_name}.json"
                    with open(player_file, "w") as file:
                        json.dump(updated_player_info, file, indent=2)
                    print(f"DEBUG: Updated player file for {player_name}")
                else:
                    print("WARNING: Combat simulation did not return valid player info. Player file not updated.")

                # Copy combat summary to main conversation history
                with open("combat_conversation_history.json", "r") as combat_file:
                    combat_history = json.load(combat_file)
                    combat_summary = next((entry for entry in reversed(combat_history) if entry["role"] == "assistant" and "Combat Summary:" in entry["content"]), None)

                if combat_summary:
                    # Modify the combat summary to change the role from "assistant" to "user"
                    modified_combat_summary = {
                        "role": "user",
                        "content": combat_summary["content"]
                    }

                    # Add the modified combat summary to the conversation history
                    conversation_history.append(modified_combat_summary)

                    # Save the updated conversation history
                    save_conversation_history(conversation_history)

                    # Get a new AI response based on the updated conversation history
                    new_response = get_ai_response(conversation_history)

                    # Process this new response
                    process_ai_response(new_response, party_tracker_data, location_data, conversation_history)
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

    elif action_type == "updateTime":
        time_estimate_str = str(parameters["timeEstimate"])
        update_world_time(time_estimate_str)

    elif action_type == "updatePlot":
        plot_point_id = parameters["plotPointId"]
        new_status = parameters["newStatus"]
        plot_impact = parameters.get("plotImpact", "")
        plot_filename = f"plot_{party_tracker_data['worldConditions']['currentAreaId']}.json"
        updated_plot = update_plot(plot_point_id, new_status, plot_impact, plot_filename)

    elif action_type == "exitGame":
        conversation_history.append({"role": "user", "content": "Dungeon Master Note: Resume the game, the player has returned."})
        save_conversation_history(conversation_history)
        exit_game()
    
    elif action_type == "transitionLocation":
        new_location = parameters["newLocation"]
        area_connectivity_id = parameters.get("areaConnectivityId")
        current_location = party_tracker_data["worldConditions"]["currentLocation"]
        current_area = party_tracker_data["worldConditions"]["currentArea"]
        current_area_id = party_tracker_data["worldConditions"]["currentAreaId"]
        print(f"DEBUG: Transitioning from {current_location} to {new_location}")
        transition_prompt = handle_location_transition(current_location, new_location, current_area, current_area_id, area_connectivity_id)
        
        if transition_prompt:
            conversation_history.append({"role": "user", "content": f"Location transition: {current_location} to {new_location}"})
            print("DEBUG: Location transition complete")
        else:
            print("ERROR: Failed to handle location transition")

    elif action_type == "levelUp":
        entity_name = parameters.get("entityName")
        new_level = parameters.get("newLevel")

        # Load leveling info
        with open("leveling_info.txt", "r") as file:
            leveling_info = file.read()

        # Create DM Note with leveling info
        dm_note = f"Leveling Dungeon Master Guidance: Proceed with leveling up the player character or the party NPC given the 5th Edition role playing game rules. Only level the player or the party NPC one level at a time to ensure no mistakes are made. If you are leveling up a party NPC then pass all changes at once using the 'updateNPCInfo' action and use the narration to narrate the party NPCs growth. If you are leveling up a player character then you must ask the player for important decisions and choices they would have control over. After the player has provided the needed information then use the 'updatePlayerInfo' to pass all changes to the players character sheet and include the experience goal for the next level. Do not update the player's information in segements. \n\n{leveling_info}"
        
        # Add DM Note to conversation history
        conversation_history.append({"role": "user", "content": dm_note})

        # Get a new AI response based on the updated conversation history
        new_response = get_ai_response(conversation_history)
        
        # Process this new response
        return process_ai_response(new_response, party_tracker_data, location_data, conversation_history)
    
    elif action_type == "updatePlayerInfo":
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
    
    elif action_type == "updateNPCInfo":
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

    elif action_type == "updatePartyNPCs":
        operation = parameters["operation"]
        npc = parameters["npc"]
        update_party_npcs(party_tracker_data, operation, npc)

    else:
        print(f"WARNING: Unknown action type: {action_type}")

def extract_json_from_codeblock(text):
    match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def process_ai_response(response, party_tracker_data, location_data, conversation_history):
    try:
        json_content = extract_json_from_codeblock(response)
        parsed_response = json.loads(json_content)
        
        narration = parsed_response.get("narration", "")
        print(colored("Dungeon Master:", "blue"), colored(narration, "blue"))
        
        # Add the AI's response to the conversation history immediately
        conversation_history.append({"role": "assistant", "content": response})
        
        actions = parsed_response.get("actions", [])
        for action in actions:
            result = process_action(action, party_tracker_data, location_data, conversation_history)
            if result == "exit":
                return "exit"  # Propagate the exit signal
            if isinstance(result, tuple) and result[0] == "skillCheck":
                dm_note = result[1]
                # Add the DM Note to the conversation history as a user message
                conversation_history.append({"role": "user", "content": dm_note})
                # Get a new AI response based on the updated conversation history
                new_response = get_ai_response(conversation_history)
                # Process this new response
                process_ai_response(new_response, party_tracker_data, location_data, conversation_history)
        
        save_conversation_history(conversation_history)
        
        return {"role": "assistant", "content": response}
    except json.JSONDecodeError as e:
        print(f"Error: Unable to parse AI response as JSON: {e}")
        print(f"Problematic response: {response}")
        conversation_history.append({"role": "assistant", "content": response})
        save_conversation_history(conversation_history)
        return {"role": "assistant", "content": response}

def save_conversation_history(history):
    #print("DEBUG: Saving updated conversation history")
    with open(json_file, "w") as file:
        json.dump(history, file, indent=2)
    # print("DEBUG: Conversation history saved successfully")

def get_ai_response(conversation_history):
    response = client.chat.completions.create(
        model=MAIN_MODEL,
        temperature=TEMPERATURE,
        messages=conversation_history
    )
    return response.choices[0].message.content.strip()

def ensure_main_system_prompt(conversation_history, main_system_prompt):
    # Remove any existing main system prompt
    conversation_history = [msg for msg in conversation_history if not (msg["role"] == "system" and msg["content"] == main_system_prompt)]
    
    # Add the main system prompt at the beginning
    return [{"role": "system", "content": main_system_prompt}] + conversation_history

def main_game_loop():
    global needs_conversation_history_update
    
    # Load the validation prompt
    validation_prompt = load_validation_prompt()

    # Load the main system prompt
    with open("system_prompt.txt", "r") as file:
        main_system_prompt = file.read()

    # Initialize conversation history
    conversation_history = load_json_file(json_file) or []

    # Load initial data
    party_tracker_data = load_json_file("party_tracker.json")
    current_area = party_tracker_data["worldConditions"]["currentArea"]
    current_area_id = party_tracker_data["worldConditions"]["currentAreaId"]
    location_data = get_location_info(party_tracker_data["worldConditions"]["currentLocation"], current_area, current_area_id)
    plot_data = load_json_file(f"plot_{current_area_id}.json")
    map_data = load_json_file(f"map_{current_area_id}.json")
    
    # Load campaign data
    campaign_name = party_tracker_data.get("campaign", "").replace(" ", "_")
    campaign_data = load_json_file(f"{campaign_name}_campaign.json")

    # Ensure main system prompt is at the beginning
    conversation_history = ensure_main_system_prompt(conversation_history, main_system_prompt)

    # Add other system prompts
    conversation_history = update_conversation_history(conversation_history, party_tracker_data, plot_data, campaign_data)
    conversation_history = update_character_data(conversation_history, party_tracker_data)

    # Ensure all system prompts are at the beginning
    system_prompts = [msg for msg in conversation_history if msg["role"] == "system"]
    non_system_messages = [msg for msg in conversation_history if msg["role"] != "system"]
    conversation_history = system_prompts + non_system_messages

    # Save the initial conversation history
    save_conversation_history(conversation_history)

    # Get initial AI response to set the scene
    initial_ai_response = get_ai_response(conversation_history)
    process_ai_response(initial_ai_response, party_tracker_data, location_data, conversation_history)

    while True:
        # Truncate older Dungeon Master Notes
        conversation_history = truncate_dm_notes(conversation_history)
        
        if needs_conversation_history_update:
            conversation_history = process_conversation_history(conversation_history)
            save_conversation_history(conversation_history)
            needs_conversation_history_update = False
        
        if needs_summarization(conversation_history):
            conversation_history = summarize_conversation(conversation_history)
        
        # Get user input
        player_name = party_tracker_data["partyMembers"][0]  # Assuming the first member is the player
        player_data = load_json_file(f"{player_name.lower().replace(' ', '_')}.json")
        
        if player_data:
            current_hp = player_data.get("hitPoints", "N/A")
            max_hp = player_data.get("maxHitPoints", "N/A")
            current_xp = player_data.get("experience_points", "N/A")
            next_level_xp = player_data.get("exp_required_for_next_level", "N/A")
            
            # Get the current time from party_tracker_data
            current_time = party_tracker_data["worldConditions"]["time"]
            
            stats_display = f"{LIGHT_OFF_GREEN}[{current_time}][HP:{current_hp}/{max_hp}][XP:{current_xp}/{next_level_xp}]{RESET_COLOR}"
            player_name_display = f"{SOLID_GREEN}{player_name}{RESET_COLOR}"
            
            user_input_text = input(f"{stats_display} {player_name_display}: ")
        else:
            user_input_text = input("User: ")
        
        # Load the latest party tracker data
        party_tracker_data = load_json_file("party_tracker.json")
        
        # Get stats for all party members
        party_members_stats = []
        for member in party_tracker_data["partyMembers"]:
            member_name = member.lower()
            member_data = load_json_file(f"{member_name}.json")
            if member_data:
                stats = {
                    "name": member_name.capitalize(),
                    "level": member_data.get("level", "N/A"),
                    "xp": member_data.get("experience_points", "N/A"),
                    "hp": member_data.get("hitPoints", "N/A"),
                    "max_hp": member_data.get("maxHitPoints", "N/A")
                }
                party_members_stats.append(stats)

        # Now let's do the same for NPCs
        for npc in party_tracker_data["partyNPCs"]:
            npc_name = npc["name"].lower().replace(' ', '_')
            npc_data = load_json_file(f"{npc_name}.json")
            if npc_data:
                stats = {
                    "name": npc["name"],
                    "level": npc_data.get("level", npc.get("level", "N/A")),
                    "xp": npc_data.get("experience_points", "N/A"),
                    "hp": npc_data.get("hitPoints", "N/A"),
                    "max_hp": npc_data.get("maxHitPoints", "N/A")
                }
                party_members_stats.append(stats)

        if party_members_stats:
            world_conditions = party_tracker_data["worldConditions"]
            date_time = f"{world_conditions['year']} {world_conditions['month']} {world_conditions['day']} {world_conditions['time']}"
            
            # Modified party stats to include ability scores and next level XP
            party_stats = []
            for stats in party_members_stats:
                member_data = load_json_file(f"{stats['name'].lower().replace(' ', '_')}.json")
                if member_data:
                    abilities = member_data.get("abilities", {})
                    ability_str = f"STR:{abilities.get('strength', 'N/A')} DEX:{abilities.get('dexterity', 'N/A')} CON:{abilities.get('constitution', 'N/A')} INT:{abilities.get('intelligence', 'N/A')} WIS:{abilities.get('wisdom', 'N/A')} CHA:{abilities.get('charisma', 'N/A')}"
                    next_level_xp = member_data.get("exp_required_for_next_level", "N/A")
                    party_stats.append(f"{stats['name']}: Level {stats['level']}, XP {stats['xp']}/{next_level_xp}, HP {stats['hp']}/{stats['max_hp']}, {ability_str}")
            
            party_stats_str = "; ".join(party_stats)
            
            current_location = world_conditions["currentLocation"]
            current_location_id = world_conditions["currentLocationId"]
            
            # Find the relevant plot points for the current location
            plot_data = load_json_file(f"plot_{current_area_id}.json")
            current_plot_points = [
                point for point in plot_data["plotPoints"] 
                if point["location"] == current_location_id and point["status"] != "completed"
            ]
            
            # Format the plot points
            plot_points_str = "\n".join([
                f"- {point['title']}: {point['description']}" 
                for point in current_plot_points
            ])
            
            # Find and format side quests for the current location
            side_quests = []
            for point in current_plot_points:
                for quest in point.get("sideQuests", []):
                    if quest["status"] != "completed":
                        side_quests.append(f"- {quest['title']} (Status: {quest['status']}): {quest['description']}")
            
            side_quests_str = "\n".join(side_quests)
            
            # Find the traps for the current location
            current_location_data = location_data
            
            traps = current_location_data.get("traps", []) if current_location_data else []
            
            # Format the traps
            traps_str = "\n".join([
                f"- {trap['name']}: {trap['description']} (Detect DC: {trap['detectDC']}, Disable DC: {trap['disableDC']}, Trigger DC: {trap['triggerDC']}, Damage: {trap['damage']})"
                for trap in traps
            ])
            
            dm_note = (f"Dungeon Master Note: Current date and time: {date_time}. "
                f"Party stats: Player Character: {party_stats[0]}; Party NPCs: {'; '.join(party_stats[1:])}. "
                f"Current location: {current_location} ({current_location_id}). "
                f"Active plot points for this location:\n{plot_points_str}\n"
                f"Active side quests for this location:\n{side_quests_str}\n"
                f"Traps in this location:\n{traps_str}\n"
                "updatePlayerInfo for the player's inventory, "
                "updateTime for time passage, "
                "updatePlot for story progression, discovers, and new information, "
                "updateNPCInfo for party NPC changes, updatePartyNPCs for party composition changes to the party tracker, "
                "levelUp for advancement, and exitGame for ending sessions. "
                "transitionLocation should always be used when the player expresses a desire to movde to an adjacent location to their current location, "
                "Always roleplay the NPC and NPC party rolls without asking the player. "
                "Always ask the player character to roll for skill checks and other actions. "
                "Proactively narrate location NPCs, start conversations, and weave plot elements into the adventure. "
                "Use party NPCs to narrate if possible instead of always narrating from the DM's perspective, but don't overdo it. "
                "Maintain immersive and engaging storytelling similar to an adventure novel while accurately managing game mechanics. "
                "Update all relevant information immediately and confirm with the player before major actions. "
                "Consider whether the party's action trigger traps in this location. "
                "Consider updating the plot elements on every action the player and NPCs take.")
        else:
            dm_note = "Dungeon Master Note: Remember to take actions if necessary such as updating the plot, time, character sheets, and location if changes occur."
        
        user_input_with_note = f"{dm_note} Player: {user_input_text}"
        conversation_history.append({"role": "user", "content": user_input_with_note})

        # Save conversation history after user input
        save_conversation_history(conversation_history)

        # Get AI response with validation
        retry_count = 0
        valid_response = False
        while retry_count < 5 and not valid_response:
            ai_response = get_ai_response(conversation_history)
            
            validation_result = validate_ai_response(ai_response, user_input_text, validation_prompt, conversation_history, party_tracker_data)
            if validation_result is True:
                valid_response = True
                print(f"DEBUG: Valid response generated on attempt {retry_count + 1}")
                result = process_ai_response(ai_response, party_tracker_data, location_data, conversation_history)
                if result == "exit":
                    return  # Exit the main_game_loop
            elif isinstance(validation_result, str):
                print(f"Validation failed. Reason: {validation_result}")
                print(f"Retrying... (Attempt {retry_count + 1}/5)")
                
                # Add the failure reason to the conversation history
                conversation_history.append({
                    "role": "user",
                    "content": f"Error Note: Your previous response failed validation. Reason: {validation_result}. Please adjust your response accordingly."
                })
                
                retry_count += 1

        if not valid_response:
            print("Failed to generate a valid response after 5 attempts. Proceeding with the last generated response.")
            result = process_ai_response(ai_response, party_tracker_data, location_data, conversation_history)
            if result == "exit":
                return  # Exit the main_game_loop

        # Reload data and update system prompts for next iteration
        party_tracker_data = load_json_file("party_tracker.json")
        current_area = party_tracker_data["worldConditions"]["currentArea"]
        current_area_id = party_tracker_data["worldConditions"]["currentAreaId"]
        location_data = get_location_info(party_tracker_data["worldConditions"]["currentLocation"], current_area, current_area_id)
        plot_data = load_json_file(f"plot_{current_area_id}.json")
        map_data = load_json_file(f"map_{current_area_id}.json")
        
        # Reload campaign data
        campaign_name = party_tracker_data.get("campaign", "").replace(" ", "_")
        campaign_data = load_json_file(f"{campaign_name}_campaign.json")
        
        conversation_history = update_conversation_history(conversation_history, party_tracker_data, plot_data, campaign_data)
        conversation_history = update_character_data(conversation_history, party_tracker_data)

        # Ensure main system prompt is at the beginning
        conversation_history = ensure_main_system_prompt(conversation_history, main_system_prompt)

        # Save the updated conversation history
        save_conversation_history(conversation_history)

if __name__ == "__main__":
    main_game_loop()