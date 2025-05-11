import json
from jsonschema import validate, ValidationError
from openai import OpenAI
import time
import re
import copy
from config import OPENAI_API_KEY

# ANSI escape codes
ORANGE = "\033[38;2;255;165;0m"
RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

# Constants
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.7

client = OpenAI(api_key=OPENAI_API_KEY)

def load_schema():
    with open("char_schema.json", "r") as schema_file:
        return json.load(schema_file)

def load_conversation_history():
    try:
        with open("conversation_history.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def process_conversation_history(history):
    for message in history:
        if message["role"] == "user" and message["content"].startswith("Leveling Dungeon Master Guidance"):
            message["content"] = "DM Guidance: Proceed with leveling up the player character or NPC given the 5th Edition role playing game rules. Only level the player or NPC one level at a time to ensure no mistakes are made. If you are leveling up an NPC then pass all changes at once using the 'updateNPCInfo' action. If you are leveling up a player character then you must ask the player for important decisions and choices they would have control over. After the player has provided the needed information then use the 'updatePlayerInfo' to pass all changes to the players character sheet and include the experience goal for the next level. Do not update the player's information in segements."
    return history

def update_player(player_name, changes, max_retries=3):
    # Load the current player info and schema
    with open(f"{player_name}.json", "r") as file:
        player_info = json.load(file)
    
    original_info = copy.deepcopy(player_info)  # Keep a copy of the original info
    schema = load_schema()

    # Load and process conversation history
    conversation_history = load_conversation_history()

    for attempt in range(max_retries):
        # Process the conversation history again right before creating the prompt
        processed_history = process_conversation_history(conversation_history)

        # Prepare the prompt for the AI
        prompt = [
            {"role": "system", "content": """You are an assistant that updates player information in a 5th Edition roleplaying game. Given the current player information and a description of changes, you must return only the updated sections as a JSON object. Do not include unchanged fields. Your response should be a valid JSON object representing only the modified parts of the character sheet. 
            
            You must also do the math based on what is contextually presented.

Here are examples of proper JSON structures:

1. Input: Update Norn's hit points to 30 out of 36 maximum.
   Output: {
     "hitpoints": 30,
     "maxhitpoints": 36
   }

2. Input: Add a Potion of Healing to Norn's inventory and update experience points to 4500.
   Output: {
     "equipment": [
       {
         "item_name": "Potion of Healing",
         "item_type": "miscellaneous",
         "description": "Heals 2d4+2 hit points when consumed",
         "quantity": 1
       }
     ],
     "experience_points": 4500
   }

3. Input: Update Norn's currency to 15 gold, 5 silver, and 20 copper pieces.
   Output: {
     "currency": {
       "gold": 15,
       "silver": 5,
       "copper": 20
     }
   }

4. Input: Add a new Throwing Axe to Norn's attack options.
   Output: {
     "attacksAndSpellcasting": [
       {
         "name": "Throwing Axe",
         "type": "ranged",
         "damage": "1d6 slashing",
         "description": "Can be thrown up to 20 feet"
       }
     ]
   }

5. Input: Norn used 2 arrows in combat. Update the arrow count in their ammunition.
   Output: {
     "ammunition": [
       {
         "name": "Arrows",
         "quantity": 18,
         "description": "Standard arrows for a bow"
       }
     ]
   }

6. Input: Thomas found 5 more darts and added them to their ammunition.
   Output: {
     "ammunition": [
       {
         "name": "Darts",
         "quantity": 25,
         "description": "Standard arrows for a bow"
       }
     ]
   }

Examples of inputs that don't require any changes to the player's information:
1. Input: Norn successfully dealt 6 damage to the orc.
   Output: {}  

Remember to use the 'ammunition' array for any changes to arrow counts or other ammunition types."""},
            *processed_history,
            {"role": "user", "content": f"Current player info: {json.dumps(player_info)}\n\nChanges to apply: {changes}\n\nRespond with ONLY the updated JSON object representing the changed sections of the character sheet, with no additional text or explanation."}
        ]

        # Get AI's response
        response = client.chat.completions.create(
            model=MODEL,
            temperature=TEMPERATURE,
            messages=prompt
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Write the raw AI response to a debug file
        with open("debug_player_update.json", "w") as debug_file:
            json.dump({"raw_ai_response": ai_response}, debug_file, indent=2)
        
        print(f"{ORANGE}DEBUG: Raw AI response written to debug_player_update.json{RESET}")
        
        # Remove markdown code blocks if present
        ai_response = re.sub(r'```json\n|\n```', '', ai_response)
        
        try:
            updates = json.loads(ai_response)
            
            # Apply updates to the player_info
            player_info = update_nested_dict(player_info, updates)
            
            # Validate the updated info against the schema
            validate(instance=player_info, schema=schema)
            
            # If we reach here, validation was successful
            print(f"{GREEN}DEBUG: Successfully updated and validated player info on attempt {attempt + 1}{RESET}")
            
            # Compare original and updated info
            diff = compare_json(original_info, player_info)
            print(f"{ORANGE}DEBUG: Changes made:{RESET}")
            print(json.dumps(diff, indent=2))
            
            # Save the updated player info
            with open(f"{player_name}.json", "w") as file:
                json.dump(player_info, file, indent=2)
            
            # Save the processed conversation history
            with open("conversation_history.json", "w") as file:
                json.dump(processed_history, file, indent=2)
            
            print(f"{ORANGE}DEBUG: {player_name}'s character information updated{RESET}")
            return player_info
            
        except json.JSONDecodeError as e:
            print(f"{ORANGE}DEBUG: AI response is not valid JSON. Error: {e}. Retrying...{RESET}")
        except ValidationError as e:
            print(f"{RED}ERROR: Updated info does not match the schema. Error: {e}. Retrying...{RESET}")
        
        # If we've reached the maximum number of retries, return the original player info
        if attempt == max_retries - 1:
            print(f"{RED}ERROR: Failed to update player info after {max_retries} attempts. Returning original player info.{RESET}")
            return original_info
        
        # Wait for a short time before retrying
        time.sleep(1)

    # This line should never be reached, but just in case:
    return original_info

def update_nested_dict(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = update_nested_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def compare_json(old, new):
    diff = {}
    for key in new:
        if key not in old:
            diff[key] = new[key]
        elif old[key] != new[key]:
            if isinstance(new[key], dict):
                nested_diff = compare_json(old[key], new[key])
                if nested_diff:
                    diff[key] = nested_diff
            else:
                diff[key] = new[key]
    return diff