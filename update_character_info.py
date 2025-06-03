import json
import copy
from jsonschema import validate, ValidationError
from openai import OpenAI
import time
import re
# Import model configuration from config.py
from config import OPENAI_API_KEY, PLAYER_INFO_UPDATE_MODEL, NPC_INFO_UPDATE_MODEL
from campaign_path_manager import CampaignPathManager
from file_operations import safe_write_json, safe_read_json
from character_validator import AICharacterValidator

client = OpenAI(api_key=OPENAI_API_KEY)

# Constants
TEMPERATURE = 0.7
VALIDATION_TEMPERATURE = 0.1  # Lower temperature for validation

# ANSI escape codes
ORANGE = "\033[38;2;255;165;0m"
RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"

def load_schema():
    """Load the unified character schema"""
    with open("char_schema.json", "r") as schema_file:
        return json.load(schema_file)

def load_conversation_history():
    data = safe_read_json("conversation_history.json")
    return data if data else []

def detect_character_role(character_name):
    """Detect character role from existing data or file location"""
    path_manager = CampaignPathManager()
    
    # First try player path
    player_path = path_manager.get_character_path(character_name)
    try:
        with open(player_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('character_role', 'player')
    except FileNotFoundError:
        pass
    
    # Then try NPC path
    npc_path = path_manager.get_character_path(character_name)
    try:
        with open(npc_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('character_role', 'npc')
    except FileNotFoundError:
        pass
    
    # Default to NPC if not found (most characters created are NPCs)
    return 'npc'

def get_character_path(character_name, character_role=None):
    """Get the appropriate file path for a character"""
    path_manager = CampaignPathManager()
    
    # Use the updated path manager that handles unified/legacy fallback
    return path_manager.get_character_path(character_name)

def process_conversation_history(history, character_role):
    """Process conversation history based on character role"""
    if character_role == 'player':
        # Player-specific processing
        for message in history:
            if message["role"] == "user" and message["content"].startswith("Leveling Dungeon Master Guidance"):
                message["content"] = "DM Guidance: Proceed with leveling up the player character given the 5th Edition role playing game rules. Only level the player one level at a time to ensure no mistakes are made. You must ask the player for important decisions and choices they would have control over. After the player has provided the needed information then use the 'updatePlayerInfo' to pass all changes to the players character sheet and include the experience goal for the next level. Do not update the player's information in segments."
    # NPC processing can be added here if needed
    return history

def format_schema_for_prompt(schema, character_role):
    """Format schema information for inclusion in the prompt"""
    if character_role == 'player':
        schema_info = "Character Schema - Valid fields and values:\n\n"
    else:
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
                array_fields.append(f"- {field}: Array of objects")
            else:
                array_fields.append(f"- {field}: Array of {items_type}")
        elif field_type == 'object':
            object_fields.append(f"- {field}: Object with specific structure")
        else:
            simple_fields.append(f"- {field}: {field_type}")
    
    # Add field categories to schema info
    if enum_fields:
        schema_info += "Enum Fields (must match exactly):\n" + "\n".join(enum_fields) + "\n\n"
    
    if simple_fields:
        schema_info += "Simple Fields:\n" + "\n".join(simple_fields) + "\n\n"
    
    if array_fields:
        schema_info += "Array Fields:\n" + "\n".join(array_fields) + "\n\n"
    
    if object_fields:
        schema_info += "Object Fields:\n" + "\n".join(object_fields) + "\n\n"
    
    # Add role-specific examples
    if character_role == 'player':
        schema_info += """
Equipment Array Example:
[{"item_name": "Sword", "item_type": "weapon", "description": "Sharp blade", "quantity": 1}]

Currency Example: 
{"gold": 50, "silver": 10, "copper": 25}

Ammunition Example:
[{"name": "Arrows", "quantity": 20, "description": "Standard arrows"}]
"""
    else:
        schema_info += """
Equipment Array Example:
[{"item_name": "Chain Mail", "item_type": "armor", "description": "Heavy armor", "quantity": 1}]

AttacksAndSpellcasting vs Actions:
- Use attacksAndSpellcasting for standard attack format
- Actions array is for D&D standard format (optional)

Combat Damage Note:
When NPCs deal damage in combat, do NOT update their action arrays. Only update when the NPC gains new abilities or equipment.
"""
    
    return schema_info

def get_model_for_character(character_role):
    """Get the appropriate model based on character role"""
    if character_role == 'player':
        return PLAYER_INFO_UPDATE_MODEL
    else:
        return NPC_INFO_UPDATE_MODEL

def normalize_status_and_condition(data, character_role):
    """Normalize status and condition fields based on character role"""
    if character_role == 'player':
        # Player-specific normalization
        if 'status' in data:
            data['status'] = data['status'].lower()
        if 'condition' in data and data['condition'] == 'normal':
            data['condition'] = 'none'
    # NPC normalization can be different if needed
    return data

def validate_character_data(data, schema, character_name):
    """Validate character data against schema"""
    try:
        validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        error_msg = f"Validation error for {character_name}: {e.message}"
        if e.path:
            error_msg += f" at path: {'.'.join(map(str, e.path))}"
        return False, error_msg

def update_character_info(character_name, changes, character_role=None):
    """
    Unified function to update character information for both players and NPCs
    
    Args:
        character_name (str): Name of the character to update
        changes (str): Description of changes to make
        character_role (str, optional): 'player' or 'npc', auto-detected if None
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    print(f"{ORANGE}Updating character info for: {character_name}{RESET}")
    
    # Auto-detect character role if not provided
    if character_role is None:
        character_role = detect_character_role(character_name)
        print(f"Detected character role: {character_role}")
    
    # Load schema and character data
    schema = load_schema()
    character_path = get_character_path(character_name, character_role)
    
    try:
        character_data = safe_read_json(character_path)
        if not character_data:
            print(f"{RED}Error: Could not load character data for {character_name}{RESET}")
            return False
        
        # Validate that character_data is a dictionary
        if not isinstance(character_data, dict):
            print(f"{RED}Error: Character data for {character_name} is corrupted (not a dictionary){RESET}")
            print(f"{RED}Loaded data type: {type(character_data)}, value: {character_data}{RESET}")
            return False
            
    except Exception as e:
        print(f"{RED}Error loading character data: {str(e)}{RESET}")
        return False
    
    # Create backup
    original_data = copy.deepcopy(character_data)
    
    # Load and process conversation history
    history = load_conversation_history()
    if character_role == 'player':
        history = process_conversation_history(history, character_role)
    
    # Format schema for prompt
    schema_info = format_schema_for_prompt(schema, character_role)
    
    # Build the prompt
    system_message = f"""You are an assistant that updates character information in a 5th Edition roleplaying game. Given the current character information and a description of changes, you must return only the updated sections as a JSON object. Do not include unchanged fields. Your response should be a valid JSON object representing only the modified parts of the character sheet.

{schema_info}

CRITICAL INSTRUCTIONS:
1. Return ONLY a JSON object with the fields that need to be updated
2. Do not include unchanged fields
3. Ensure all values match the schema requirements exactly
4. For arrays, include the complete updated array if any element changes
5. Maintain data integrity and consistency

Character Role: {character_role}
"""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"Current character data:\n{json.dumps(character_data, indent=2)}"},
        {"role": "user", "content": f"Changes to make: {changes}"}
    ]
    
    # Add conversation history for context (last 10 messages)
    if history:
        recent_history = history[-10:]
        for msg in recent_history:
            if msg.get('role') in ['user', 'assistant']:
                messages.insert(-2, {"role": msg['role'], "content": msg['content'][:1000]})
    
    max_attempts = 3
    attempt = 1
    
    # Get appropriate model for character type
    model = get_model_for_character(character_role)
    
    while attempt <= max_attempts:
        try:
            print(f"Attempt {attempt} of {max_attempts}")
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=2000
            )
            
            raw_response = response.choices[0].message.content.strip()
            
            # Enhanced debug logging for NPCs
            if character_role == 'npc':
                debug_info = {
                    "attempt": attempt,
                    "npc_name": character_name,
                    "changes": changes,
                    "raw_ai_response": raw_response
                }
                safe_write_json("debug_npc_update.json", debug_info)
            
            # Clean and parse JSON response
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in response")
            
            clean_response = json_match.group()
            updates = json.loads(clean_response)
            
            # Apply updates to character data
            updated_data = copy.deepcopy(character_data)
            for key, value in updates.items():
                if key in updated_data:
                    updated_data[key] = value
                else:
                    print(f"{ORANGE}Warning: Adding new field '{key}' to character{RESET}")
                    updated_data[key] = value
            
            # Role-specific normalization
            updated_data = normalize_status_and_condition(updated_data, character_role)
            
            # Validate updated data
            is_valid, error_msg = validate_character_data(updated_data, schema, character_name)
            
            if not is_valid:
                print(f"{RED}Validation failed: {error_msg}{RESET}")
                if attempt == max_attempts:
                    print(f"{RED}Max attempts reached. Reverting changes.{RESET}")
                    return False
                attempt += 1
                continue
            
            # Save updated character data
            if safe_write_json(character_path, updated_data):
                print(f"{GREEN}Successfully updated {character_name} ({character_role})!{RESET}")
                
                # Log the changes
                changed_fields = list(updates.keys())
                print(f"Updated fields: {', '.join(changed_fields)}")
                
                # NEW: AI Character Validation after successful update
                try:
                    validator = AICharacterValidator()
                    validated_data, validation_success = validator.validate_character_file_safe(character_path)
                    
                    if validation_success and validator.corrections_made:
                        print(f"{GREEN}Character auto-validated with corrections: {validator.corrections_made}{RESET}")
                    elif validation_success:
                        print(f"{GREEN}Character validated - no corrections needed{RESET}")
                    else:
                        print(f"{ORANGE}Warning: Character validation failed, but update completed{RESET}")
                        
                except Exception as e:
                    print(f"{ORANGE}Warning: Character validation error: {str(e)}{RESET}")
                    # Don't fail the update if validation has issues
                
                return True
            else:
                print(f"{RED}Error: Failed to save character data{RESET}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"{RED}JSON decode error (attempt {attempt}): {str(e)}{RESET}")
            print(f"Raw response: {raw_response}")
            
        except Exception as e:
            print(f"{RED}Error during update (attempt {attempt}): {str(e)}{RESET}")
        
        if attempt < max_attempts:
            attempt += 1
            time.sleep(1)
        else:
            break
    
    print(f"{RED}Failed to update character after {max_attempts} attempts{RESET}")
    return False

# Backward compatibility functions
def updatePlayerInfo(player_name, changes):
    """Backward compatibility wrapper for player updates"""
    return update_character_info(player_name, changes, character_role='player')

def updateNPCInfo(npc_name, changes):
    """Backward compatibility wrapper for NPC updates"""
    return update_character_info(npc_name, changes, character_role='npc')

if __name__ == "__main__":
    # Test the unified system
    print("Testing unified character update system...")
    
    # Test with a player character
    result = update_character_info("norn", "Add 100 experience points", character_role='player')
    print(f"Player update result: {result}")
    
    # Test with an NPC
    result = update_character_info("test_guard", "Increase level to 3", character_role='npc')
    print(f"NPC update result: {result}")