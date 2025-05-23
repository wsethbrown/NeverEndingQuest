import json
import copy
from jsonschema import validate, ValidationError
from openai import OpenAI
import time
import re
# Import model configuration from config.py
from config import OPENAI_API_KEY, NPC_INFO_UPDATE_MODEL
from campaign_path_manager import CampaignPathManager
from file_operations import safe_write_json, safe_read_json

client = OpenAI(api_key=OPENAI_API_KEY)

# Constants
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
    data = safe_read_json("conversation_history.json")
    return data if data else []

def format_schema_for_prompt(schema):
    """Format schema information for inclusion in the prompt"""
    schema_info = "NPC Schema - Valid fields and values:\n\n"
    
    properties = schema.get('properties', {})
    
    # Group fields by type for better readability
    simple_fields = []
    enum_fields = []
    array_fields = []
    object_fields = []
    
    for field, definition in properties.items():
        field_type = definition.get('type', 'unknown')
        
        if 'enum' in definition:
            enum_fields.append(f"- {field}: Must be one of {definition['enum']}")
        elif field_type == 'array':
            items_type = definition.get('items', {}).get('type', 'object')
            if items_type == 'object':
                # For arrays of objects, show the required structure
                array_fields.append(f"- {field}: Array of objects with required fields")
            else:
                array_fields.append(f"- {field}: Array of {items_type}")
        elif field_type == 'object':
            object_fields.append(f"- {field}: Object with nested properties")
        else:
            simple_fields.append(f"- {field}: {field_type}")
    
    # Combine all field types
    if enum_fields:
        schema_info += "Enumerated fields (must use exact values):\n"
        schema_info += "\n".join(enum_fields) + "\n\n"
    
    if simple_fields:
        schema_info += "Simple fields:\n"
        schema_info += "\n".join(simple_fields) + "\n\n"
    
    if array_fields:
        schema_info += "Array fields:\n"
        schema_info += "\n".join(array_fields) + "\n\n"
    
    if object_fields:
        schema_info += "Complex object fields:\n"
        schema_info += "\n".join(object_fields) + "\n\n"
    
    # Add specific examples for the problematic fields
    schema_info += """IMPORTANT: Two different attack array formats:

1. Actions array format (use for D&D standard attacks):
{
  "name": "string",
  "attackBonus": integer,
  "damageDice": "string",
  "damageBonus": integer,
  "damageType": "string"
}

2. AttacksAndSpellcasting array format (use for simplified tracking):
{
  "name": "string",
  "type": "melee" | "ranged" | "spell",
  "damage": "string",
  "description": "string"
}

Equipment array items:
{
  "item_name": "string",
  "item_type": "weapon" | "armor" | "miscellaneous",
  "description": "string",
  "quantity": integer
}

Currency object:
{
  "gold": integer,
  "silver": integer,
  "copper": integer
}

Abilities object:
{
  "strength": integer,
  "dexterity": integer,
  "constitution": integer,
  "intelligence": integer,
  "wisdom": integer,
  "charisma": integer
}"""
    
    return schema_info

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
    
    # Enhanced debug logging
    debug_update_log = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "npc_name": npc_name,
        "incoming_changes": changes,
        "attempts": []
    }
    # Load the current NPC info and schema
    path_manager = CampaignPathManager()
    npc_file_path = path_manager.get_npc_path(npc_name)
    npc_info = safe_read_json(npc_file_path)
    if not npc_info:
        print(f"{RED}ERROR: Could not read NPC file for '{npc_name}' at path: {npc_file_path}{RESET}")
        return None

    original_info = copy.deepcopy(npc_info)  # Keep a copy of the original info
    schema = load_schema()

    # Load conversation history
    conversation_history = load_conversation_history()

    for attempt in range(max_retries):
        # Format the schema for the prompt
        schema_info = format_schema_for_prompt(schema)

        # Prepare the prompt for the AI
        prompt = [
            {"role": "system", "content": f"""You are an assistant that updates NPC information in the world's most popular 5th Edition roleplaying game. Given the current NPC information and a description of changes, you must return only the updated sections as a JSON object. Do not include unchanged fields. Your response should be a valid JSON object representing only the modified parts of the NPC sheet.

{schema_info}

You must also do the math based on what is contextually presented. 

For example, if the input states the party NPC used 3 arrows in combat then you will need to remove 3 arrows from their current total before passing the final amount. IF the party NPC started with 17 arrows and uses 3 in combat then you will update the ammunition total for the arrows to 14.

Guidance on updating ammunition. If the item already exists, increase its quantity.

Here are examples of proper JSON structures:

Examples of inputs requiring updates to the JSON:
1. Input: Update Grunk the Orc's hit points to 30 out of 45 maximum.
   Output: {{
     "hitPoints": 30,
     "maxHitPoints": 45
   }}

2. Input: Add a Potion of Healing to Grunk's equipment and update experience points to 2000.
   Output: {{
     "equipment": [
       {{
         "item_name": "Potion of Healing",
         "item_type": "miscellaneous",
         "description": "Heals 2d4+2 hit points when consumed",
         "quantity": 1
       }}
     ],
     "experience_points": 2000
   }}

3. Input: Level up Grunk to level 5, increasing strength to 18, adding Athletics skill, and gaining Extra Attack feature.
   Output: {{
     "level": 5,
     "abilities": {{
       "strength": 18
     }},
     "skills": {{
       "Athletics": 6
     }},
     "specialAbilities": [
       {{
         "name": "Extra Attack",
         "description": "You can attack twice, instead of once, whenever you take the Attack action on your turn."
       }}
     ],
     "proficiencyBonus": 3
   }}

4. Input: Update Grunk's currency to 15 gold, 5 silver, and 20 copper pieces.
   Output: {{
     "currency": {{
       "gold": 15,
       "silver": 5,
       "copper": 20
     }}
   }}

5. Input: Add a new Throwing Axe to Grunk's actions (D&D format).
   Output: {{
     "actions": [
       {{
         "name": "Throwing Axe",
         "attackBonus": 5,
         "damageDice": "1d6",
         "damageBonus": 3,
         "damageType": "slashing"
       }}
     ]
   }}

6. Input: Patrick used 2 arrows in combat. Update the arrow count in their ammunition.
   Output: {{
     "ammunition": [
       {{
         "name": "Arrows",
         "quantity": 18,
         "description": "Standard arrows for a bow"
       }}
     ]
   }}

7. Input: Thomas found 5 more darts and added them to their ammunition.
   Output: {{
     "ammunition": [
       {{
         "name": "Darts",
         "quantity": 25,
         "description": "Standard arrows for a bow"
       }}
     ]
   }}

8. Input: Update Elara's status to alive after waking up from being knocked out.
   Output: {{
     "status": "alive"
   }}

9. Input: Elara is affected by multiple conditions: blinded and frightened.
   Output: {{
     "condition": "blinded",
     "condition_affected": ["frightened"]
   }}

Important: Be aware of schema restrictions. For example, the 'status' field only accepts 'alive', 'dead', or 'unconscious'. Do not use values outside of these options.

Example of an error scenario:
Input: Update Elara's status to conscious after waking up from being knocked out.
Incorrect output: {{
  "status": "conscious"
}}
Correct output: {{
  "status": "alive"
}}

Examples of incorrect inputs that don't require any changes to the NPC's information:
1. Input: Harmus successfully dealt 6 damage to the orc.
   Output: {{}}

Combat damage examples that should NOT update actions:
10. Input: Marcus hits the goblin with his mace, dealing 8 damage.
    Output: {{}}
    
11. Input: Luna's firebolt spell hits the skeleton for 9 fire damage.
    Output: {{}}
    
12. Input: Thorin attacks the orc with his battleaxe, scoring a critical hit for 15 damage.
    Output: {{}}
    
13. Input: Lyra fires her crossbow at the bandit, dealing 6 piercing damage.
    Output: {{}}

IMPORTANT: When NPCs deal damage in combat (e.g., "hits for X damage", "deals X damage", "scores a hit"), DO NOT update the actions or attacksAndSpellcasting arrays. These arrays define the NPC's available attacks, not track damage dealt. Only update these arrays when:
- Adding new weapons or spells
- Changing weapon stats (attack bonus, damage dice)
- Removing weapons or abilities

Combat damage dealt is tracked elsewhere and should not modify the NPC's action definitions.

Remember to:
- Only include fields that are being changed
- Use the exact values specified in the schema for enumerated fields
- Include all required properties for complex objects like equipment and actions
- Use the 'ammunition' array for any changes to arrow counts or other ammunition types
- Choose the correct format (actions vs attacksAndSpellcasting) based on what you're updating. If both exist, only update the one that contains the weapon/spell being modified. Never update weapon definitions when the NPC simply uses them in combat."""},
            *conversation_history,
            {"role": "user", "content": f"Current NPC info: {json.dumps(npc_info)}\n\nChanges to apply: {changes}\n\nRespond with ONLY the updated JSON object representing the changed sections of the NPC sheet, with no additional text or explanation."}
        ]

        # Log the attempt details
        attempt_log = {
            "attempt_number": attempt + 1,
            "prompt_sent": prompt[-1]["content"]  # Just log the user message
        }
        
        print(f"{ORANGE}DEBUG: Sending changes to AI for interpretation (Attempt {attempt + 1}):{RESET}")
        print(f"{ORANGE}Changes: {changes}{RESET}")
        
        # Get AI's response
        response = client.chat.completions.create(
            model=NPC_INFO_UPDATE_MODEL, # Use imported model name
            temperature=TEMPERATURE,
            messages=prompt
        )

        ai_response = response.choices[0].message.content.strip()

        # Enhanced debug logging  
        attempt_log["ai_response"] = ai_response
        print(f"{ORANGE}DEBUG: AI response received:{RESET}")
        print(f"{ORANGE}{ai_response}{RESET}")

        # Write the raw AI response to a debug file
        safe_write_json("debug_npc_update.json", {
            "attempt": attempt + 1,
            "npc_name": npc_name,
            "changes": changes,
            "raw_ai_response": ai_response
        }, create_backup=False)

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
            
            # Add success to log
            attempt_log["success"] = True
            attempt_log["parsed_updates"] = updates
            debug_update_log["attempts"].append(attempt_log)

            # Compare original and updated info
            diff = compare_json(original_info, npc_info)
            print(f"{ORANGE}DEBUG: Changes made:{RESET}")
            print(json.dumps(diff, indent=2))
            
            debug_update_log["final_diff"] = diff
            debug_update_log["success"] = True

            # Save the updated NPC info with atomic write
            if not safe_write_json(npc_file_path, npc_info):
                print(f"{RED}ERROR: Failed to save NPC file for {npc_name}{RESET}")
                return original_info

            print(f"{ORANGE}DEBUG: {npc_name}'s information updated{RESET}")
            
            # Append to debug log (read existing, append, write back)
            existing_log = safe_read_json("npc_update_detailed_log.json") or []
            if isinstance(existing_log, dict):
                existing_log = [existing_log]
            existing_log.append(debug_update_log)
            safe_write_json("npc_update_detailed_log.json", existing_log, create_backup=False)
            
            return npc_info

        except json.JSONDecodeError as e:
            print(f"{ORANGE}DEBUG: AI response is not valid JSON. Error: {e}. Retrying...{RESET}")
            attempt_log["json_decode_error"] = str(e)
            debug_update_log["attempts"].append(attempt_log)
        except ValidationError as e:
            print(f"{RED}ERROR: Updated info does not match the schema. Error: {e}. Retrying...{RESET}")
            attempt_log["validation_error"] = {
                "error_message": str(e),
                "error_path": list(e.path),
                "failing_instance": e.instance
            }
            debug_update_log["attempts"].append(attempt_log)

        # If we've reached the maximum number of retries, return the original NPC info
        if attempt == max_retries - 1:
            print(f"{RED}ERROR: Failed to update NPC info after {max_retries} attempts. Returning original NPC info.{RESET}")
            
            # Write final failure debug log
            debug_update_log["success"] = False
            debug_update_log["error"] = "Failed after all retries"
            
            # Append to debug log (read existing, append, write back)
            existing_log = safe_read_json("npc_update_detailed_log.json") or []
            if isinstance(existing_log, dict):
                existing_log = [existing_log]
            existing_log.append(debug_update_log)
            safe_write_json("npc_update_detailed_log.json", existing_log, create_backup=False)
                
            return original_info

        # Wait for a short time before retrying
        time.sleep(1)

    # This line should never be reached, but just in case:
    return original_info