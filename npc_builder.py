import json
import sys
import os
import re
from openai import OpenAI
from jsonschema import validate, ValidationError

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

client = OpenAI(api_key="sk-proj-YHoOCk08nxYvZss63drnT3BlbkFJa6f5DH7hbOfwkwrAcnGc")

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
        print(f"{GREEN}Successfully saved data to {file_name}{RESET}")
        return True
    except Exception as e:
        print(f"{RED}Error saving to {file_name}: {str(e)}{RESET}")
        return False

def generate_npc(npc_name, schema, npc_race=None, npc_class=None, npc_level=None, npc_background=None):
    system_prompt = load_prompt("npc_builder_prompt.txt")
    if not system_prompt:
        return None

    system_message = f"""You are an assistant that creates NPC schema JSON files from a master NPC schema template for a D&D 5e game. Given an NPC name and optional details, create a JSON representation of the NPC's stats and abilities according to D&D 5e rules following the NPC schema template exactly. Ensure your new NPC JSON adheres to the provided schema template. Do not include any additional properties or nested 'type' and 'value' fields. Return only the JSON content without any markdown formatting.

Use the following rules information when creating the NPC:

{system_prompt}

Adhere strictly to D&D 5e rules and the provided schema."""

    prompt = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"Create an NPC named '{npc_name}' using D&D 5e rules. Race: {npc_race or 'Any'}, Class: {npc_class or 'Any'}, Level: {npc_level or 'Any'}, Background: {npc_background or 'Any'}. Schema: {json.dumps(schema)}"}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            temperature=0.7,
            messages=prompt
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
    except Exception as e:
        print(f"{RED}Error: Failed to generate NPC data. {str(e)}{RESET}")
    
    return None

def remove_nested_values(data):
    if isinstance(data, dict):
        return {k: remove_nested_values(v['value'] if isinstance(v, dict) and 'value' in v else v) for k, v in data.items()}
    elif isinstance(data, list):
        return [remove_nested_values(item) for item in data]
    else:
        return data

def main():
    if len(sys.argv) < 2:
        print(f"{RED}Usage: python npc_builder.py <npc_name> [race] [class] [level] [background]{RESET}")
        sys.exit(1)

    npc_name = sys.argv[1]
    npc_race = sys.argv[2] if len(sys.argv) > 2 else None
    npc_class = sys.argv[3] if len(sys.argv) > 3 else None
    npc_level = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else None
    npc_background = sys.argv[5] if len(sys.argv) > 5 else None

    print(f"DEBUG: Received arguments - Name: {npc_name}, Race: {npc_race}, Class: {npc_class}, Level: {npc_level}, Background: {npc_background}")

    schema = load_schema("npc_schema.json")
    if not schema:
        sys.exit(1)

    npc_data = generate_npc(npc_name, schema, npc_race, npc_class, npc_level, npc_background)
    if npc_data:
        file_name = f"{npc_name.lower().replace(' ', '_')}.json"
        current_dir = os.getcwd()
        full_path = os.path.join(current_dir, file_name)
        if save_json(full_path, npc_data):
            print(f"{GREEN}NPC '{npc_name}' created and saved to {full_path}{RESET}")
        else:
            print(f"{RED}Failed to save NPC data{RESET}")
            sys.exit(1)
    else:
        print(f"{RED}Failed to generate NPC data{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()