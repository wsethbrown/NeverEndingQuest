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

# Constants
MODEL = "gpt-4o-2024-08-06"
TEMPERATURE = 0.7

json_file = "conversation_history.json"
player_json_file = "player_conversation_history.json"

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
        model=MODEL,
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

def validate_ai_response(primary_response, user_input, validation_prompt):
    validation_conversation = [
        {"role": "system", "content": validation_prompt},
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": primary_response}
    ]
    
    validation_result = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        messages=validation_conversation
    )
    
    is_valid = validation_result.choices[0].message.content.strip().lower() == "yes"
    
    if is_valid:
        print("DEBUG: Validation passed successfully")
    
    return is_valid

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
        print(f"DEBUG: File {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"DEBUG: Invalid JSON in {file_path}.")
        return None
    except UnicodeDecodeError:
        print(f"DEBUG: Unable to decode {file_path} using UTF-8 encoding.")
        return None

def get_location_info(location_name, current_area):
    area_file = f"{current_area.lower().replace(' ', '_')}.json"
    locations = load_json_file(area_file)
    if locations and "locations" in locations:
        for location in locations["locations"]:
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

def update_world_conditions(current_conditions, new_location, current_area):
    current_time = datetime.strptime(current_conditions["time"], "%H:%M:%S")
    new_time = (current_time + timedelta(hours=1)).strftime("%H:%M:%S")

    location_info = get_location_info(new_location, current_area)
    
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
            "majorEventsUnderway": current_conditions["majorEventsUnderway"],
            "politicalClimate": "",
            "activeEncounter": "",
            "activeCombatEncounter": current_conditions.get("activeCombatEncounter", "")
        }
    else:
        return current_conditions

def handle_location_transition(current_location, new_location, current_area):
    print(f"DEBUG: Handling location transition from {current_location} to {new_location}")
    
    current_location_info = get_location_info(current_location, current_area)
    new_location_info = get_location_info(new_location, current_area)
    
    if current_location_info and new_location_info:
        with open("current_location.json", "w") as file:
            json.dump(new_location_info, file, indent=2)

        try:
            print("DEBUG: Running adv_summary.py to update area JSON")
            result = subprocess.run(["python", "adv_summary.py", "conversation_history.json", "current_location.json"], 
                                    check=True, capture_output=True, text=True)
            print("adv_summary.py output:", result.stdout)
            print("adv_summary.py error output:", result.stderr)
            print("DEBUG: adv_summary.py completed successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running adv_summary.py: {e}")
            print("Error output:", e.stderr)
            print("Standard output:", e.stdout)

        party_tracker = load_json_file("party_tracker.json")
        if party_tracker:
            party_tracker["worldConditions"] = update_world_conditions(party_tracker["worldConditions"], new_location, current_area)
            party_tracker["worldConditions"]["currentLocation"] = new_location
            party_tracker["worldConditions"]["currentLocationId"] = new_location_info["locationId"]
            party_tracker["worldConditions"]["weatherConditions"] = new_location_info.get("weatherConditions", "")
            
            print(f"DEBUG: Updating party_tracker.json with new location: {new_location}")
            with open("party_tracker.json", "w") as file:
                json.dump(party_tracker, file, indent=2)
            print("DEBUG: party_tracker.json updated successfully")

        return f"Describe the immediate surroundings and any notable features or encounters in {new_location}, based on its recent history and current state."
    else:
        print(f"ERROR: Could not find information for either {current_location} or {new_location}")
        return None

def process_conversation_history(history):
    print(f"DEBUG: Processing conversation history")
    for message in history:
        if message["role"] == "user" and message["content"].startswith("Leveling Dungeon Master Guidance"):
            message["content"] = "DM Guidance: Proceed with leveling up the player character or NPC given the 5th Edition game rules. Only level the player or NPC one level at a time to ensure no mistakes are made. If you are leveling up an NPC then pass all changes at once using the 'updateNPCInfo' action. If you are leveling up a player character then you must ask the player for important decisions and choices they would have control over. After the player has provided the needed information then use the 'updatePlayerInfo' to pass all changes to the players character sheet and include the experience goal for the next level. Do not update the player's information in segments."
    print(f"DEBUG: Conversation history processing complete")
    return history

def process_action(action, party_tracker_data, location_data, conversation_history, player_conversation_history):
    global needs_conversation_history_update
    action_type = action.get("action")
    parameters = action.get("parameters", {})
    
    if action_type == "skillCheck":
        stat_name = parameters["stat"]
        time_estimate = parameters["timeEstimate"]
        character_name = parameters.get("entityName", "").lower()
        is_npc = parameters.get("entityType", "").lower() == "npc"

        if is_npc:
            # Handle NPC skill check
            result = get_npc_stat(character_name, stat_name, time_estimate)
        else:
            # Player skill check logic
            player_name = next((member.lower() for member in party_tracker_data["partyMembers"]), None)
            if player_name:
                result = get_player_stat(player_name, stat_name, time_estimate)
            else:
                print("No player found in the party tracker data.")
                return None

        # Return the DM Note as a tuple with "skillCheck" role
        return ("skillCheck", f"DM Note: {result}")

    elif action_type == "createEncounter":
        print("DEBUG: Creating combat encounter")
        try:
            result = subprocess.run(
                ["python", "combat_builder.py"],
                input=json.dumps(action),
                check=True, capture_output=True, text=True
            )
            print("DEBUG: combat_builder.py output:", result.stdout)
            print("DEBUG: combat_builder.py error output:", result.stderr)
            print("DEBUG: Combat encounter created successfully")
            
            encounter_id = result.stdout.strip().split()[-1]
            
            party_tracker_data["worldConditions"]["activeCombatEncounter"] = encounter_id
            with open("party_tracker.json", "w") as file:
                json.dump(party_tracker_data, file, indent=2)
            print(f"DEBUG: Updated party tracker with combat encounter ID: {encounter_id}")
            
            dialogue_summary, updated_player_info = run_combat_simulation(encounter_id, party_tracker_data, location_data)
            
            player_name = next((member.lower() for member in party_tracker_data["partyMembers"]), None)
            if player_name:
                player_file = f"{player_name}.json"
                with open(player_file, "w") as file:
                    json.dump(updated_player_info, file, indent=2)
                print(f"DEBUG: Updated player file for {player_name}")
            
            conversation_history.append({"role": "user", "content": f"Note to DM: The combat was handled by another Dungeon Master and the summary is provided as follows. Please call actions to update the time and the party NPC experience points. The player's experience points were already updated and don't need to be updated again. When updating the time, make a reasonable estimate of the time the encounter would have taken: {dialogue_summary}"})
            
            # Get a new AI response based on the updated conversation history
            new_response = get_ai_response(conversation_history)

            # Process this new response
            process_ai_response(new_response, party_tracker_data, location_data, conversation_history, player_conversation_history)

            party_tracker_data["worldConditions"]["activeCombatEncounter"] = ""
            with open("party_tracker.json", "w") as file:
                json.dump(party_tracker_data, file, indent=2)
            #print("DEBUG: Cleared active combat encounter from party tracker")
            
        except Exception as e:
            print(f"Unexpected error occurred: {e}")

    elif action_type == "updateTime":
        time_estimate_str = str(parameters["timeEstimate"])
        update_world_time(time_estimate_str)

    elif action_type == "updatePlot":
        plot_point_id = parameters["plotPointId"]
        new_status = parameters["newStatus"]
        updated_plot = update_plot(plot_point_id, new_status)
        print(f"DEBUG: Plot updated for plot point {plot_point_id}")

    elif action_type == "exitGame":
        conversation_history.append({"role": "user", "content": "Dungeon Master Note: Resume the game, the player has returned."})
        save_conversation_history(conversation_history)
        exit_game()
    
    elif action_type == "transitionLocation":
        new_location = parameters["newLocation"]
        current_location = party_tracker_data["worldConditions"]["currentLocation"]
        current_area = party_tracker_data["worldConditions"]["currentArea"]
        print(f"DEBUG: Transitioning from {current_location} to {new_location}")
        transition_prompt = handle_location_transition(current_location, new_location, current_area)
        
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
        dm_note = f"Leveling Dungeon Master Guidance: Proceed with leveling up the player character or NPC given the 5th Edition game rules. Only level the player or NPC one level at a time to ensure no mistakes are made. If you are leveling up an NPC then pass all changes at once using the 'updateNPCInfo' action. If you are leveling up a player character then you must ask the player for important decisions and choices they would have control over. After the player has provided the needed information then use the 'updatePlayerInfo' to pass all changes to the players character sheet and include the experience goal for the next level. Do not update the player's information in segments. \n\n{leveling_info}"
        
        # Add DM Note to conversation history
        conversation_history.append({"role": "user", "content": dm_note})

        # Get a new AI response based on the updated conversation history
        new_response = get_ai_response(conversation_history)
        
        # Process this new response
        return process_ai_response(new_response, party_tracker_data, location_data, conversation_history, player_conversation_history)
    
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

def process_ai_response(response, party_tracker_data, location_data, conversation_history, player_conversation_history):
    try:
        json_content = extract_json_from_codeblock(response)
        parsed_response = json.loads(json_content)
        
        narration = parsed_response.get("narration", "")
        print(colored("Dungeon Master:", "blue"), colored(narration, "blue"))
        
        # Add the AI's response to the conversation history immediately
        conversation_history.append({"role": "assistant", "content": response})
        
        actions = parsed_response.get("actions", [])
        for action in actions:
            result = process_action(action, party_tracker_data, location_data, conversation_history, player_conversation_history)
            if result == "exit":
                return "exit"  # Propagate the exit signal
            if isinstance(result, tuple) and result[0] == "skillCheck":
                dm_note = result[1]
                # Add the DM Note to the conversation history as a user message
                conversation_history.append({"role": "user", "content": dm_note})
                # Get a new AI response based on the updated conversation history
                new_response = get_ai_response(conversation_history)
                # Process this new response
                process_ai_response(new_response, party_tracker_data, location_data, conversation_history, player_conversation_history)
        
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

def save_player_conversation_history(history):
    with open(player_json_file, "w") as file:
        json.dump(history, file, indent=2)

def get_ai_response(conversation_history):
    response = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        messages=conversation_history
    )
    return response.choices[0].message.content.strip()

def get_player_response(player_conversation_history):
    response = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        messages=player_conversation_history
    )
    return response.choices[0].message.content.strip()

def main_game_loop():
    global needs_conversation_history_update
    
    # Load the validation prompt
    validation_prompt = load_validation_prompt()

    # Load the system prompt
    with open("system_prompt.txt", "r") as file:
        system_prompt = file.read()

    # Initialize conversation history
    conversation_history = load_json_file(json_file) or []

    # Initialize player conversation history
    player_conversation_history = load_json_file(player_json_file) or []

    # Load initial data
    party_tracker_data = load_json_file("party_tracker.json")
    current_area = party_tracker_data["worldConditions"]["currentArea"]
    location_data = get_location_info(party_tracker_data["worldConditions"]["currentLocation"], current_area)
    plot_data = load_json_file("plot.json")
    map_data = load_json_file("map.json")

    # Ensure system prompt is at the beginning
    if not conversation_history or conversation_history[0]["role"] != "system" or conversation_history[0]["content"] != system_prompt:
        conversation_history = [{"role": "system", "content": system_prompt}] + [msg for msg in conversation_history if msg["role"] != "system"]

    # Load player character data
    player_name = next((member.lower() for member in party_tracker_data["partyMembers"]), None)
    player_data = load_json_file(f"{player_name}.json")
    player_system_prompt = f"""
    You are {player_data['name']}, a level {player_data['level']} {player_data['class']}. Your background is {player_data.get('background', '')}.
    Your abilities are: {player_data.get('abilities', {})}.
    Your personality traits are: {player_data.get('personality_traits', '')}.
    Act accordingly in the game, making decisions based on your character's personality and goals.
    Be decisive and take lead of the party and don't ask open ended questions.
    """

    # Ensure player's system prompt is at the beginning
    if not player_conversation_history or player_conversation_history[0]["role"] != "system" or player_conversation_history[0]["content"] != player_system_prompt:
        player_conversation_history = [{"role": "system", "content": player_system_prompt}] + [msg for msg in player_conversation_history if msg["role"] != "system"]

    # Add other system prompts
    conversation_history = update_conversation_history(conversation_history, party_tracker_data, plot_data, map_data)
    conversation_history = update_character_data(conversation_history, party_tracker_data)

    # Ensure all system prompts are at the beginning
    system_prompts = [msg for msg in conversation_history if msg["role"] == "system"]
    non_system_messages = [msg for msg in conversation_history if msg["role"] != "system"]
    conversation_history = system_prompts + non_system_messages

    # Save the initial conversation history
    save_conversation_history(conversation_history)
    save_player_conversation_history(player_conversation_history)

    # Get initial AI response to set the scene
    initial_ai_response = get_ai_response(conversation_history)
    process_ai_response(initial_ai_response, party_tracker_data, location_data, conversation_history, player_conversation_history)

    while True:
        # Truncate older Dungeon Master Notes
        conversation_history = truncate_dm_notes(conversation_history)
        
        if needs_conversation_history_update:
            conversation_history = process_conversation_history(conversation_history)
            save_conversation_history(conversation_history)
            needs_conversation_history_update = False
        
        if needs_summarization(conversation_history):
            conversation_history = summarize_conversation(conversation_history)
        
        # Get player input from AI model
        # Prepare the latest Dungeon Master's narration to send to the player model
        latest_dm_message = conversation_history[-1]["content"] if conversation_history else ""
        player_conversation_history.append({"role": "assistant", "content": latest_dm_message})

        # Save the player conversation history before getting the response
        save_player_conversation_history(player_conversation_history)

        # Get player response
        player_input_text = get_player_response(player_conversation_history)
        print(colored(f"{player_name.capitalize()}:", "green"), colored(player_input_text, "green"))

        # Add the player's response to their conversation history
        player_conversation_history.append({"role": "user", "content": player_input_text})

        # Save the player conversation history after player's response
        save_player_conversation_history(player_conversation_history)

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
                    "hp": member_data.get("hitpoints", "N/A"),
                    "max_hp": member_data.get("maxhitpoints", "N/A")
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
                    "hp": npc_data.get("hitPoints", npc_data.get("hitpoints", "N/A")),
                    "max_hp": npc_data.get("maxHitPoints", npc_data.get("maxhitpoints", "N/A"))
                }
                party_members_stats.append(stats)

        if party_members_stats:
            world_conditions = party_tracker_data["worldConditions"]
            date_time = f"{world_conditions['year']} {world_conditions['month']} {world_conditions['day']} {world_conditions['time']}"
            
            party_stats = "; ".join([f"{stats['name']}: Level {stats['level']}, XP {stats['xp']}, HP {stats['hp']}/{stats['max_hp']}" for stats in party_members_stats])
            
            dm_note = (f"Dungeon Master Note: Current date and time: {date_time}. "
                    f"Party stats: {party_stats}. "
                    "Remember to take actions if necessary such as skill checks, updating the plot, "
                    "time, character sheets, and location if changes occur. Always ask the players to roll for their skill checks. Keep an eye on everyone's XP and whether they can level. Proactively engage location NPCs with the party and dynamically include them in the conversation. Weave the plot elements into the adventure to ensure the player and party have enough clues. When appropriate, take opportunities to use party NPCs to engage and narrate the adventure instead of always speaking from the dungeon master's perspective.")
        else:
            dm_note = "Dungeon Master Note: Remember to take actions if necessary such as skill checks, updating the plot, time, character sheets, and location if changes occur."
        
        user_input_with_note = f"{dm_note} Player: {player_input_text}"
        conversation_history.append({"role": "user", "content": user_input_with_note})

        # Save conversation history after user input
        save_conversation_history(conversation_history)

        # Get AI response with validation
        retry_count = 0
        valid_response = False
        while retry_count < 5 and not valid_response:
            ai_response = get_ai_response(conversation_history)
            
            if validate_ai_response(ai_response, player_input_text, validation_prompt):
                valid_response = True
                print(f"DEBUG: Valid response generated on attempt {retry_count + 1}")
                result = process_ai_response(ai_response, party_tracker_data, location_data, conversation_history, player_conversation_history)
                if result == "exit":
                    return  # Exit the main_game_loop
            else:
                print(f"Validation failed. Retrying... (Attempt {retry_count + 1}/5)")
                retry_count += 1

        if not valid_response:
            print("Failed to generate a valid response after 5 attempts. Proceeding with the last generated response.")
            process_ai_response(ai_response, party_tracker_data, location_data, conversation_history, player_conversation_history)

        # Reload data and update system prompts for next iteration
        party_tracker_data = load_json_file("party_tracker.json")
        current_area = party_tracker_data["worldConditions"]["currentArea"]
        location_data = get_location_info(party_tracker_data["worldConditions"]["currentLocation"], current_area)
        plot_data = load_json_file("plot.json")
        map_data = load_json_file("map.json")
        conversation_history = update_conversation_history(conversation_history, party_tracker_data, plot_data, map_data)
        conversation_history = update_character_data(conversation_history, party_tracker_data)

        # Ensure system prompts are at the beginning after updates
        system_prompts = [msg for msg in conversation_history if msg["role"] == "system"]
        non_system_messages = [msg for msg in conversation_history if msg["role"] != "system"]
        conversation_history = system_prompts + non_system_messages

        # Save the updated conversation history
        save_conversation_history(conversation_history)
        save_player_conversation_history(player_conversation_history)

if __name__ == "__main__":
    main_game_loop()
