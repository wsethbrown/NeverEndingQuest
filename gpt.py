import json
from openai import OpenAI

client = OpenAI(api_key="sk-proj-YHoOCk08nxYvZss63drnT3BlbkFJa6f5DH7hbOfwkwrAcnGc")

conversation_history = [
    {"role": "system", "content": "You are a world class dungeon master. Interact with players based on the setting provided to you. If the situation starts a combat then respond with <action>combat<action>"}
]

json_file = "conversation_history.json"
try:
    with open(json_file, "r") as file:
        conversation_history.extend(json.load(file))
except FileNotFoundError:
    pass

# Read the encounter data from the JSON file
try:
    with open("encounter_E101.json", "r") as file:
        encounter_data = json.load(file)
except FileNotFoundError:
    print("encounter_E101.json not found. Starting the conversation without encounter data.")
    encounter_data = None
except json.JSONDecodeError:
    print("encounter_E101.json has an invalid JSON format. Starting the conversation without encounter data.")
    encounter_data = None

# Create the first user message with the encounter data
first_user_message = "Here's the encounter data:\n"
if encounter_data:
    first_user_message += f"Encounter Data: {json.dumps(encounter_data, indent=2)}\n"
else:
    first_user_message += "No encounter data available.\n"

first_user_message += "Narrate this encounter."

user_input = {"role": "user", "content": first_user_message}
conversation_history.append(user_input)

while True:
    # Get AI's response
    response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=conversation_history
    )
    ai_response = response.choices[0].message.content.strip()
    assistant_output = {"role": "assistant", "content": ai_response}
    conversation_history.append(assistant_output)
    print("Assistant:", ai_response)

    # Get user's input
    user_input_text = input("User: ")
    user_input = {"role": "user", "content": user_input_text}
    conversation_history.append(user_input)

    # Save conversation history to JSON file
    with open(json_file, "w") as file:
        json.dump(conversation_history[1:], file, indent=2)

    user_choice = input("Continue the conversation? (y/n): ")
    if user_choice.lower() != 'y':
        break