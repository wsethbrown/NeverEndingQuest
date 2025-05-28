import json
from jsonschema import validate, ValidationError
from openai import OpenAI
import time
import re
import copy
# Import model configuration from config.py
from config import OPENAI_API_KEY, PLAYER_INFO_UPDATE_MODEL
from campaign_path_manager import CampaignPathManager
from file_operations import safe_write_json, safe_read_json

# ANSI escape codes
ORANGE = "\033[38;2;255;165;0m"
RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

# Constants
TEMPERATURE = 0.7
VALIDATION_TEMPERATURE = 0.1  # Lower temperature for validation

client = OpenAI(api_key=OPENAI_API_KEY)

def load_schema():
    with open("char_schema.json", "r") as schema_file:
        return json.load(schema_file)

def load_conversation_history():
    data = safe_read_json("conversation_history.json")
    return data if data else []

def process_conversation_history(history):
    for message in history:
        if message["role"] == "user" and message["content"].startswith("Leveling Dungeon Master Guidance"):
            message["content"] = "DM Guidance: Proceed with leveling up the player character or NPC given the 5th Edition role playing game rules. Only level the player or NPC one level at a time to ensure no mistakes are made. If you are leveling up an NPC then pass all changes at once using the 'updateNPCInfo' action. If you are leveling up a player character then you must ask the player for important decisions and choices they would have control over. After the player has provided the needed information then use the 'updatePlayerInfo' to pass all changes to the players character sheet and include the experience goal for the next level. Do not update the player's information in segements."
    return history

def format_schema_for_prompt(schema):
    """Format schema information for inclusion in the prompt"""
    schema_info = "Character Schema - Valid fields and values:\n\n"
    
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
    
    # Add specific examples for common complex fields
    schema_info += """Common field structures:

Equipment array items:
{
  "item_name": "string",
  "item_type": "weapon" | "armor" | "miscellaneous",
  "description": "string",
  "quantity": integer
}

AttacksAndSpellcasting array items:
{
  "name": "string",
  "attackBonus": integer,
  "damageDice": "string",
  "damageBonus": integer,
  "damageType": "string",
  "type": "melee" | "ranged" | "spell",
  "description": "string"
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

def update_player(player_name, changes, max_retries=3):
    # Load the current player info and schema
    path_manager = CampaignPathManager()
    player_file_path = path_manager.get_player_path(player_name)
    player_info = safe_read_json(player_file_path)
    if not player_info:
        print(f"{RED}ERROR: Could not read player file for {player_name}{RESET}")
        return None

    original_info = copy.deepcopy(player_info)  # Keep a copy of the original info
    schema = load_schema()

    # Load and process conversation history
    conversation_history = load_conversation_history()

    for attempt in range(max_retries):
        # Process the conversation history again right before creating the prompt
        processed_history = process_conversation_history(conversation_history)

        # Format the schema for the prompt
        schema_info = format_schema_for_prompt(schema)

        # Prepare the prompt for the AI
        prompt = [
            {"role": "system", "content": f"""You are an assistant that updates player information in a 5th Edition roleplaying game. Given the current player information and a description of changes, you must return only the updated sections as a JSON object. Do not include unchanged fields. Your response should be a valid JSON object representing only the modified parts of the character sheet.

{schema_info}

CRITICAL RULES FOR ARRAYS (equipment, ammunition, etc.):
- When ADDING items: Return the COMPLETE array including all existing items PLUS the new items
- When REMOVING/USING/EXPENDING items: Return the COMPLETE array with those items removed
- When UPDATING quantities: Return the COMPLETE array with updated quantities
- NEVER return a partial array with only new/changed items
- NEVER return an empty array unless explicitly clearing all items
- The system will REPLACE the entire array with what you return

You must also do the math based on what is contextually presented.

Here are examples of proper JSON structures:

1. Input: Update Norn's hit points to 30 out of 36 maximum.
   Output: {{
     "hitPoints": 30,
     "maxHitPoints": 36
   }}

2. Input: Add a Potion of Healing to Norn's inventory (which already contains a sword and shield) and update experience points to 4500.
   Output: {{
     "equipment": [
       {{
         "item_name": "Longsword",
         "item_type": "weapon",
         "description": "Versatile weapon",
         "quantity": 1
       }},
       {{
         "item_name": "Shield", 
         "item_type": "armor",
         "description": "+2 AC",
         "quantity": 1
       }},
       {{
         "item_name": "Potion of Healing",
         "item_type": "miscellaneous",
         "description": "Heals 2d4+2 hit points when consumed",
         "quantity": 1
       }}
     ],
     "experience_points": 4500
   }}

3. Input: Update Norn's currency to 15 gold, 5 silver, and 20 copper pieces.
   Output: {{
     "currency": {{
       "gold": 15,
       "silver": 5,
       "copper": 20
     }}
   }}

4. Input: Add a new Throwing Axe to Norn's attack options.
   Output: {{
     "attacksAndSpellcasting": [
       {{
         "name": "Throwing Axe",
         "attackBonus": 5,
         "damageDice": "1d6",
         "damageBonus": 3,
         "damageType": "slashing",
         "type": "ranged",
         "description": "Can be thrown up to 20 feet"
       }}
     ]
   }}

5. Input: Norn used 2 arrows in combat. Update the arrow count in their ammunition.
   Output: {{
     "ammunition": [
       {{
         "name": "Arrows",
         "quantity": 18,
         "description": "Standard arrows for a bow"
       }}
     ]
   }}

6. Input: Thomas found 5 more darts and added them to their ammunition.
   Output: {{
     "ammunition": [
       {{
         "name": "Darts",
         "quantity": 25,
         "description": "Standard arrows for a bow"
       }}
     ]
   }}

7. Input: Norn becomes unconscious and prone.
   Output: {{
     "status": "unconscious",
     "condition": "prone"
   }}

8. Input: Norn is affected by multiple conditions: blinded and frightened.
   Output: {{
     "condition": "blinded",
     "condition_affected": ["frightened"]
   }}

Examples of inputs that don't require any changes to the player's information:
1. Input: Norn successfully dealt 6 damage to the orc.
   Output: {{}}  

Remember to:
- Only include fields that are being changed
- Use the exact values specified in the schema for enumerated fields
- Include all required properties for complex objects like equipment and attacks
- Use the 'ammunition' array for any changes to arrow counts or other ammunition types
- FOR ARRAYS: Always return the COMPLETE updated array, not just new/changed items
- NEVER return empty arrays unless explicitly clearing all items

Example of WRONG approach:
Input: Used potion of healing from inventory
WRONG Output: {"equipment": []}  // This deletes ALL equipment!

Example of CORRECT approach:
Input: Used potion of healing from inventory (player has sword, shield, potion)
CORRECT Output: {"equipment": [{"item_name": "Longsword", ...}, {"item_name": "Shield", ...}]}  // Potion removed, other items kept"""},
            *processed_history,
            {"role": "user", "content": f"Current player info: {json.dumps(player_info)}\n\nChanges to apply: {changes}\n\nRespond with ONLY the updated JSON object representing the changed sections of the character sheet, with no additional text or explanation."}
        ]

        # Get AI's response
        response = client.chat.completions.create(
            model=PLAYER_INFO_UPDATE_MODEL, # Use imported model name
            temperature=TEMPERATURE,
            messages=prompt
        )

        ai_response = response.choices[0].message.content.strip()

        # Write the raw AI response to a debug file
        safe_write_json("debug_player_update.json", {"raw_ai_response": ai_response}, create_backup=False)

        print(f"{ORANGE}DEBUG: Raw AI response written to debug_player_update.json{RESET}")

        # Remove markdown code blocks if present
        ai_response = re.sub(r'```json\n|\n```', '', ai_response)

        try:
            updates = json.loads(ai_response)
            
            # Validate the proposed updates before applying
            is_valid, issues, corrections = validate_player_update(
                original_info, 
                updates, 
                changes,
                attempt + 1
            )
            
            if not is_valid:
                print(f"{ORANGE}DEBUG: Proposed updates have issues: {', '.join(issues)}{RESET}")
                if corrections:
                    print(f"{GREEN}DEBUG: Applying corrections from validator{RESET}")
                    updates = corrections
                else:
                    # If no corrections provided, retry with feedback
                    print(f"{ORANGE}DEBUG: No corrections provided, retrying...{RESET}")
                    continue

            # Apply updates to the player_info
            player_info = update_nested_dict(player_info, updates)
            
            # Normalize status field case if present
            if 'status' in player_info and isinstance(player_info['status'], str):
                player_info['status'] = player_info['status'].lower()
            
            # Normalize condition field - convert 'normal' to 'none'
            if 'condition' in player_info and player_info['condition'] == 'normal':
                player_info['condition'] = 'none'

            # Validate the updated info against the schema
            validate(instance=player_info, schema=schema)

            # If we reach here, validation was successful
            print(f"{GREEN}DEBUG: Successfully updated and validated player info on attempt {attempt + 1}{RESET}")

            # Compare original and updated info
            diff = compare_json(original_info, player_info)
            print(f"{ORANGE}DEBUG: Changes made:{RESET}")
            print(json.dumps(diff, indent=2))

            # Save the updated player info with atomic write
            if not safe_write_json(player_file_path, player_info):
                print(f"{RED}ERROR: Failed to save player file for {player_name}{RESET}")
                return original_info

            # Save the processed conversation history with atomic write
            # Note: This saves the main conversation_history.json.
            # If this function is called by combat_manager.py, it might be overwriting
            # the main history with a version that doesn't yet include combat summary.
            # This is a pre-existing behavior.
            if not safe_write_json("conversation_history.json", processed_history):
                print(f"{RED}WARNING: Failed to save conversation history{RESET}")

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

def validate_player_update(original_info, proposed_updates, change_description, attempt_number=1):
    """
    Validate if proposed updates correctly implement the requested changes.
    Returns (is_valid, issues, corrections)
    """
    # Apply proposed updates to get final state
    test_info = copy.deepcopy(original_info)
    test_info = update_nested_dict(test_info, proposed_updates)
    
    # Create validation prompt
    validation_prompt = [
        {"role": "system", "content": """You are a validation assistant for a D&D 5e game system. 
Your job is to verify if the proposed JSON updates correctly implement the requested changes.

Analyze:
1. What was requested to change
2. What the original state was  
3. What the proposed updates would result in
4. Whether this matches the intent

For arrays (equipment, ammunition, etc.):
- "Add X" or "found X" or "received X" means X should be ADDED to existing items, not replace them
- "Remove/use/expend/consume X" means only X should be removed, other items stay
- "Replace inventory with X" or "inventory is now X" means clear and set to only X
- Empty arrays should only occur if explicitly clearing all items

Common issues to check:
- Equipment array being replaced instead of items being added/removed
- Ammunition counts being replaced instead of updated
- Currency calculations (ensure math is correct)
- Status effects being properly added to arrays

Return JSON with this exact structure:
{
  "is_valid": true/false,
  "issues": ["list of specific problems found"],
  "corrections": {
    // Only if invalid - the corrected updates that should be applied
    // This should be the minimal set of changes needed
  }
}"""},
        {"role": "user", "content": f"""Requested changes: {change_description}

Original player state (relevant fields):
- Equipment ({len(original_info.get('equipment', []))} items): {[item.get('item_name', 'unknown') for item in original_info.get('equipment', [])]}
- Ammunition: {json.dumps(original_info.get('ammunition', []), indent=2)}
- Currency: {json.dumps(original_info.get('currency', {}), indent=2)}
- HP: {original_info.get('hitPoints', 0)}/{original_info.get('maxHitPoints', 0)}
- Status: {original_info.get('status', 'alive')}
- Condition: {original_info.get('condition', 'none')}

Proposed updates:
{json.dumps(proposed_updates, indent=2)}

Final state after updates (relevant fields):
- Equipment ({len(test_info.get('equipment', []))} items): {[item.get('item_name', 'unknown') for item in test_info.get('equipment', [])]}
- Ammunition: {json.dumps(test_info.get('ammunition', []), indent=2)}  
- Currency: {json.dumps(test_info.get('currency', {}), indent=2)}
- HP: {test_info.get('hitPoints', 0)}/{test_info.get('maxHitPoints', 0)}
- Status: {test_info.get('status', 'alive')}
- Condition: {test_info.get('condition', 'none')}

Validate if the proposed updates correctly implement the requested changes."""}
    ]
    
    try:
        # Get validation response
        response = client.chat.completions.create(
            model=PLAYER_INFO_UPDATE_MODEL,
            temperature=VALIDATION_TEMPERATURE,
            messages=validation_prompt
        )
        
        validation_response = response.choices[0].message.content.strip()
        # Remove markdown if present
        validation_response = re.sub(r'```json\n|\n```', '', validation_response)
        
        validation = json.loads(validation_response)
        
        # Debug output
        print(f"{ORANGE}DEBUG: Validation result for attempt {attempt_number}:{RESET}")
        print(f"{ORANGE}Valid: {validation.get('is_valid', False)}{RESET}")
        if validation.get('issues'):
            print(f"{ORANGE}Issues: {', '.join(validation['issues'])}{RESET}")
        
        return validation.get('is_valid', False), validation.get('issues', []), validation.get('corrections', {})
        
    except Exception as e:
        print(f"{RED}ERROR: Validation failed: {str(e)}{RESET}")
        # If validation fails, assume the update is valid to avoid blocking
        return True, [], {}

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