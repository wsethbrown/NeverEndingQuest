import json
import subprocess
import os
import re
from openai import OpenAI
from datetime import datetime, timedelta
from termcolor import colored

# Import other necessary modules
from combat_manager import run_combat_simulation
from plot_update import update_plot
from player_stats import get_player_stat
from update_world_time import update_world_time
from conversation_utils import update_conversation_history, update_character_data
import update_player_info
import update_npc_info

# Import new manager modules
import location_manager
import action_handler
from campaign_path_manager import CampaignPathManager

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
    path_manager = CampaignPathManager()
    npc_file = path_manager.get_npc_path(npc_name)
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
    path_manager = CampaignPathManager()
    area_file = path_manager.get_area_path(current_area_id)
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

def load_json_file(file_path):
    """Load a JSON file, with error handling"""
    return location_manager.load_json_file(file_path)

def process_conversation_history(history):
    print(f"DEBUG: Processing conversation history")
    for message in history:
        if message["role"] == "user" and message["content"].startswith("Leveling Dungeon Master Guidance"):
            message["content"] = "DM Guidance: Proceed with leveling up the player character or the party NPC given the 5th Edition role playing game rules. Only level the player character or party NPC one level at a time to ensure no mistakes are made. If you are leveling up a party NPC then pass all changes at once using the 'updateNPCInfo' action. If you are leveling up a player character then you must ask the player for important decisions and choices they would have control over. After the player has provided the needed information then use the 'updatePlayerInfo' to pass all changes to the players character sheet and include the experience goal for the next level. Do not update the player's information in segements."
    print(f"DEBUG: Conversation history processing complete")
    return history

def truncate_dm_notes(conversation_history):
    for message in conversation_history:
        if message["role"] == "user" and message["content"].startswith("Dungeon Master Note:"):
            parts = message["content"].split("Player:", 1)
            if len(parts) == 2:
                date_time = re.search(r"Current date and time: ([^.]+)", parts[0])
                if date_time:
                    message["content"] = f"Dungeon Master Note: {date_time.group(0)}. Player:{parts[1]}"
    return conversation_history

def extract_json_from_codeblock(text):
    match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def process_ai_response(response, party_tracker_data, location_data, conversation_history):
    global needs_conversation_history_update
    
    try:
        json_content = extract_json_from_codeblock(response)
        parsed_response = json.loads(json_content)

        narration = parsed_response.get("narration", "")
        print(colored("Dungeon Master:", "blue"), colored(narration, "blue"))

        conversation_history.append({"role": "assistant", "content": response})

        actions = parsed_response.get("actions", [])
        for action in actions:
            # Call action_handler to process each action
            result = action_handler.process_action(action, party_tracker_data, location_data, conversation_history)
            if result == "exit":
                return "exit"
            if isinstance(result, bool) and result:
                needs_conversation_history_update = True
            if isinstance(result, tuple) and result[0] == "skillCheck":  # This condition seems unlikely to be met now
                dm_note = result[1]
                conversation_history.append({"role": "user", "content": dm_note})
                new_response = get_ai_response(conversation_history)
                process_ai_response(new_response, party_tracker_data, location_data, conversation_history)

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
    """
    Ensure the main system prompt is first in the conversation history.
    This removes any existing instances of the main prompt and adds it at the beginning.
    """
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

def order_conversation_messages(conversation_history, main_system_prompt_text):
    """Order conversation messages with main system prompt first, followed by other system prompts"""
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
    ordered_history = []
    if main_prompt:
        ordered_history.append(main_prompt)
    ordered_history.extend(other_system_prompts)
    ordered_history.extend(non_system_messages)
    
    return ordered_history

def main_game_loop():
    global needs_conversation_history_update

    validation_prompt_text = load_validation_prompt() 

    with open("system_prompt.txt", "r") as file:
        main_system_prompt_text = file.read() 

    conversation_history = load_json_file(json_file) or []
    party_tracker_data = load_json_file("party_tracker.json")
    
    # Initialize path manager after loading party tracker
    path_manager = CampaignPathManager()
    
    current_area_id = party_tracker_data["worldConditions"]["currentAreaId"]
    location_data = location_manager.get_location_info( 
        party_tracker_data["worldConditions"]["currentLocation"],
        party_tracker_data["worldConditions"]["currentArea"],
        current_area_id
    )

    plot_data = load_json_file(path_manager.get_plot_path(current_area_id))
    
    campaign_name = party_tracker_data.get("campaign", "").replace(" ", "_")
    campaign_data = load_json_file(path_manager.get_campaign_file_path())

    conversation_history = ensure_main_system_prompt(conversation_history, main_system_prompt_text)
    conversation_history = update_conversation_history(conversation_history, party_tracker_data, plot_data, campaign_data)
    conversation_history = update_character_data(conversation_history, party_tracker_data)

    # Use the new order_conversation_messages function
    conversation_history = order_conversation_messages(conversation_history, main_system_prompt_text)
    
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
        player_data_file = path_manager.get_player_path(player_name_actual)
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
            member_file_path = path_manager.get_player_path(member_name_iter)
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
            npc_name_iter = npc_info_iter["name"]
            npc_data_file = path_manager.get_npc_path(npc_name_iter)
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
        location_data = location_manager.get_location_info( 
            party_tracker_data["worldConditions"]["currentLocation"],
            party_tracker_data["worldConditions"]["currentArea"],
            current_area_id
        )

        if party_members_stats:
            world_conditions = party_tracker_data["worldConditions"]
            date_time_str = f"{world_conditions['year']} {world_conditions['month']} {world_conditions['day']} {world_conditions['time']}"
            party_stats_formatted = []
            for stats_item in party_members_stats:
                # Check if this is a player or an NPC
                if stats_item['name'] in [p for p in party_tracker_data["partyMembers"]]:
                    member_data_for_note = load_json_file(path_manager.get_player_path(stats_item['name']))
                else:
                    member_data_for_note = load_json_file(path_manager.get_npc_path(stats_item['name']))
                if member_data_for_note:
                    abilities = member_data_for_note.get("abilities", {})
                    ability_str = f"STR:{abilities.get('strength', 'N/A')} DEX:{abilities.get('dexterity', 'N/A')} CON:{abilities.get('constitution', 'N/A')} INT:{abilities.get('intelligence', 'N/A')} WIS:{abilities.get('wisdom', 'N/A')} CHA:{abilities.get('charisma', 'N/A')}"
                    next_level_xp_note = member_data_for_note.get("exp_required_for_next_level", "N/A")
                    party_stats_formatted.append(f"{stats_item['name']}: Level {stats_item['level']}, XP {stats_item['xp']}/{next_level_xp_note}, HP {stats_item['hp']}/{stats_item['max_hp']}, {ability_str}")

            party_stats_str = "; ".join(party_stats_formatted)
            current_location_name_note = world_conditions["currentLocation"]
            current_location_id_note = world_conditions["currentLocationId"]
            
            # --- CONNECTIVITY SECTION ---
            connected_locations_display_str = "None listed"
            connected_areas_display_str = "" # Initialize as empty

            if location_data: # Ensure location_data is not None
                # Get connections within the current area
                if "connectivity" in location_data and location_data["connectivity"]:
                    connected_ids_current_area = location_data["connectivity"]
                    connected_names_current_area = []
                    # Load the current area's full data to get names from IDs
                    current_area_full_data = load_json_file(path_manager.get_area_path(current_area_id))
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
                        area_connections_formatted.append(f"{name} (via Area ID: {conn_id})")
                    
                    if area_connections_formatted:
                        connected_areas_display_str = ". Connects to new areas: " + ", ".join(area_connections_formatted)
            # --- END OF CONNECTIVITY SECTION ---
            
            plot_data_for_note = load_json_file(path_manager.get_plot_path(current_area_id)) 
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
                        f"- {trap.get('name', 'Unknown Trap')}: {trap.get('description', 'No description')} (Detect DC: {trap.get('detectDC', 'N/A')}, Disable DC: {trap.get('disableDC', 'N/A')}, Trigger DC: {trap.get('triggerDC', 'N/A')}, Damage: {trap.get('damage', 'N/A')})"
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
                "transitionLocation should always be used when the player expresses a desire to move to an adjacent location to their current location, "
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
        plot_data = load_json_file(path_manager.get_plot_path(current_area_id))
        campaign_name_updated = party_tracker_data.get("campaign", "").replace(" ", "_")
        campaign_data = load_json_file(path_manager.get_campaign_file_path())

        conversation_history = update_conversation_history(conversation_history, party_tracker_data, plot_data, campaign_data)
        conversation_history = update_character_data(conversation_history, party_tracker_data)
        conversation_history = ensure_main_system_prompt(conversation_history, main_system_prompt_text)
        
        # Use the new order_conversation_messages function
        conversation_history = order_conversation_messages(conversation_history, main_system_prompt_text)
        
        save_conversation_history(conversation_history)

if __name__ == "__main__":
    main_game_loop()