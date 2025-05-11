import json
import encounter
from openai import OpenAI
from player_stats import get_player_stat
from conversation_utils import update_conversation_history
from update_party_tracker import update_party_tracker

client = OpenAI(api_key="sk-proj-YHoOCk08nxYvZss63drnT3BlbkFJa6f5DH7hbOfwkwrAcnGc")

json_file = "conversation_history.json"

# Load conversation history from the JSON file if it exists
try:
    with open(json_file, "r") as file:
        conversation_history = json.load(file)
except FileNotFoundError:
    conversation_history = [
        {"role": "system", "content": "You are a world class dungeon master who delights in telling warm and intricate stories. Interact with your player based on the settings and other information provided to you and keep the context of your narration within the limits of the information provided. Talk to the player as if he/she is the actual character. Ask questions about action directly and roleplay the outcomes. You must take a turn based approached identicial to Dungeons and Dragons. The player must choose every action. If the situation starts a combat encounter then respond with only <combat>. You will then be provided the results of the initiative, combat rolls, damage and outcome. Narrate this as a tactical dungeon master using dramatic flair! If an NPC or monster needs to make a skill check respond with <skillcheck> only. If the player needs to make a skill check, ask the player to roll their dice and then you must wait for their response. After the player provides their role, respond only with <getplayerskill(stat)><(your time estimate in minutes)> and then wait for the results to be provided to you. For example, if you need the wisdom modifier and the activity would take two minutes then respond with <getplayerskill(wisdom)><2>. You may only chose a getplayerskill(stat) to be a choice of wisdom, strength, dexterity, charisma, intelligence, or constitution. In all cases where you are requesting actions, wait for the results before continuing."}
    ]

# Read the location data from the JSON file
try:
    with open("location.json", "r") as file:
        location_data = json.load(file)
except FileNotFoundError:
    print("location.json not found. Starting the conversation without location data.")
    location_data = None
except json.JSONDecodeError:
    print("location.json has an invalid JSON format. Starting the conversation without location data.")
    location_data = None

# Read the party tracker data from the JSON file
try:
    with open("party_tracker.json", "r") as file:
        party_tracker_data = json.load(file)
except FileNotFoundError:
    print("party_tracker.json not found. Starting the conversation without party tracker data.")
    party_tracker_data = None
except json.JSONDecodeError:
    print("party_tracker.json has an invalid JSON format. Starting the conversation without party tracker data.")
    party_tracker_data = None

# Read the player stats from the JSON file
player_name = None
if party_tracker_data:
    for member in party_tracker_data["party"]:
        if member["isPlayerCharacter"]:
            player_name = member["name"].lower()
            break

if player_name:
    player_file = f"{player_name}.json"
    try:
        with open(player_file, "r") as file:
            player_stats = json.load(file)
    except FileNotFoundError:
        print(f"{player_file} not found. Starting the conversation without player stats.")
        player_stats = None
    except json.JSONDecodeError:
        print(f"{player_file} has an invalid JSON format. Starting the conversation without player stats.")
        player_stats = None
else:
    print("No player character found in the party tracker. Starting the conversation without player stats.")
    player_stats = None

while True:
    # Update the party_tracker.json with the player's information
    party_tracker_data = update_party_tracker(player_name, player_stats, party_tracker_data)
    
    # Update the conversation history with the latest location and party tracker data
    conversation_history = update_conversation_history(conversation_history, location_data, party_tracker_data)

    # Get AI's response
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        temperature=0.7,
        messages=conversation_history
    )
    ai_response = response.choices[0].message.content.strip()

    # Add the AI's response to the conversation history
    assistant_output = {"role": "assistant", "content": ai_response}
    conversation_history.append(assistant_output)

    # Save the updated conversation history to the JSON file
    with open(json_file, "w") as file:
        json.dump(conversation_history, file, indent=2)

    # Check if the AI's response contains any action phrases
    if "<getplayerskill(" in ai_response:
        # Extract the stat name and time estimate from the action phrase
        start_index = ai_response.index("<getplayerskill(") + len("<getplayerskill(")
        end_index = ai_response.index(")>", start_index)
        stat_name = ai_response[start_index:end_index]

        # Extract the time estimate from the action phrase
        if "<" in ai_response[end_index:]:
            start_index = ai_response.index("<", end_index) + len("<")
            end_index = ai_response.index(">", start_index)
            time_estimate = ai_response[start_index:end_index]
            print(f"Time estimate found: {time_estimate} minutes")
        else:
            time_estimate = "0"  # Default time estimate if not provided
            print("No time estimate found. Using default value of 0 minutes.")

        # Call the get_player_stat function to retrieve the player's stat and update the time
        user_input_text = get_player_stat(player_name, stat_name, time_estimate)

        # Add the user's response to the conversation history
        user_input = {"role": "user", "content": user_input_text}
        conversation_history.append(user_input)

        # Get the model's response based on the player's stat
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            temperature=0.5,
            messages=conversation_history
        )
        ai_response = response.choices[0].message.content.strip()

    elif "<combat>" in ai_response:
        # Read the party tracker data from the JSON file
        with open("party_tracker.json", "r") as file:
            party_tracker_data = json.load(file)

        # Extract the active encounter from the party tracker data
        active_encounter = party_tracker_data["worldState"]["activeEncounter"]

        # Construct the file path for the encounter JSON file
        file_path = f"encounter_{active_encounter}.json"

        # Append the <combat> output to the conversation history
        assistant_output = {"role": "assistant", "content": "<combat>"}
        conversation_history.append(assistant_output)

        # Activate the encounter.py script
        encounter_data = encounter.roll_initiative(file_path)
        encounter.handle_encounter(encounter_data, file_path)

        # Remove the <combat> tag from the AI's response
        ai_response = ai_response.replace("<combat>", "")

        # Read the updated encounter data from the JSON file
        with open(file_path, "r") as encounter_file:
            updated_encounter_data = json.load(encounter_file)

        # Extract the encounter history from the updated encounter data
        encounter_history = updated_encounter_data["history"]

        # Format the encounter history for the model
        formatted_history = "\n".join(
            [f"Encounter Details:\n" + "\n".join(encounter_history[0]["encounter_details"])] +
            ["\n".join(round_data) for round_data in encounter_history[1:]]
        )

        # Append the formatted encounter history to the AI's response
        ai_response += f"\n\nEncounter History:\n{formatted_history}"

        # Add the AI's response to the conversation history
        assistant_output = {"role": "assistant", "content": ai_response}
        conversation_history.append(assistant_output)
        print("Dungeon Master:", ai_response)
    
    else:
        print("Dungeon Master:", ai_response)

        # Get user's input
        user_input_text = input("User: ")
        user_input = {"role": "user", "content": user_input_text}
        conversation_history.append(user_input)

    # Save conversation history to JSON file
    with open(json_file, "w") as file:
        json.dump(conversation_history, file, indent=2)