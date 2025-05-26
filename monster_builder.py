import json
import sys
import os
import re
from openai import OpenAI
from jsonschema import validate, ValidationError
# Import model configuration from config.py
from config import OPENAI_API_KEY # Assuming API key is in config.py
# We need a model name for monster_builder, let's assume it will be MONSTER_BUILDER_MODEL
# You'll need to add MONSTER_BUILDER_MODEL = "gpt-4.1-2025-04-14" (or your preferred model)
# to your config.py file.
from config import MONSTER_BUILDER_MODEL # This line will cause an error until you define it in config.py
from campaign_path_manager import CampaignPathManager

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

# Use OPENAI_API_KEY from config
client = OpenAI(api_key=OPENAI_API_KEY)
# Note: The original monster_builder.py had a hardcoded API key here.
# It's better practice to use the one from config.py.

def load_schema(file_name):
    try:
        with open(file_name, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"{RED}Error: File {file_name} not found.{RESET}")
        return None
    except json.JSONDecodeError:
        print(f"{RED}Error: Invalid JSON in {file_name}.{RESET}")
        return None

def save_json(file_name, data):
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_name)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            print(f"{YELLOW}Created directory: {directory}{RESET}")
        
        with open(file_name, 'w') as file:
            json.dump(data, file, indent=2)
        print(f"{GREEN}Successfully saved data to {file_name}{RESET}")
        return True
    except Exception as e:
        print(f"{RED}Error saving to {file_name}: {str(e)}{RESET}")
        return False

def generate_monster(monster_name, schema):
    prompt = [
        {"role": "system", "content": "You are an assistant that creates monster schema JSON files from a master monster schema template for a D&D 5e game. Given a monster name, create a JSON representation of the monster's stats and abilities according to D&D 5e rules following the monster schema template exactly. Be sure to follow the monster bestiary for naming normal monsters based on the name provided. For example, if the name is Orc_1, then your monster name is an Orc. If you are given a named monster or boss then you can create a unique monster schema with that name as it will be unique. Ensure your new monster JSON adheres to the provided schema template. Do not include any additional properties or nested 'type' and 'value' fields. Return only the JSON content without any markdown formatting."},
        {"role": "user", "content": f"Create a monster named '{monster_name}' using D&D 5e rules. Schema: {json.dumps(schema)}"}
    ]

    try:
        response = client.chat.completions.create(
            model=MONSTER_BUILDER_MODEL, # Use imported model name
            temperature=0.7,
            messages=prompt
        )

        ai_response = response.choices[0].message.content.strip()
        print(f"{YELLOW}AI Response:{RESET}\n{ai_response}")

        # Remove markdown code block if present
        ai_response = re.sub(r'^```json\s*|\s*```$', '', ai_response, flags=re.MULTILINE)

        try:
            monster_data = json.loads(ai_response)
            # Remove the outer "properties" object if it exists
            if "properties" in monster_data:
                monster_data = monster_data["properties"]
            # Remove nested 'value' fields if they exist
            monster_data = remove_nested_values(monster_data)
            validate(instance=monster_data, schema=schema)
            return monster_data
        except json.JSONDecodeError as e:
            print(f"{RED}Error: Invalid JSON in AI response. {str(e)}{RESET}")
            print(f"{YELLOW}Processed AI response:{RESET}\n{ai_response}")
        except ValidationError as e:
            print(f"{RED}Error: Generated monster data does not match schema. {str(e)}{RESET}")
            print(f"{YELLOW}Processed monster data:{RESET}\n{json.dumps(monster_data, indent=2)}") # Added indent for readability
    except Exception as e:
        print(f"{RED}Error: Failed to generate monster data. {str(e)}{RESET}")

    return None

def remove_nested_values(data):
    if isinstance(data, dict):
        return {k: remove_nested_values(v['value'] if isinstance(v, dict) and 'value' in v else v) for k, v in data.items()}
    elif isinstance(data, list):
        return [remove_nested_values(item) for item in data]
    else:
        return data

def main():
    if len(sys.argv) != 2:
        print(f"{RED}Usage: python monster_builder.py <monster_name>{RESET}")
        return

    monster_name_arg = sys.argv[1] # Renamed variable
    schema_data = load_schema("mon_schema.json") # Renamed variable
    if not schema_data:
        return

    generated_monster_data = generate_monster(monster_name_arg, schema_data) # Renamed variable
    if generated_monster_data:
        path_manager = CampaignPathManager()
        full_path = path_manager.get_monster_path(monster_name_arg)
        if save_json(full_path, generated_monster_data):
            print(f"{GREEN}Monster '{monster_name_arg}' created and saved to {full_path}{RESET}")
        else:
            print(f"{RED}Failed to save monster data{RESET}")
            sys.exit(1) # Ensure exit with error code
    else:
        print(f"{RED}Failed to generate monster data{RESET}")
        sys.exit(1)  # Exit with an error code

if __name__ == "__main__":
    main()