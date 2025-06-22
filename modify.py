import json
import sys
from openai import OpenAI
from config import OPENAI_API_KEY, DM_MINI_MODEL

# Models
SCHEMA_UPDATER_MODEL = DM_MINI_MODEL

# Temperature
TEMPERATURE = 0.8

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def write_debug_output(content, filename="second_model_output.json"):
    try:
        with open(filename, "w") as debug_file:
            json.dump(content, debug_file, indent=2)
        print(f"Debug output written to {filename}")
    except Exception as e:
        print(f"Error writing debug output: {str(e)}")

def update_json_schema(ai_response, player_info, monster_info):
    print("Modifying player and encounter details...")

    # Load the character schema JSON
    with open("char_schema.json", "r") as file:
        char_schema = json.load(file)

    # Load the monster schema JSON
    with open("mon_schema.json", "r") as file:
        mon_schema = json.load(file)

    schema_updater_prompt = [
        {"role": "system", "content": f"Given a narrative describing events in a Dungeons & Dragons 5th Edition game affecting a player character and any mentioned monsters, update the JSON schemas to reflect the changes dictated by the storyline. Focus on updating the 'hitpoints', 'equipment', and 'attacksAndSpellcasting' fields, but return the full JSON structure for both the player character and the monster. Your output must strictly adhere to the provided JSON structure, containing no text or information before or after the JSON documents. Separate the two JSONs with a single line containing only three hyphens: '---'.\n\nCharacter Schema:\n{json.dumps(char_schema, indent=2)}\n\nMonster Schema:\n{json.dumps(mon_schema, indent=2)}\n\nCombat Information:\n{ai_response}\n\nCurrent Player Character JSON:\n{json.dumps(player_info, indent=2)}\n\nCurrent Monster JSON:\n{json.dumps(monster_info, indent=2)}"}
    ]

    while True:
        response = client.chat.completions.create(
            model=SCHEMA_UPDATER_MODEL,
            temperature=TEMPERATURE,
            messages=schema_updater_prompt
        )

        schema_updates = response.choices[0].message.content.strip()
        
        # Write debug output here
        write_debug_output({
            "prompt": schema_updater_prompt,
            "response": schema_updates
        })
        
        print("Second Model Output:")
        print(schema_updates)

        # Remove special characters and clean the JSON output
        schema_updates = schema_updates.replace("```json", "").replace("```", "").strip()

        try:
            schemas = schema_updates.split("---")
            
            if len(schemas) != 2:
                raise ValueError("Expected two schemas in the response")
            
            updated_player_info = json.loads(schemas[0].strip())
            updated_monster_info = json.loads(schemas[1].strip())

            print("Valid JSON schemas received. Exiting the second model.")

            # Update the JSON files based on the updated schemas
            player_name = updated_player_info["name"].lower().replace(" ", "_")
            player_file = f"{player_name}.json"
            with open(player_file, "w") as file:
                json.dump(updated_player_info, file, indent=2)
            print(f"{updated_player_info['name']} JSON file updated.")

            monster_name = updated_monster_info["name"].lower().replace(" ", "_")
            monster_file = f"{monster_name}.json"
            with open(monster_file, "w") as file:
                json.dump(updated_monster_info, file, indent=2)
            print(f"{updated_monster_info['name']} JSON file updated.")

            return updated_player_info, updated_monster_info

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Invalid JSON schema received. Error: {str(e)}. Retrying...")
            schema_updater_prompt.append({"role": "assistant", "content": schema_updates})
            schema_updater_prompt.append({"role": "user", "content": "The JSON schemas you provided are invalid or don't meet our requirements. Please provide two valid JSON objects, separated by a line containing only three hyphens: '---'. The first JSON object should be the full Player Character schema, and the second should be the full Monster schema. Ensure all JSON syntax is correct and try again."})

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python modify.py <ai_response_file> <player_info_file> <monster_info_file>")
        sys.exit(1)

    ai_response_file = sys.argv[1]
    player_info_file = sys.argv[2]
    monster_info_file = sys.argv[3]

    # Load AI's response from the file
    with open(ai_response_file, "r") as file:
        ai_response = file.read()

    # Load player character information from the JSON file
    with open(player_info_file, "r") as file:
        player_info = json.load(file)

    # Load monster information from the JSON file
    with open(monster_info_file, "r") as file:
        monster_info = json.load(file)

    # Call the update_json_schema function to update the relevant JSON schema
    player_info, monster_info = update_json_schema(ai_response, player_info, monster_info)