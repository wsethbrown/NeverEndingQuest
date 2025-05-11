import json
import copy
from jsonschema import validate, ValidationError
from openai import OpenAI
import time
import re
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

# Constants
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.7

# ANSI escape codes
ORANGE = "\033[38;2;255;165;0m"
RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

def load_schema():
    with open("npc_schema.json", "r") as schema_file:
        return json.load(schema_file)

def load_conversation_history():
    try:
        with open("conversation_history.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

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

def update_npc(npc_name, changes, max_retries=3):
    print(f"{ORANGE}DEBUG: Starting NPC update for {npc_name}{RESET}")
    # Load the current NPC info and schema
    with open(f"{npc_name.lower().replace(' ', '_')}.json", "r") as file:
        npc_info = json.load(file)
    
    original_info = copy.deepcopy(npc_info)  # Keep a copy of the original info
    schema = load_schema()

    # Load conversation history
    conversation_history = load_conversation_history()

    for attempt in range(max_retries):
        # Prepare the prompt for the AI
        prompt = [
            {"role": "system", "content": """You are an assistant that updates NPC information in the world's most popular 5th Edition roleplaying game. Given the current NPC information and a description of changes, you must return only the updated sections as a JSON object. Do not include unchanged fields. Your response should be a valid JSON object representing only the modified parts of the NPC sheet.
            
            You must also do the math based on what is contextually presented. 

            For example, if the input states the party NPC used 3 arrows in combat then you will need to remove 3 arrows from their current total before passing the final amount. IF the party NPC started with 17 arrows and uses 3 in combat then you will update the ammunition total for the arrows to 14.

            Guidance on updating ammunition. If the item already exists, increase its quantity.

Here are examples of proper JSON structures:

Examples of inputs requiring updates to the JSON:
1. Input: Update Grunk the Orc's hit points to 30 out of 45 maximum.
   Output: {
     "hitPoints": 30,
     "maxHitPoints": 45
   }

2. Input: Add a Potion of Healing to Grunk's equipment and update experience points to 2000.
   Output: {
     "equipment": [
       {
         "item_name": "Potion of Healing",
         "item_type": "miscellaneous",
         "description": "Heals 2d4+2 hit points when consumed",
         "quantity": 1
       }
     ],
     "experience_points": 2000
   }

3. Input: Level up Grunk to level 5, increasing strength to 18, adding Athletics skill, and gaining Extra Attack feature.
   Output: {
     "level": 5,
     "abilities": {
       "strength": 18
     },
     "skills": {
       "Athletics": 6
     },
     "specialAbilities": [
       {
         "name": "Extra Attack",
         "description": "You can attack twice, instead of once, whenever you take the Attack action on your turn."
       }
     ],
     "proficiencyBonus": 3
   }

4. Input: Update Grunk's currency to 15 gold, 5 silver, and 20 copper pieces.
   Output: {
     "currency": {
       "gold": 15,
       "silver": 5,
       "copper": 20
     }
   }

5. Input: Add a new Throwing Axe to Grunk's actions.
   Output: {
     "actions": [
       {
         "name": "Throwing Axe",
         "attackBonus": 5,
         "damageDice": "1d6",
         "damageBonus": 3,
         "damageType": "slashing"
       }
     ]
   }
   
6. Input: Patrick used 2 arrows in combat. Update the arrow count in their ammunition.
   Output: {
     "ammunition": [
       {
         "name": "Arrows",
         "quantity": 18,
         "description": "Standard arrows for a bow"
       }
     ]
   }

7. Input: Thomas found 5 more darts and added them to their ammunition.
   Output: {
     "ammunition": [
       {
         "name": "Darts",
         "quantity": 25,
         "description": "Standard arrows for a bow"
       }
     ]
   }

Important: Be aware of schema restrictions. For example, the 'status' field only accepts 'alive', 'dead', or 'unconscious'. Do not use values outside of these options.

Example of an error scenario:
Input: Update Elara's status to conscious after waking up from being knocked out.
Incorrect output: {
  "status": "conscious"
}
Correct output: {
  "status": "alive"
}

   Examples of incorrect inputs that don't require any changes to the NPC's information:
   1. Input: Harmus successfully dealt 6 damage to the orc.
   Output: {}
   """},
            *conversation_history,
            {"role": "user", "content": f"Current NPC info: {json.dumps(npc_info)}\n\nChanges to apply: {changes}\n\nRespond with ONLY the updated JSON object representing the changed sections of the NPC sheet, with no additional text or explanation."}
        ]

        # Get AI's response
        response = client.chat.completions.create(
            model=MODEL,
            temperature=TEMPERATURE,
            messages=prompt
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Write the raw AI response to a debug file
        with open("debug_npc_update.json", "w") as debug_file:
            json.dump({"raw_ai_response": ai_response}, debug_file, indent=2)
        
        print(f"{ORANGE}DEBUG: Raw AI response written to debug_npc_update.json{RESET}")
        
        # Remove markdown code blocks if present
        ai_response = re.sub(r'```json\n|\n```', '', ai_response)
        
        try:
            updates = json.loads(ai_response)
            
            # Apply updates to the NPC info
            npc_info = update_nested_dict(npc_info, updates)
            
            # Check for any new top-level keys
            new_keys = set(npc_info.keys()) - set(original_info.keys())
            if new_keys:
                print(f"{RED}WARNING: New top-level keys detected: {new_keys}. These will be removed.{RESET}")
                for key in new_keys:
                    del npc_info[key]
            
            # Validate the updated info against the schema
            validate(instance=npc_info, schema=schema)
            
            # If we reach here, validation was successful
            print(f"{GREEN}DEBUG: Successfully updated and validated NPC info on attempt {attempt + 1}{RESET}")
            
            # Compare original and updated info
            diff = compare_json(original_info, npc_info)
            print(f"{ORANGE}DEBUG: Changes made:{RESET}")
            print(json.dumps(diff, indent=2))
            
            # Save the updated NPC info
            with open(f"{npc_name.lower().replace(' ', '_')}.json", "w") as file:
                json.dump(npc_info, file, indent=2)
            
            print(f"{ORANGE}DEBUG: {npc_name}'s information updated{RESET}")
            return npc_info
            
        except json.JSONDecodeError as e:
            print(f"{ORANGE}DEBUG: AI response is not valid JSON. Error: {e}. Retrying...{RESET}")
        except ValidationError as e:
            print(f"{RED}ERROR: Updated info does not match the schema. Error: {e}. Retrying...{RESET}")
        
        # If we've reached the maximum number of retries, return the original NPC info
        if attempt == max_retries - 1:
            print(f"{RED}ERROR: Failed to update NPC info after {max_retries} attempts. Returning original NPC info.{RESET}")
            return original_info
        
        # Wait for a short time before retrying
        time.sleep(1)

    # This line should never be reached, but just in case:
    return original_info