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

client = OpenAI(api_key="sk-proj-YHoOCk08nxYvZss63drnT3BlbkFJa6f5DH7hbOfwkwrAcnGc")

json_file = "conversation_history.json"

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
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {file_path}.")
        return None
    except UnicodeDecodeError:
        print(f"Error: Unable to decode {file_path} using UTF-8 encoding.")
        return None

def get_location_info(location_name):
    locations = load_json_file("location.json")
    if locations and "locations" in locations:
        for location in locations["locations"]:
            if location["name"] == location_name:
                return location
    return None

def update_world_conditions(current_conditions, new_location):
    current_time = datetime.strptime(current_conditions["time"], "%H:%M:%S")
    new_time = (current_time + timedelta(hours=1)).strftime("%H:%M:%S")

    location_info = get_location_info(new_location)
    
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
            "majorEventsUnderway": current_conditions["majorEventsUnderway"],
            "politicalClimate": "",
            "activeEncounter": "",
            "activeCombatEncounter": current_conditions.get("activeCombatEncounter", "")
        }
    else:
        return current_conditions

def handle_location_transition(current_location, new_location):
    print(f"DEBUG: Handling location transition from {current_location} to {new_location}")
    
    current_location_info = get_location_info(current_location)
    new_location_info = get_location_info(new_location)
    
    if current_location_info and new_location_info:
        with open("current_location.json", "w") as file:
            json.dump(current_location_info, file, indent=2)

        try:
            print("DEBUG: Running adv_summary.py to update location.json")
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
            party_tracker["worldConditions"] = update_world_conditions(party_tracker["worldConditions"], new_location)
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

def process_action(action, party_tracker_data, location_data, conversation_history):
    action_type = action.get("action")
    parameters = action.get("parameters", {})
    
    if action_type == "skillCheck":
        stat_name = parameters["stat"]
        time_estimate = parameters["timeEstimate"]
        player_name = next((member.lower() for member in party_tracker_data["partyMembers"] if member.lower() == "norn"), None)

        if player_name:
            result = get_player_stat(player_name, stat_name, time_estimate)
            # Return the DM Note as a tuple with "user" role
            return ("skillCheck", f"DM Note: {result}")
        else:
            print("Player not found in the party tracker data.")
            return None

    elif action_type == "createEncounter":
        print("DEBUG: Creating combat encounter")
        try:
            result = subprocess.run(
                ["python", "combat_builder.py"],
                input=json.dumps(action),
                check=True, capture_output=True, text=True
            )
            print("combat_builder.py output:", result.stdout)
            print("combat_builder.py error output:", result.stderr)
            print("DEBUG: Combat encounter created successfully")
            
            encounter_id = result.stdout.strip().split()[-1]
            
            party_tracker_data["worldConditions"]["activeCombatEncounter"] = encounter_id
            with open("party_tracker.json", "w") as file:
                json.dump(party_tracker_data, file, indent=2)
            print(f"DEBUG: Updated party tracker with combat encounter ID: {encounter_id}")
            
            dialogue_summary, updated_player_info = run_combat_simulation(encounter_id, party_tracker_data, location_data)
            
            player_name = next((member.lower() for member in party_tracker_data["partyMembers"] if member.lower() == "norn"), None)
            if player_name:
                player_file = f"{player_name}.json"
                with open(player_file, "w") as file:
                    json.dump(updated_player_info, file, indent=2)
                print(f"DEBUG: Updated player file for {player_name}")
            
            conversation_history.append({"role": "user", "content": f"Note to DM: The combat was handled by another Dungeon Master and the summary is provided as follows. All updates have been made to the character except for time. Make no other updates other than to update the time the combat encounter would take: {dialogue_summary}"})
            
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

    elif action_type == "transitionLocation":
        new_location = parameters["newLocation"]
        current_location = party_tracker_data["worldConditions"]["currentLocation"]
        print(f"DEBUG: Transitioning from {current_location} to {new_location}")
        transition_prompt = handle_location_transition(current_location, new_location)
        
        if transition_prompt:
            conversation_history.append({"role": "system", "content": f"Location transition: {current_location} to {new_location}"})
            print("DEBUG: Location transition complete")
        else:
            print("ERROR: Failed to handle location transition")

    elif action_type == "updatePlayerInfo":
        print(f"DEBUG: Processing updatePlayerInfo action")
        changes = parameters["changes"]
        player_name = next((member.lower() for member in party_tracker_data["partyMembers"] if member.lower() == "norn"), None)
        
        if player_name:
            print(f"DEBUG: Updating player info for {player_name}")
            try:
                updated_player_info = update_player_info.update_player(player_name, changes)
                print(f"DEBUG: Player info updated successfully")
            except Exception as e:
                print(f"ERROR: Failed to update player info: {str(e)}")
        else:
            print("ERROR: Player not found in the party tracker data.")
    
    elif action_type == "updateNPCInfo":
        print(f"DEBUG: Processing updateNPCInfo action")
        changes = parameters["changes"]
        npc_name = parameters["npcName"]
        
        print(f"DEBUG: Updating NPC info for {npc_name}")
        try:
            updated_npc_info = update_npc_info.update_npc(npc_name, changes)
            print(f"DEBUG: NPC info updated successfully")
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
    print("DEBUG: Conversation history saved successfully")

def get_ai_response(conversation_history):
    response = client.chat.completions.create(
        #model="gpt-4o",
        model="gpt-4o-2024-08-06",
        temperature=0.7,
        messages=conversation_history
    )
    return response.choices[0].message.content.strip()

def main_game_loop():
    # Load the system prompt
    with open("system_prompt.txt", "r") as file:
        system_prompt = file.read()

    # Initialize conversation history
    conversation_history = load_json_file(json_file) or []

    # Load initial data
    location_data = load_json_file("location.json")
    party_tracker_data = load_json_file("party_tracker.json")
    plot_data = load_json_file("plot.json")
    map_data = load_json_file("map.json")

    # Ensure system prompt is at the beginning
    if not conversation_history or conversation_history[0]["role"] != "system" or conversation_history[0]["content"] != system_prompt:
        conversation_history = [{"role": "system", "content": system_prompt}] + [msg for msg in conversation_history if msg["role"] != "system"]

    # Add other system prompts
    conversation_history = update_conversation_history(conversation_history, location_data, party_tracker_data, plot_data, map_data)
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
        # Get user input
        user_input_text = input("User: ")
        
        # Load the latest party tracker data
        party_tracker_data = load_json_file("party_tracker.json")
        
        # Get the player's name from party tracker
        player_name = next((member.lower() for member in party_tracker_data["partyMembers"] if member.lower() == "norn"), None)
        
        if player_name:
            # Load the player's JSON file
            player_data = load_json_file(f"{player_name}.json")
            
            # Extract relevant information
            world_conditions = party_tracker_data["worldConditions"]
            date_time = f"{world_conditions['year']} {world_conditions['month']} {world_conditions['day']} {world_conditions['time']}"
            
            # Extract core stats
            hp = player_data["hitpoints"]
            max_hp = player_data["maxhitpoints"]
            level = player_data["level"]
            xp = player_data["experience_points"]
            
            # Create the note to DM
            dm_note = (f"Dungeon Master Note: Current date and time: {date_time}. "
                    f"Player {player_name.capitalize()}: Level {level}, XP {xp}, HP {hp}/{max_hp}. "
                    "Remember to take actions if necessary such as skill checks, updating the plot, "
                    "time, character sheet, and location if changes occur. Always ask the player to roll for their skill check.")
        else:
            dm_note = "Dungeon Master Note: Remember to take actions if necessary such as skill checks, updating the plot, time, character sheet, and location if changes occur."
        
        user_input_with_note = f"{dm_note} Player: {user_input_text}"
        conversation_history.append({"role": "user", "content": user_input_with_note})

        # Save conversation history after user input
        save_conversation_history(conversation_history)

        # Get AI response
        ai_response = get_ai_response(conversation_history)
        
        # Process AI response (this now includes saving the response to conversation history)
        process_ai_response(ai_response, party_tracker_data, location_data, conversation_history)

        # Reload data and update system prompts for next iteration
        location_data = load_json_file("location.json")
        party_tracker_data = load_json_file("party_tracker.json")
        plot_data = load_json_file("plot.json")
        map_data = load_json_file("map.json")
        conversation_history = update_conversation_history(conversation_history, location_data, party_tracker_data, plot_data, map_data)
        conversation_history = update_character_data(conversation_history, party_tracker_data)

        # Ensure system prompts are at the beginning after updates
        system_prompts = [msg for msg in conversation_history if msg["role"] == "system"]
        non_system_messages = [msg for msg in conversation_history if msg["role"] != "system"]
        conversation_history = system_prompts + non_system_messages

        # Save the updated conversation history
        save_conversation_history(conversation_history)

if __name__ == "__main__":
    main_game_loop()