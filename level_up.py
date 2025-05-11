# level_up.py

import json
from jsonschema import validate
from openai import OpenAI
from update_player_info import update_player, load_schema

client = OpenAI(api_key="sk-proj-YHoOCk08nxYvZss63drnT3BlbkFJa6f5DH7hbOfwkwrAcnGc")

def load_leveling_info():
    with open("leveling_info.txt", "r") as file:
        return file.read().strip()

def level_up_character(character_name):
    # Load character data and schema
    file_name = f"{character_name}.json"
    schema = load_schema()

    with open(file_name, "r") as file:
        character_data = json.load(file)
    
    current_level = character_data['level']
    new_level = current_level + 1

    # Load leveling information
    leveling_info = load_leveling_info()

    # Initialize conversation history
    conversation_history = [
        {"role": "system", "content": f"You are a 5th Edition role playing game character leveling assistant. You're helping level up the character {character_name} from level {current_level} to level {new_level}. Here's the current character data:\n\n{json.dumps(character_data, indent=2)}\n\nAnd here's the leveling information:\n\n{leveling_info}"},
        {"role": "system", "content": "Engage in a natural conversation with the player about leveling up their character. Ask questions about their choices, explain the options available, and guide them through the process. Once all decisions are made, provide a summary of changes."},
        {"role": "system", "content": "After the summary, provide a JSON representation of the updated character data, starting with 'JSON UPDATE:'. Include all fields from the original character data, updating only what has changed due to leveling up."}
    ]

    # Start the leveling conversation
    while True:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=conversation_history
        )

        assistant_message = response.choices[0].message.content.strip()
        print(f"\nDungeon Master: {assistant_message}")
        conversation_history.append({"role": "assistant", "content": assistant_message})

        if "JSON UPDATE:" in assistant_message.upper():
            break

        user_input = input("\nPlayer: ")
        conversation_history.append({"role": "user", "content": user_input})

    # Extract the JSON update from the assistant's last message
    json_update = assistant_message.split("JSON UPDATE:")[-1].strip()
    
    try:
        updated_character = json.loads(json_update)
        validate(instance=updated_character, schema=schema)
        
        # Save the updated character data
        with open(file_name, "w") as file:
            json.dump(updated_character, file, indent=2)
        
        print(f"\n{character_name} has been successfully leveled up to level {new_level}.")
        
        # Save the conversation history
        with open(f"{character_name.lower()}_level_up_conversation.json", "w") as file:
            json.dump(conversation_history, file, indent=2)
        
        print(f"The level-up conversation has been saved to {character_name.lower()}_level_up_conversation.json")
        
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Error updating character data: {e}")
        print("Please review the AI's output and try again.")

if __name__ == "__main__":
    character_name = input("Enter character name: ")
    level_up_character(character_name)