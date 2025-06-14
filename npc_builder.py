import json
import sys
import os
import re
from openai import OpenAI
from jsonschema import validate, ValidationError
# Import model configuration from config.py
from config import OPENAI_API_KEY, NPC_BUILDER_MODEL # Assuming API key might also be in config eventually
from module_path_manager import ModulePathManager

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

# Use OPENAI_API_KEY from config
client = OpenAI(api_key=OPENAI_API_KEY)
# Note: The original npc_builder.py had a hardcoded API key here.
# It's better practice to use the one from config.py.
# If your config.py does not yet have OPENAI_API_KEY, you'll need to add it or adjust.
# For now, I'll assume OPENAI_API_KEY is correctly defined in your config.py as used by other scripts.

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

def load_prompt(file_name):
    try:
        with open(file_name, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"{RED}Error: File {file_name} not found.{RESET}")
        return None
    except Exception as e:
        print(f"{RED}Error reading {file_name}: {str(e)}{RESET}")
        return None

def save_json(file_name, data):
    try:
        with open(file_name, 'w') as file:
            json.dump(data, file, indent=2)
        print(f"{GREEN}DEBUG: NPC save ({file_name}) - PASS{RESET}")
        return True
    except Exception as e:
        print(f"{RED}Error saving to {file_name}: {str(e)}{RESET}")
        return False

def generate_npc(npc_name, schema, npc_race=None, npc_class=None, npc_level=None, npc_background=None):
    system_prompt_text = load_prompt("npc_builder_prompt.txt") # Renamed variable
    if not system_prompt_text:
        return None

    system_message = f"""You are an assistant that creates NPC schema JSON files from a master NPC schema template for a 5e game. Given an NPC name and optional details, create a JSON representation of the NPC's stats and abilities according to 5e rules following the NPC schema template exactly. Ensure your new NPC JSON adheres to the provided schema template. Do not include any additional properties or nested 'type' and 'value' fields. Return only the JSON content without any markdown formatting.

Use the following rules information when creating the NPC:

{system_prompt_text}

Adhere strictly to 5e rules and the provided schema."""

    prompt_messages = [ # Renamed variable
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"Create an NPC named '{npc_name}' using 5e rules. Race: {npc_race or 'Any'}, Class: {npc_class or 'Any'}, Level: {npc_level or 'Any'}, Background: {npc_background or 'Any'}. Schema: {json.dumps(schema)}"}
    ]

    try:
        response = client.chat.completions.create(
            model=NPC_BUILDER_MODEL, # Use imported model name
            temperature=0.7,
            messages=prompt_messages
        )

        ai_response = response.choices[0].message.content.strip()
        #print(f"{YELLOW}AI Response:{RESET}\n{ai_response}")

        # Remove markdown code block if present
        ai_response = re.sub(r'^```json\s*|\s*```$', '', ai_response, flags=re.MULTILINE)

        try:
            npc_data = json.loads(ai_response)
            # Remove nested 'value' fields if they exist
            npc_data = remove_nested_values(npc_data)
            validate(instance=npc_data, schema=schema)
            return npc_data
        except json.JSONDecodeError as e:
            print(f"{RED}Error: Invalid JSON in AI response. {str(e)}{RESET}")
            print(f"{YELLOW}Processed AI response:{RESET}\n{ai_response}")
        except ValidationError as e:
            print(f"{RED}Error: Generated NPC data does not match schema. {str(e)}{RESET}")
            print(f"{YELLOW}Problematic NPC data:{RESET}\n{json.dumps(npc_data, indent=2)}") # Log problematic data
    except Exception as e:
        print(f"{RED}Error: Failed to generate NPC data. {str(e)}{RESET}")

    return None

def remove_nested_values(data):
    if isinstance(data, dict):
        # Check if it's a dict with only 'value' and possibly 'type' keys
        # This was a specific pattern you wanted to remove.
        # However, the more general approach from generate_npc was:
        # remove_nested_values(v['value'] if isinstance(v, dict) and 'value' in v else v)
        # Let's stick to the logic that was in generate_npc for this function.
        new_dict = {}
        for k, v in data.items():
            if isinstance(v, dict) and 'value' in v and len(v) == 1: # Simple {'value': ...} case
                new_dict[k] = remove_nested_values(v['value'])
            elif isinstance(v, dict) and 'value' in v and 'type' in v and len(v) == 2: # {'type':..., 'value':...} case
                 new_dict[k] = remove_nested_values(v['value'])
            else:
                new_dict[k] = remove_nested_values(v)
        return new_dict
    elif isinstance(data, list):
        return [remove_nested_values(item) for item in data]
    else:
        return data

def main():
    if len(sys.argv) < 2:
        print(f"{RED}Usage: python npc_builder.py <npc_name> [race] [class] [level] [background]{RESET}")
        sys.exit(1)

    npc_name_arg = sys.argv[1] # Renamed variable
    npc_race_arg = sys.argv[2] if len(sys.argv) > 2 else None # Renamed variable
    npc_class_arg = sys.argv[3] if len(sys.argv) > 3 else None # Renamed variable
    npc_level_arg = None # Renamed variable
    if len(sys.argv) > 4 and sys.argv[4].isdigit():
        try:
            npc_level_arg = int(sys.argv[4])
        except ValueError:
            print(f"{RED}Error: Level must be an integer.{RESET}")
            sys.exit(1)
    elif len(sys.argv) > 4 and not sys.argv[4].isdigit() and sys.argv[4] != '': # handle empty string for level
        print(f"{RED}Error: Level must be an integer or empty if not specified.{RESET}")
        sys.exit(1)


    npc_background_arg = sys.argv[5] if len(sys.argv) > 5 else None # Renamed variable

    print(f"DEBUG: Received arguments - Name: {npc_name_arg}, Race: {npc_race_arg}, Class: {npc_class_arg}, Level: {npc_level_arg}, Background: {npc_background_arg}")

    npc_schema_data = load_schema("char_schema.json") # Use unified character schema
    if not npc_schema_data:
        sys.exit(1)

    generated_npc_data = generate_npc(npc_name_arg, npc_schema_data, npc_race_arg, npc_class_arg, npc_level_arg, npc_background_arg) # Renamed variable
    if generated_npc_data:
        path_manager = ModulePathManager()
        full_path = path_manager.get_character_unified_path(npc_name_arg)  # Force unified path
        
        # Ensure characters directory exists
        characters_dir = os.path.dirname(full_path)
        os.makedirs(characters_dir, exist_ok=True)
        if save_json(full_path, generated_npc_data):
            print(f"{GREEN}DEBUG: NPC creation ({npc_name_arg}) - PASS{RESET}")
        else:
            print(f"{RED}DEBUG: NPC save ({npc_name_arg}) - FAIL{RESET}")
            sys.exit(1)
    else:
        print(f"{RED}DEBUG: NPC creation ({npc_name_arg}) - FAIL{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()