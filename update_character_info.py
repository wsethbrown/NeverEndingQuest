# ============================================================================
# UPDATE_CHARACTER_INFO.PY - CHARACTER DATA MANAGEMENT LAYER
# ============================================================================
# 
# ARCHITECTURE ROLE: Character State Management - AI-Driven Updates with Validation
# 
# This module provides secure, validated character data updates using AI to
# interpret natural language change requests while preventing data corruption
# through intelligent merging and validation strategies.
# 
# KEY RESPONSIBILITIES:
# - AI-driven character data interpretation and updates
# - Deep merge functionality to prevent data loss
# - Critical field validation and corruption prevention  
# - Schema validation and data integrity enforcement
# - Character backup and rollback capabilities
# 
# DATA INTEGRITY DESIGN:
# - DEEP MERGE STRATEGY: Preserves nested object data during partial updates
# - CRITICAL FIELD PROTECTION: Validates essential fields aren't deleted
# - CORRUPTION PREVENTION: Blocks updates that would destroy important data
# - ROLLBACK CAPABILITY: Maintains original data for recovery if needed
# 
# AI INTEGRATION ARCHITECTURE:
# - Natural language change processing via OpenAI models
# - Model-specific optimization (different models for players vs NPCs)
# - Intelligent prompt engineering to prevent partial object replacement
# - Multi-attempt processing with validation between attempts
# 
# VALIDATION LAYERS:
# 1. Schema Validation: Ensures data structure compliance
# 2. Critical Field Validation: Prevents accidental deletion of key data
# 3. AI Character Validation: Post-update character sheet validation
# 4. Character Effects Validation: Equipment and ability effects validation
# 
# DATA CORRUPTION PREVENTION:
# - Problem: AI returning partial objects that replace entire nested structures
# - Solution: Deep merge + critical field validation + enhanced prompting
# - Example: Spell slot updates preserve spellcasting ability, DC, spells list
# - Debugging: Comprehensive logging of problematic updates for analysis
# 
# ARCHITECTURAL INTEGRATION:
# - Core dependency for main.py character update actions
# - Integrates with conversation_utils.py for character data display
# - Uses module_path_manager.py for file location resolution
# - Supports character_validator.py for post-update validation
# 
# DESIGN PATTERNS:
# - Command Pattern: Encapsulated character update operations
# - Template Method: Standardized update workflow with role-specific variations
# - Strategy Pattern: Different AI models for different character types
# - Guard Pattern: Multiple validation layers preventing corruption
# 
# This module ensures character data integrity while providing flexible,
# AI-driven updates that understand natural language change requests.
# ============================================================================

import json
import copy
import shutil
import os
from datetime import datetime
from jsonschema import validate, ValidationError
from openai import OpenAI
import time
import re
# Import model configuration from config.py
from config import OPENAI_API_KEY, PLAYER_INFO_UPDATE_MODEL, NPC_INFO_UPDATE_MODEL
from module_path_manager import ModulePathManager
from file_operations import safe_write_json, safe_read_json
from character_validator import AICharacterValidator
from character_effects_validator import AICharacterEffectsValidator

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

def normalize_character_name(character_name):
    """Convert character name to safe filename format"""
    import re
    
    # Convert to lowercase and replace problematic characters
    name = character_name.strip().lower()
    
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    
    # Replace apostrophes with underscores (handles names like "Mac'Davier")
    name = name.replace("'", "_")
    
    # Replace any other non-alphanumeric characters with underscores
    name = re.sub(r'[^a-z0-9_]', '_', name)
    
    # Remove multiple consecutive underscores
    name = re.sub(r'_+', '_', name)
    
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    return name

def detect_character_role(character_name):
    """Detect character role from existing data or file location"""
    # Get current module from party tracker for consistent path resolution
    try:
        party_tracker_data = safe_json_load("party_tracker.json")
        current_module = party_tracker_data.get("module", "").replace(" ", "_") if party_tracker_data else None
        path_manager = ModulePathManager(current_module)
    except:
        path_manager = ModulePathManager()  # Fallback to reading from file
    
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
    # Get current module from party tracker for consistent path resolution
    try:
        party_tracker_data = safe_json_load("party_tracker.json")
        current_module = party_tracker_data.get("module", "").replace(" ", "_") if party_tracker_data else None
        path_manager = ModulePathManager(current_module)
    except:
        path_manager = ModulePathManager()  # Fallback to reading from file
    
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
    # Add common item type guidance
    schema_info += """
CRITICAL - Valid item_type values (MUST use one of these EXACTLY):
- "weapon" - swords, bows, daggers, melee and ranged weapons
- "armor" - armor pieces, shields, cloaks, boots, gloves, protective wear
- "ammunition" - arrows, bolts, sling bullets, thrown weapon ammo
- "consumable" - potions, scrolls, food, rations, anything consumed when used
- "equipment" - tools, torches, rope, containers, utility items
- "miscellaneous" - rings, amulets, wands, truly miscellaneous items only

NEVER use: "wondrous item", "magic item", "magical" or any other value!

NOTE: Enhanced categorization system fixes GitHub issue #45 (inconsistent item storage)

Enhanced Item Type Mappings:
- Arrows/Bolts/Bullets -> item_type: "ammunition"
- Travel Ration/Food -> item_type: "consumable", item_subtype: "food"
- Torch/Rope/Tools -> item_type: "equipment", item_subtype: "tool"
- Cloak of Elvenkind -> item_type: "armor", item_subtype: "cloak"
- Ring of Protection -> item_type: "miscellaneous", item_subtype: "ring"
- Wand of Magic Missiles -> item_type: "miscellaneous", item_subtype: "wand"
- Potion of Healing -> item_type: "consumable", item_subtype: "potion"
- Scroll of Fireball -> item_type: "consumable", item_subtype: "scroll"
"""
    
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
- Actions array is for 5e standard format (optional)

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

def deep_merge_dict(base_dict, update_dict):
    """Recursively merge update_dict into base_dict, preserving nested structures"""
    result = copy.deepcopy(base_dict)
    
    for key, value in update_dict.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = deep_merge_dict(result[key], value)
        elif key == 'equipment' and isinstance(result.get(key), list) and isinstance(value, list):
            # Special handling for equipment arrays - merge items by name
            result[key] = merge_equipment_arrays(result[key], value)
        else:
            # Replace or add the value
            result[key] = copy.deepcopy(value)
    
    return result

def merge_equipment_arrays(base_equipment, update_equipment):
    """Merge equipment arrays by item name, preserving existing items and removing zero-quantity items"""
    result = copy.deepcopy(base_equipment)
    
    # Create a mapping of item names to indices in the base equipment
    item_name_to_index = {}
    for i, item in enumerate(result):
        item_name = item.get('item_name', '')
        if item_name:
            item_name_to_index[item_name] = i
    
    # Process updates
    for update_item in update_equipment:
        update_item_name = update_item.get('item_name', '')
        if not update_item_name:
            continue
            
        if update_item_name in item_name_to_index:
            # Update existing item by merging dictionaries
            index = item_name_to_index[update_item_name]
            result[index] = deep_merge_dict(result[index], update_item)
        else:
            # Add new item if it doesn't exist
            result.append(copy.deepcopy(update_item))
    
    # Remove items with zero or negative quantity
    result = [item for item in result if item.get('quantity', 1) > 0]
    
    return result

def fix_item_types(updates):
    """Fix common item_type mistakes before validation"""
    # Map of common wrong values to correct values
    item_type_fixes = {
        # Existing fixes
        "wondrous item": "miscellaneous",
        "wondrous": "miscellaneous",
        "magic item": "miscellaneous",
        "magical item": "miscellaneous",
        "magical": "miscellaneous",
        "equipment": "equipment",  # Allow equipment instead of forcing to miscellaneous
        "potion": "consumable",
        "scroll": "consumable",
        # New fixes for common issues
        "arrows": "ammunition",
        "ammunition": "ammunition",
        "ammo": "ammunition",
        "ration": "consumable",
        "food": "consumable",
        "torch": "equipment",
        "tool": "equipment",
        "rope": "equipment",
        "container": "equipment",
        # Keep existing
        "cloak": "armor",
        "ring": "miscellaneous",
        "amulet": "miscellaneous",
        "wand": "miscellaneous",
        "rod": "miscellaneous",
        "staff": "weapon"
    }
    
    # Fix equipment array if present
    if 'equipment' in updates and isinstance(updates['equipment'], list):
        for item in updates['equipment']:
            if 'item_type' in item and isinstance(item['item_type'], str):
                item_type_lower = item['item_type'].lower()
                if item_type_lower in item_type_fixes:
                    old_type = item['item_type']
                    item['item_type'] = item_type_fixes[item_type_lower]
                    print(f"{ORANGE}Auto-corrected item_type: '{old_type}' -> '{item['item_type']}' for {item.get('item_name', 'unknown item')}{RESET}")
    
    return updates

def validate_critical_fields_preserved(original_data, updated_data, character_name):
    """Validate that critical nested fields are not accidentally deleted"""
    critical_paths = [
        ('spellcasting', 'ability'),
        ('spellcasting', 'spellSaveDC'),
        ('spellcasting', 'spellAttackBonus'),
        ('spellcasting', 'spells'),
    ]
    
    # Also check for equipment array preservation
    critical_arrays = ['equipment', 'ammunition']
    
    warnings = []
    
    for path in critical_paths:
        # Check if the field existed in original but is missing in updated
        original_value = original_data
        updated_value = updated_data
        path_exists_in_original = True
        path_exists_in_updated = True
        
        try:
            for key in path:
                original_value = original_value[key]
        except (KeyError, TypeError):
            path_exists_in_original = False
        
        try:
            for key in path:
                updated_value = updated_value[key]
        except (KeyError, TypeError):
            path_exists_in_updated = False
        
        if path_exists_in_original and not path_exists_in_updated:
            field_path = '.'.join(path)
            warnings.append(f"Critical field '{field_path}' was deleted from {character_name}")
    
    # Check for massive array reductions (potential data loss)
    for array_name in critical_arrays:
        if array_name in original_data and array_name in updated_data:
            original_array = original_data[array_name]
            updated_array = updated_data[array_name]
            
            if isinstance(original_array, list) and isinstance(updated_array, list):
                original_count = len(original_array)
                updated_count = len(updated_array)
                
                # Warn if we lost more than 80% of items (likely indicates replacement instead of merge)
                if original_count > 5 and updated_count < (original_count * 0.2):
                    warnings.append(f"Critical array reduction: {array_name} went from {original_count} to {updated_count} items in {character_name}")
    
    return warnings

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

def create_character_backup(character_path, backup_reason="update"):
    """
    Create a timestamped backup of a character file before making changes
    
    Args:
        character_path (str): Path to the character file
        backup_reason (str): Reason for backup (for naming)
    
    Returns:
        str: Path to the backup file, or None if backup failed
    """
    if not os.path.exists(character_path):
        print(f"{RED}Cannot backup: Character file does not exist: {character_path}{RESET}")
        return None
    
    try:
        # Generate timestamp for unique backup naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create backup filename
        base_name = os.path.basename(character_path)
        name_without_ext = os.path.splitext(base_name)[0]
        backup_filename = f"{name_without_ext}.backup_{backup_reason}_{timestamp}.json"
        backup_path = os.path.join(os.path.dirname(character_path), backup_filename)
        
        # Copy the file
        shutil.copy2(character_path, backup_path)
        print(f"DEBUG: Created backup: {backup_filename}")
        
        # Also create a "latest" backup that's easier to find
        latest_backup_path = character_path + ".backup_latest"
        shutil.copy2(character_path, latest_backup_path)
        
        return backup_path
        
    except Exception as e:
        print(f"{RED}Failed to create backup: {str(e)}{RESET}")
        return None

def cleanup_old_backups(character_path, max_backups=5):
    """
    Clean up old backup files, keeping only the most recent ones
    
    Args:
        character_path (str): Path to the character file
        max_backups (int): Maximum number of backup files to keep
    """
    try:
        directory = os.path.dirname(character_path)
        base_name = os.path.basename(character_path)
        name_without_ext = os.path.splitext(base_name)[0]
        
        # Find all backup files for this character
        backup_files = []
        for file in os.listdir(directory):
            if file.startswith(f"{name_without_ext}.backup_") and file.endswith(".json"):
                # Skip the "latest" backup file
                if not file.endswith(".backup_latest"):
                    backup_path = os.path.join(directory, file)
                    # Get file modification time for sorting
                    mtime = os.path.getmtime(backup_path)
                    backup_files.append((mtime, backup_path))
        
        # Sort by modification time (newest first)
        backup_files.sort(reverse=True)
        
        # Remove old backups if we have too many
        if len(backup_files) > max_backups:
            files_to_remove = backup_files[max_backups:]
            for _, file_path in files_to_remove:
                try:
                    os.remove(file_path)
                    print(f"DEBUG: Removed old backup: {os.path.basename(file_path)}")
                except Exception as e:
                    print(f"{ORANGE}Warning: Could not remove old backup {file_path}: {str(e)}{RESET}")
                    
    except Exception as e:
        print(f"{ORANGE}Warning: Backup cleanup failed: {str(e)}{RESET}")

def restore_character_from_backup(character_name, backup_type="latest", character_role=None):
    """
    Restore a character from a backup file
    
    Args:
        character_name (str): Name of the character to restore
        backup_type (str): Type of backup to restore ("latest", or specific timestamp)
        character_role (str, optional): Character role, auto-detected if None
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"{ORANGE}Restoring character: {character_name}{RESET}")
    
    # Auto-detect character role if not provided
    if character_role is None:
        character_role = detect_character_role(character_name)
        print(f"DEBUG: Detected character role: {character_role}")
    
    character_path = get_character_path(character_name, character_role)
    
    if backup_type == "latest":
        backup_path = character_path + ".backup_latest"
    else:
        # Look for specific backup file
        directory = os.path.dirname(character_path)
        base_name = os.path.basename(character_path)
        name_without_ext = os.path.splitext(base_name)[0]
        backup_path = os.path.join(directory, f"{name_without_ext}.backup_{backup_type}.json")
    
    if not os.path.exists(backup_path):
        print(f"{RED}Error: Backup file not found: {backup_path}{RESET}")
        return False
    
    try:
        # Create a backup of current state before restoration
        restoration_backup = create_character_backup(character_path, "pre_restoration")
        
        # Copy backup to main file
        shutil.copy2(backup_path, character_path)
        print(f"{GREEN}Successfully restored {character_name} from backup{RESET}")
        
        if restoration_backup:
            print(f"Previous state backed up as: {os.path.basename(restoration_backup)}")
        
        return True
        
    except Exception as e:
        print(f"{RED}Error restoring from backup: {str(e)}{RESET}")
        return False

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
    
    print(f"DEBUG: Updating character info for: {character_name}")
    
    # Normalize character name to handle titles and descriptors
    normalized_name = normalize_character_name(character_name)
    if normalized_name != character_name:
        print(f"DEBUG: Normalized character name from '{character_name}' to '{normalized_name}'")
        character_name = normalized_name
    
    # Auto-detect character role if not provided
    if character_role is None:
        character_role = detect_character_role(character_name)
        print(f"DEBUG: Detected character role: {character_role}")
    
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
    
    # Create file backup before any changes
    backup_path = create_character_backup(character_path, "update")
    if backup_path is None:
        print(f"{ORANGE}Warning: Could not create backup, but proceeding with update{RESET}")
    else:
        # Clean up old backups to prevent accumulation
        cleanup_old_backups(character_path)
    
    # Create in-memory backup
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
4. IMPORTANT: For equipment arrays, return ONLY the specific items being modified, NOT the entire array
5. Maintain data integrity and consistency
6. IMPORTANT: When updating nested objects like 'spellcasting', include ALL existing subfields to prevent data loss
7. NEVER return partial nested objects that would delete existing important data
8. If updating spell slots, always include ability, spellSaveDC, spellAttackBonus, and spells fields
9. SPELL SLOT RULE: Cantrips (0-level spells) do NOT consume spell slots. Only deduct spell slots for leveled spells (1st-9th level).

EQUIPMENT UPDATE EXAMPLES:
CORRECT (updating one item): {{"equipment": [{{"item_name": "Jeweled dagger", "description": "updated description", "magical": true}}]}}
WRONG (would delete all other items): {{"equipment": [...]}} with multiple items

DANGEROUS EXAMPLE (DO NOT DO):
{{"spellcasting": {{"spellSlots": {{...}}}}}} // This deletes ability, DC, bonus, and spells!

SAFE EXAMPLE:
{{"spellcasting": {{"ability": "wisdom", "spellSaveDC": 13, "spellAttackBonus": 5, "spells": {{...}}, "spellSlots": {{...}}}}}} // This preserves all data

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
            print(f"DEBUG: Attempt {attempt} of {max_attempts}")
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=TEMPERATURE
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
            
            # Fix common item_type mistakes before applying updates
            updates = fix_item_types(updates)
            
            # Apply updates to character data using deep merge
            updated_data = deep_merge_dict(character_data, updates)
            
            # Validate that critical fields weren't accidentally deleted
            critical_warnings = validate_critical_fields_preserved(character_data, updated_data, character_name)
            if critical_warnings:
                for warning in critical_warnings:
                    print(f"{RED}CRITICAL WARNING: {warning}{RESET}")
                print(f"{RED}Aborting update to prevent data loss. AI response may be incomplete.{RESET}")
                
                # Log the problematic update for debugging
                debug_info = {
                    "character_name": character_name,
                    "attempt": attempt,
                    "warnings": critical_warnings,
                    "original_spellcasting": character_data.get('spellcasting', {}),
                    "update_data": updates,
                    "ai_response": raw_response
                }
                safe_write_json("debug_critical_field_loss.json", debug_info)
                print(f"{ORANGE}Debug info saved to debug_critical_field_loss.json{RESET}")
                
                if attempt == max_attempts:
                    print(f"{RED}Max attempts reached. Update failed to preserve critical data.{RESET}")
                    return False
                attempt += 1
                continue
            
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
                print(f"DEBUG: Successfully updated {character_name} ({character_role})!")
                
                # Log the changes
                changed_fields = list(updates.keys())
                print(f"DEBUG: Updated fields: {', '.join(changed_fields)}")
                
                # AI Character Validation after successful update
                try:
                    validator = AICharacterValidator()
                    validated_data, validation_success = validator.validate_character_file_safe(character_path)
                    
                    if validation_success and validator.corrections_made:
                        print(f"DEBUG: Character auto-validated with corrections...")
                    elif validation_success:
                        print(f"DEBUG: Character validated - no corrections needed")
                    else:
                        print(f"DEBUG: Warning: Character validation failed, but update completed")
                        
                except Exception as e:
                    print(f"{ORANGE}Warning: Character validation error: {str(e)}{RESET}")
                    # Don't fail the update if validation has issues
                
                # AI Character Effects Validation after AC validation
                try:
                    effects_validator = AICharacterEffectsValidator()
                    effects_validated_data, effects_success = effects_validator.validate_character_effects_safe(character_path)
                    
                    if effects_success and effects_validator.corrections_made:
                        print(f"DEBUG: Character effects auto-validated with corrections...")
                    elif effects_success:
                        print(f"DEBUG: Character effects validated - no corrections needed")
                    else:
                        print(f"DEBUG: Warning: Character effects validation failed, but update completed")
                        
                except Exception as e:
                    print(f"{ORANGE}Warning: Character effects validation error: {str(e)}{RESET}")
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

# Utility functions for backup management
def list_character_backups(character_name, character_role=None):
    """
    List all available backups for a character
    
    Args:
        character_name (str): Name of the character
        character_role (str, optional): Character role, auto-detected if None
    
    Returns:
        list: List of backup file information
    """
    if character_role is None:
        character_role = detect_character_role(character_name)
    
    character_path = get_character_path(character_name, character_role)
    directory = os.path.dirname(character_path)
    base_name = os.path.basename(character_path)
    name_without_ext = os.path.splitext(base_name)[0]
    
    backups = []
    try:
        for file in os.listdir(directory):
            if file.startswith(f"{name_without_ext}.backup_") and file.endswith(".json"):
                backup_path = os.path.join(directory, file)
                mtime = os.path.getmtime(backup_path)
                backups.append({
                    'filename': file,
                    'path': backup_path,
                    'modified': datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    'size': os.path.getsize(backup_path)
                })
        
        # Sort by modification time (newest first)
        backups.sort(key=lambda x: x['modified'], reverse=True)
        
    except Exception as e:
        print(f"{RED}Error listing backups: {str(e)}{RESET}")
    
    return backups

if __name__ == "__main__":
    # Test the unified system
    print("Testing unified character update system...")
    
    # Test with a player character
    result = update_character_info("norn", "Add 100 experience points", character_role='player')
    print(f"Player update result: {result}")
    
    # Test with an NPC
    result = update_character_info("test_guard", "Increase level to 3", character_role='npc')
    print(f"NPC update result: {result}")