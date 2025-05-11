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

# Import model configurations from config.py
from config import (
    OPENAI_API_KEY,
    DM_MAIN_MODEL,
    DM_SUMMARIZATION_MODEL,
    DM_VALIDATION_MODEL
)

client = OpenAI(api_key=OPENAI_API_KEY)

# Temperature Configuration (remains the same)
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
    summarization_prompt_text = """
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
        model=DM_SUMMARIZATION_MODEL, # Use imported model name
        temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": summarization_prompt_text},
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

def validate_ai_response(primary_response, user_input, validation_prompt_text, conversation_history, party_tracker_data):
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
        {"role": "system", "content": validation_prompt_text},
        {"role": "system", "content": location_details},
        last_two_messages[0],
        last_two_messages[1],
        {"role": "assistant", "content": primary_response}
    ]

    max_validation_retries = 3
    for attempt in range(max_validation_retries):
        validation_result = client.chat.completions.create(
            model=DM_VALIDATION_MODEL, # Use imported model name
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
    area_file = f"{current_area_id}.json" # Corrected file naming convention
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
            "weather": location_info.get("weatherConditions", ""), # Ensure consistent naming
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

        current_area_file = f"{current_area_id}.json"
        print(f"DEBUG: Searching for current location in file: {current_area_file}")
        current_area_data = load_json_file(current_area_file)

        if current_area_data and "locations" in current_area_data:
            current_location_info = next((loc for loc in current_area_data["locations"] if loc["name"] == current_location), None)
            print(f"DEBUG: Current location info: {current_location_info}")
        else:
            print(f"ERROR: Failed to load current area data or 'locations' not found in {current_area_file}")
            return None

        new_location_info = None # Initialize to handle cases where it might not be set
        new_area_data = None # Initialize

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
                    # Attempt to find the location by ID if name fails, assuming new_location could be an ID
                    new_location_info = next((loc for loc in new_area_data["locations"] if loc["locationId"] == new_location), None)
                    if new_location_info:
                         print(f"DEBUG: New location with ID '{new_location}' found in new area {area_connectivity_id}")
                    else:
                        print(f"DEBUG: New location with ID '{new_location}' also not found in new area {area_connectivity_id}")
                        return None # Location not found in new area
            else:
                print(f"DEBUG: Failed to load new area data or 'locations' not found in {new_area_file}")
                return None
        else: # Transition within the same area
            new_location_info = next((loc for loc in current_area_data["locations"] if loc["name"] == new_location), None)
            if not new_location_info:
                # Attempt to find the location by ID if name fails
                new_location_info = next((loc for loc in current_area_data["locations"] if loc["locationId"] == new_location), None)


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
            # Determine which area data to use for world conditions update
            area_for_conditions = new_area_data if area_connectivity_id and new_area_data else current_area_data
            area_id_for_conditions = area_connectivity_id if area_connectivity_id else current_area_id
            
            party_tracker["worldConditions"] = update_world_conditions(
                party_tracker["worldConditions"],
                new_location_info["name"], # Use name from new_location_info
                area_for_conditions.get("areaName", current_area if not area_connectivity_id else "Unknown Area"),
                area_id_for_conditions
            )
            party_tracker["worldConditions"]["currentLocation"] = new_location_info["name"] # Ensure this uses the name

            if area_connectivity_id and new_area_data:
                party_tracker["worldConditions"]["currentArea"] = new_area_data.get("areaName", "Unknown Area")
                party_tracker["worldConditions"]["currentAreaId"] = area_connectivity_id
            # else, currentArea and currentAreaId remain as they were if no area transition

            party_tracker["worldConditions"]["currentLocationId"] = new_location_info["locationId"]
            party_tracker["worldConditions"]["weatherConditions"] = new_location_info.get("weatherConditions", "") # Ensure consistent naming

            print(f"DEBUG: Attempting to update party_tracker.json")
            try:
                with open("party_tracker.json", "w") as file:
                    json.dump(party_tracker, file, indent=2)
                print("DEBUG: Successfully updated party_tracker.json")
            except Exception as e:
                print(f"ERROR: Failed to update party_tracker.json. Error: {str(e)}")

        return f"Describe the immediate surroundings and any notable features or encounters in {new_location_info['name']}, based on its recent history and current state."
    else:
        print(f"ERROR: Could not find information for current location: {current_location} or new location: {new_location}")
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

def process_action(action, party_tracker_data, location_data_param, conversation_history): # Renamed location_data to avoid conflict
    global needs_conversation_history_update
    action_type = action.get("action")
    parameters = action.get("parameters", {})
    current_location_data = location_data_param # Use the passed in location_data

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
                # Use the reloaded location data for the combat simulation
                reloaded_location_data = get_location_data(current_location_id, current_area_id)


                if reloaded_location_data is None:
                    print(f"ERROR: Failed to load location data for {current_location_id}")
                    return # Or handle error appropriately

                dialogue_summary, updated_player_info = run_combat_simulation(encounter_id, party_tracker_data, reloaded_location_data)


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
                    modified_combat_summary = {
                        "role": "user",
                        "content": combat_summary["content"]
                    }
                    conversation_history.append(modified_combat_summary)
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
        new_location_name_or_id = parameters["newLocation"] # This could be a name or an ID
        area_connectivity_id = parameters.get("areaConnectivityId")
        current_location_name = party_tracker_data["worldConditions"]["currentLocation"]
        current_area_name = party_tracker_data["worldConditions"]["currentArea"]
        current_area_id = party_tracker_data["worldConditions"]["currentAreaId"]
        print(f"DEBUG: Transitioning from {current_location_name} to {new_location_name_or_id}")
        transition_prompt = handle_location_transition(current_location_name, new_location_name_or_id, current_area_name, current_area_id, area_connectivity_id)

        if transition_prompt:
            conversation_history.append({"role": "user", "content": f"Location transition: {current_location_name} to {new_location_name_or_id}"}) # Use the provided name/ID
            print("DEBUG: Location transition complete")
             # After transition, the current_location_data in the main loop might be stale.
            # We need to ensure the AI response processing uses the *new* location data.
            # This might require process_ai_response to reload location data or for main_game_loop to handle it.
            # For now, let's assume the main loop will reload it before the next AI call.
        else:
            print("ERROR: Failed to handle location transition")

    elif action_type == "levelUp":
        entity_name = parameters.get("entityName")
        new_level = parameters.get("newLevel")

        with open("leveling_info.txt", "r") as file:
            leveling_info = file.read()

        dm_note = f"Leveling Dungeon Master Guidance: Proceed with leveling up the player character or the party NPC given the 5th Edition role playing game rules. Only level the player or the party NPC one level at a time to ensure no mistakes are made. If you are leveling up a party NPC then pass all changes at once using the 'updateNPCInfo' action and use the narration to narrate the party NPCs growth. If you are leveling up a player character then you must ask the player for important decisions and choices they would have control over. After the player has provided the needed information then use the 'updatePlayerInfo' to pass all changes to the players character sheet and include the experience goal for the next level. Do not update the player's information in segements. \n\n{leveling_info}"
        conversation_history.append({"role": "user", "content": dm_note})
        new_response = get_ai_response(conversation_history)
        return process_ai_response(new_response, party_tracker_data, current_location_data, conversation_history) # Pass current_location_data

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

def process_ai_response(response, party_tracker_data, location_data_param, conversation_history): # Renamed location_data
    try:
        json_content = extract_json_from_codeblock(response)
        parsed_response = json.loads(json_content)

        narration = parsed_response.get("narration", "")
        print(colored("Dungeon Master:", "blue"), colored(narration, "blue"))

        conversation_history.append({"role": "assistant", "content": response})

        actions = parsed_response.get("actions", [])
        for action in actions:
            result = process_action(action, party_tracker_data, location_data_param, conversation_history) # Pass location_data_param
            if result == "exit":
                return "exit"
            if isinstance(result, tuple) and result[0] == "skillCheck": # This condition seems unlikely to be met now
                dm_note = result[1]
                conversation_history.append({"role": "user", "content": dm_note})
                new_response = get_ai_response(conversation_history)
                process_ai_response(new_response, party_tracker_data, location_data_param, conversation_history) # Pass location_data_param

        save_conversation_history(conversation_history)

        return {"role": "assistant", "content": response}
    except json.JSONDecodeError as e:
        print(f"Error: Unable to parse AI response as JSON: {e}")
        print(f"Problematic response: {response}")
        conversation_history.append({"role": "assistant", "content": response}) # Still save if narration was printed
        print(colored("Dungeon Master:", "blue"), colored(response, "blue")) # Print raw response if JSON fails but it was a narration
        save_conversation_history(conversation_history)
        return {"role": "assistant", "content": response} # Return raw if parsing fails

def save_conversation_history(history):
    with open(json_file, "w") as file:
        json.dump(history, file, indent=2)

def get_ai_response(conversation_history):
    response = client.chat.completions.create(
        model=DM_MAIN_MODEL, # Use imported model name
        temperature=TEMPERATURE,
        messages=conversation_history
    )
    return response.choices[0].message.content.strip()

def ensure_main_system_prompt(conversation_history, main_system_prompt_text):
    # Remove all existing system prompts that appear to be the main system prompt
    # We'll identify the main system prompt by checking if it starts with the first few words
    # of the actual system prompt content
    main_prompt_start = main_system_prompt_text[:50]  # First 50 characters as identifier
    
    # Filter out any system message that starts with our identifier
    filtered_history = []
    for msg in conversation_history:
        if msg["role"] == "system" and msg["content"].startswith(main_prompt_start):
            continue  # Skip this message as it's likely our main system prompt
        filtered_history.append(msg)
    
    # Always place the main system prompt at the beginning
    return [{"role": "system", "content": main_system_prompt_text}] + filtered_history

def main_game_loop():
    global needs_conversation_history_update

    validation_prompt_text = load_validation_prompt() 

    with open("system_prompt.txt", "r") as file:
        main_system_prompt_text = file.read() 

    conversation_history = load_json_file(json_file) or []
    party_tracker_data = load_json_file("party_tracker.json")
    
    current_area_id = party_tracker_data["worldConditions"]["currentAreaId"]
    location_data = get_location_info( 
        party_tracker_data["worldConditions"]["currentLocation"],
        party_tracker_data["worldConditions"]["currentArea"],
        current_area_id
    )

    plot_data = load_json_file(f"plot_{current_area_id}.json")
    
    campaign_name = party_tracker_data.get("campaign", "").replace(" ", "_")
    campaign_data = load_json_file(f"{campaign_name}_campaign.json")

    conversation_history = ensure_main_system_prompt(conversation_history, main_system_prompt_text)
    conversation_history = update_conversation_history(conversation_history, party_tracker_data, plot_data, campaign_data)
    conversation_history = update_character_data(conversation_history, party_tracker_data)

    # Ensure the main system prompt is first, followed by other system prompts
    main_prompt = None
    other_system_prompts = []
    non_system_messages = []

    for msg in conversation_history:
        if msg["role"] == "system":
            if msg["content"].startswith(main_system_prompt_text[:50]):
                main_prompt = msg
            else:
                other_system_prompts.append(msg)
        else:
            non_system_messages.append(msg)

    # Reconstruct with proper order: main system prompt, other system prompts, then conversation
    conversation_history = []
    if main_prompt:
        conversation_history.append(main_prompt)
    conversation_history.extend(other_system_prompts)
    conversation_history.extend(non_system_messages)

    save_conversation_history(conversation_history)

    initial_ai_response = get_ai_response(conversation_history)
    # Ensure location_data passed here is the one loaded for the initial state
    process_ai_response(initial_ai_response, party_tracker_data, location_data, conversation_history) 

    while True:
        conversation_history = truncate_dm_notes(conversation_history)

        if needs_conversation_history_update:
            conversation_history = process_conversation_history(conversation_history)
            save_conversation_history(conversation_history)
            needs_conversation_history_update = False

        if needs_summarization(conversation_history):
            conversation_history = summarize_conversation(conversation_history)

        player_name_actual = party_tracker_data["partyMembers"][0]
        player_data_file = f"{player_name_actual.lower().replace(' ', '_')}.json"
        player_data_current = load_json_file(player_data_file)

        if player_data_current:
            current_hp = player_data_current.get("hitPoints", "N/A")
            max_hp = player_data_current.get("maxHitPoints", "N/A")
            current_xp = player_data_current.get("experience_points", "N/A")
            next_level_xp = player_data_current.get("exp_required_for_next_level", "N/A")
            current_time_str = party_tracker_data["worldConditions"]["time"]
            stats_display = f"{LIGHT_OFF_GREEN}[{current_time_str}][HP:{current_hp}/{max_hp}][XP:{current_xp}/{next_level_xp}]{RESET_COLOR}"
            player_name_display = f"{SOLID_GREEN}{player_name_actual}{RESET_COLOR}"
            user_input_text = input(f"{stats_display} {player_name_display}: ")
        else:
            user_input_text = input("User: ")

        party_tracker_data = load_json_file("party_tracker.json") 

        party_members_stats = []
        for member_name_iter in party_tracker_data["partyMembers"]:
            member_file_path = f"{member_name_iter.lower().replace(' ', '_')}.json"
            member_data_iter = load_json_file(member_file_path)
            if member_data_iter:
                stats = {
                    "name": member_name_iter.capitalize(), 
                    "level": member_data_iter.get("level", "N/A"),
                    "xp": member_data_iter.get("experience_points", "N/A"),
                    "hp": member_data_iter.get("hitPoints", "N/A"),
                    "max_hp": member_data_iter.get("maxHitPoints", "N/A")
                }
                party_members_stats.append(stats)

        for npc_info_iter in party_tracker_data["partyNPCs"]:
            npc_name_iter = npc_info_iter["name"].lower().replace(' ', '_')
            npc_data_file = f"{npc_name_iter}.json"
            npc_data_iter = load_json_file(npc_data_file)
            if npc_data_iter:
                stats = {
                    "name": npc_info_iter["name"], 
                    "level": npc_data_iter.get("level", npc_info_iter.get("level", "N/A")),
                    "xp": npc_data_iter.get("experience_points", "N/A"),
                    "hp": npc_data_iter.get("hitPoints", "N/A"),
                    "max_hp": npc_data_iter.get("maxHitPoints", "N/A")
                }
                party_members_stats.append(stats)
        
        # Reload current location_data for the DM note based on party_tracker
        # This ensures location_data is fresh for each DM note construction
        current_area_id = party_tracker_data["worldConditions"]["currentAreaId"] 
        location_data = get_location_info( 
            party_tracker_data["worldConditions"]["currentLocation"],
            party_tracker_data["worldConditions"]["currentArea"],
            current_area_id
        )

        if party_members_stats:
            world_conditions = party_tracker_data["worldConditions"]
            date_time_str = f"{world_conditions['year']} {world_conditions['month']} {world_conditions['day']} {world_conditions['time']}"
            party_stats_formatted = []
            for stats_item in party_members_stats:
                member_data_for_note = load_json_file(f"{stats_item['name'].lower().replace(' ', '_')}.json")
                if member_data_for_note:
                    abilities = member_data_for_note.get("abilities", {})
                    ability_str = f"STR:{abilities.get('strength', 'N/A')} DEX:{abilities.get('dexterity', 'N/A')} CON:{abilities.get('constitution', 'N/A')} INT:{abilities.get('intelligence', 'N/A')} WIS:{abilities.get('wisdom', 'N/A')} CHA:{abilities.get('charisma', 'N/A')}"
                    next_level_xp_note = member_data_for_note.get("exp_required_for_next_level", "N/A")
                    party_stats_formatted.append(f"{stats_item['name']}: Level {stats_item['level']}, XP {stats_item['xp']}/{next_level_xp_note}, HP {stats_item['hp']}/{stats_item['max_hp']}, {ability_str}")

            party_stats_str = "; ".join(party_stats_formatted)
            current_location_name_note = world_conditions["currentLocation"]
            current_location_id_note = world_conditions["currentLocationId"]
            
            # --- START OF NEW/MODIFIED SECTION FOR CONNECTIVITY ---
            connected_locations_display_str = "None listed"
            connected_areas_display_str = "" # Initialize as empty

            if location_data: # Ensure location_data is not None
                # Get connections within the current area
                if "connectivity" in location_data and location_data["connectivity"]:
                    connected_ids_current_area = location_data["connectivity"]
                    connected_names_current_area = []
                    # Load the current area's full data to get names from IDs
                    current_area_full_data = load_json_file(f"{current_area_id}.json")
                    if current_area_full_data and "locations" in current_area_full_data:
                        for loc_id in connected_ids_current_area:
                            found_loc = next((l["name"] for l in current_area_full_data["locations"] if l["locationId"] == loc_id), loc_id)
                            connected_names_current_area.append(found_loc)
                    if connected_names_current_area:
                         connected_locations_display_str = ", ".join(connected_names_current_area)
                
                # Get connections to other areas
                if "areaConnectivity" in location_data and location_data["areaConnectivity"]:
                    area_names = location_data.get("areaConnectivity", [])
                    area_ids = location_data.get("areaConnectivityId", [])
                    area_connections_formatted = []
                    for i, name in enumerate(area_names):
                        conn_id = area_ids[i] if i < len(area_ids) else "Unknown ID"
                        # To get the *target location name* in the new area, we'd need to load that area's map/location file.
                        # For simplicity in the DM note, we can list the target area and its ID.
                        # The actual target location name for transition is handled by AI/transition logic.
                        # For now, let's just make it clear it's an area transition.
                        # If the AI needs the *specific entry point name* of the new area, this could be complex here.
                        # The AI's transitionLocation action should specify the newLocation name/ID based on map data.
                        # Here, we list the *area* it connects to.
                        # The `newLocation` parameter in `transitionLocation` will be the target room name/ID.
                        # The `areaConnectivity` field in location data usually lists *target room names* in the new area.
                        area_connections_formatted.append(f"{name} (via Area ID: {conn_id})")
                    
                    if area_connections_formatted:
                        connected_areas_display_str = ". Connects to new areas: " + ", ".join(area_connections_formatted)
            # --- END OF NEW/MODIFIED SECTION FOR CONNECTIVITY ---
            
            plot_data_for_note = load_json_file(f"plot_{current_area_id}.json") 
            current_plot_points = []
            if plot_data_for_note and "plotPoints" in plot_data_for_note:
                 current_plot_points = [
                    point for point in plot_data_for_note["plotPoints"]
                    if point["location"] == current_location_id_note and point["status"] != "completed"
                ]
            plot_points_str = "\n".join([f"- {point['title']}: {point['description']}" for point in current_plot_points])
            
            side_quests = []
            for point in current_plot_points:
                for quest in point.get("sideQuests", []):
                    if quest["status"] != "completed":
                        side_quests.append(f"- {quest['title']} (Status: {quest['status']}): {quest['description']}")
            side_quests_str = "\n".join(side_quests)

            traps_str = "None listed"
            if location_data and "traps" in location_data: 
                traps = location_data.get("traps", [])
                if traps:
                    traps_str = "\n".join([
                        f"- {trap['name']}: {trap['description']} (Detect DC: {trap['detectDC']}, Disable DC: {trap['disableDC']}, Trigger DC: {trap['triggerDC']}, Damage: {trap['damage']})"
                        for trap in traps
                    ])

            dm_note = (f"Dungeon Master Note: Current date and time: {date_time_str}. "
                f"Party stats: {party_stats_str}. "
                f"Current location: {current_location_name_note} ({current_location_id_note}). "
                # --- MODIFIED LINE TO INCLUDE CONNECTIVITY ---
                f"Adjacent locations in this area: {connected_locations_display_str}{connected_areas_display_str}.\n"
                # --- END OF MODIFIED LINE ---
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
        save_conversation_history(conversation_history)

        retry_count = 0
        valid_response_received = False 
        ai_response_content = None 

        while retry_count < 5 and not valid_response_received:
            ai_response_content = get_ai_response(conversation_history)
            validation_result = validate_ai_response(ai_response_content, user_input_text, validation_prompt_text, conversation_history, party_tracker_data)
            if validation_result is True:
                valid_response_received = True
                print(f"DEBUG: Valid response generated on attempt {retry_count + 1}")
                # Pass the same location_data that was used for the DM note construction
                result = process_ai_response(ai_response_content, party_tracker_data, location_data, conversation_history) 
                if result == "exit":
                    return
            elif isinstance(validation_result, str):
                print(f"Validation failed. Reason: {validation_result}")
                print(f"Retrying... (Attempt {retry_count + 1}/5)")
                conversation_history.append({
                    "role": "user",
                    "content": f"Error Note: Your previous response failed validation. Reason: {validation_result}. Please adjust your response accordingly."
                })
                retry_count += 1
            else: 
                print(f"DEBUG: Unexpected validation result: {validation_result}. Assuming invalid and retrying.")
                retry_count += 1


        if not valid_response_received:
            print("Failed to generate a valid response after 5 attempts. Proceeding with the last generated response.")
            if ai_response_content: 
                result = process_ai_response(ai_response_content, party_tracker_data, location_data, conversation_history) 
                if result == "exit":
                    return
            else:
                print("ERROR: No AI response was generated after retries.")
                conversation_history.append({"role": "assistant", "content": "I seem to be having trouble formulating a response. Could you try rephrasing your action or query?"})
                save_conversation_history(conversation_history)


        current_area_id = party_tracker_data["worldConditions"]["currentAreaId"] 
        plot_data = load_json_file(f"plot_{current_area_id}.json")
        campaign_name_updated = party_tracker_data.get("campaign", "").replace(" ", "_")
        campaign_data = load_json_file(f"{campaign_name_updated}_campaign.json")

        conversation_history = update_conversation_history(conversation_history, party_tracker_data, plot_data, campaign_data)
        conversation_history = update_character_data(conversation_history, party_tracker_data)
        conversation_history = ensure_main_system_prompt(conversation_history, main_system_prompt_text)
        
        # Re-apply the ordering logic here too
        main_prompt = None
        other_system_prompts = []
        non_system_messages = []

        for msg in conversation_history:
            if msg["role"] == "system":
                if msg["content"].startswith(main_system_prompt_text[:50]):
                    main_prompt = msg
                else:
                    other_system_prompts.append(msg)
            else:
                non_system_messages.append(msg)

        # Reconstruct with proper order
        conversation_history = []
        if main_prompt:
            conversation_history.append(main_prompt)
        conversation_history.extend(other_system_prompts)
        conversation_history.extend(non_system_messages)
        
        save_conversation_history(conversation_history)

if __name__ == "__main__":
    main_game_loop()