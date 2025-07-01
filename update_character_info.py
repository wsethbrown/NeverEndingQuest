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
import concurrent.futures
import threading
from typing import List, Tuple, Dict, Optional
# Import model configuration from config.py
from config import OPENAI_API_KEY, PLAYER_INFO_UPDATE_MODEL, NPC_INFO_UPDATE_MODEL
from module_path_manager import ModulePathManager
from file_operations import safe_write_json, safe_read_json
from encoding_utils import safe_json_load
from character_validator import AICharacterValidator
from character_effects_validator import AICharacterEffectsValidator
from enhanced_logger import debug, info, warning, error, set_script_name

# Set script name for logging
set_script_name(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

# Constants
TEMPERATURE = 0.7
VALIDATION_TEMPERATURE = 0.1  # Lower temperature for validation
MAX_PARALLEL_WORKERS = 8  # Max parallel character updates
BATCH_SIZE = 8  # Process in batches if more than 8 characters

# ANSI escape codes - REMOVED per CLAUDE.md guidelines
# All color codes have been removed to prevent Windows console encoding errors

# Global lock manager to prevent file conflicts
_file_locks = {}
_lock_manager = threading.Lock()

def get_file_lock(file_path: str) -> threading.Lock:
    """Get or create a lock for a specific file path"""
    with _lock_manager:
        if file_path not in _file_locks:
            _file_locks[file_path] = threading.Lock()
        return _file_locks[file_path]

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
                    debug(f"VALIDATION: Auto-corrected item_type: '{old_type}' -> '{item['item_type']}' for {item.get('item_name', 'unknown item')}", category="character_validation")
    
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

def purge_invalid_fields(data, schema, character_name=""):
    """
    Remove fields from character data that are not in the schema.
    This prevents validation failures from AI-added invalid fields.
    
    Args:
        data (dict): Character data to clean
        schema (dict): Schema to validate against
        character_name (str): Character name for logging
    
    Returns:
        tuple: (cleaned_data, removed_fields_list)
    """
    if not isinstance(data, dict) or not isinstance(schema, dict):
        return data, []
    
    schema_properties = schema.get('properties', {})
    removed_fields = []
    cleaned_data = {}
    
    for field, value in data.items():
        if field in schema_properties:
            # Field exists in schema - keep it (but recursively clean if it's an object)
            field_schema = schema_properties[field]
            if isinstance(value, dict) and field_schema.get('type') == 'object':
                # Recursively clean nested objects
                if 'properties' in field_schema:
                    cleaned_value, nested_removed = purge_invalid_fields(value, field_schema, f"{character_name}.{field}")
                    cleaned_data[field] = cleaned_value
                    if nested_removed:
                        removed_fields.extend([f"{field}.{nf}" for nf in nested_removed])
                else:
                    cleaned_data[field] = value
            else:
                cleaned_data[field] = value
        else:
            # Field not in schema - remove it
            removed_fields.append(field)
            warning(f"VALIDATION: PURGED invalid field '{field}' from {character_name}", category="character_validation")
    
    return cleaned_data, removed_fields

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
        error(f"FAILURE: Cannot backup: Character file does not exist: {character_path}", category="file_operations")
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
        debug(f"FILE_OP: Created backup: {backup_filename}", category="file_operations")
        
        # Also create a "latest" backup that's easier to find
        latest_backup_path = character_path + ".backup_latest"
        shutil.copy2(character_path, latest_backup_path)
        
        return backup_path
        
    except Exception as e:
        error(f"FAILURE: Failed to create backup", exception=e, category="file_operations")
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
                    debug(f"FILE_OP: Removed old backup: {os.path.basename(file_path)}", category="file_operations")
                except Exception as e:
                    warning(f"FILE_OP: Could not remove old backup {file_path}", exception=e, category="file_operations")
                    
    except Exception as e:
        warning(f"FILE_OP: Backup cleanup failed", exception=e, category="file_operations")

def _process_single_character(character_update: Dict[str, any]) -> Tuple[str, bool, str]:
    """
    Process a single character update in a thread-safe manner
    
    Args:
        character_update: Dict with keys:
            - character_name: str
            - changes: str
            - character_role: Optional[str]
    
    Returns:
        Tuple of (character_name, success, message)
    """
    character_name = character_update['character_name']
    changes = character_update['changes']
    character_role = character_update.get('character_role')
    
    try:
        # Get file lock for this character
        character_path = get_character_path(character_name, character_role)
        file_lock = get_file_lock(character_path)
        
        # Acquire lock and process
        with file_lock:
            # Call the original update logic
            success = _update_character_info_internal(character_name, changes, character_role)
            
            if success:
                message = f"Successfully updated {character_name}"
                info(f"PARALLEL: {message}", category="character_updates")
            else:
                message = f"Failed to update {character_name}"
                error(f"PARALLEL: {message}", category="character_updates")
                
            return (character_name, success, message)
            
    except Exception as e:
        message = f"Error updating {character_name}: {str(e)}"
        error(f"PARALLEL: {message}", exception=e, category="character_updates")
        return (character_name, False, message)

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
    info(f"STATE_CHANGE: Restoring character: {character_name}", category="character_updates")
    
    # Auto-detect character role if not provided
    if character_role is None:
        character_role = detect_character_role(character_name)
        debug(f"STATE_CHANGE: Detected character role: {character_role}", category="character_updates")
    
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
        error(f"FAILURE: Backup file not found: {backup_path}", category="file_operations")
        return False
    
    try:
        # Create a backup of current state before restoration
        restoration_backup = create_character_backup(character_path, "pre_restoration")
        
        # Copy backup to main file
        shutil.copy2(backup_path, character_path)
        info(f"SUCCESS: Successfully restored {character_name} from backup", category="character_updates")
        
        if restoration_backup:
            info(f"FILE_OP: Previous state backed up as: {os.path.basename(restoration_backup)}", category="file_operations")
        
        return True
        
    except Exception as e:
        error(f"FAILURE: Error restoring from backup", exception=e, category="character_updates")
        return False

def _update_character_info_internal(character_name, changes, character_role=None):
    """
    Unified function to update character information for both players and NPCs
    
    Args:
        character_name (str): Name of the character to update
        changes (str): Description of changes to make
        character_role (str, optional): 'player' or 'npc', auto-detected if None
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    debug(f"STATE_CHANGE: Updating character info for: {character_name}", category="character_updates")
    
    # Normalize character name to handle titles and descriptors
    normalized_name = normalize_character_name(character_name)
    if normalized_name != character_name:
        debug(f"STATE_CHANGE: Normalized character name from '{character_name}' to '{normalized_name}'", category="character_updates")
        character_name = normalized_name
    
    # Auto-detect character role if not provided
    if character_role is None:
        character_role = detect_character_role(character_name)
        debug(f"STATE_CHANGE: Detected character role: {character_role}", category="character_updates")
    
    # Load schema and character data
    schema = load_schema()
    character_path = get_character_path(character_name, character_role)
    
    try:
        character_data = safe_read_json(character_path)
        if not character_data:
            error(f"FAILURE: Could not load character data for {character_name}", category="file_operations")
            return False
        
        # Validate that character_data is a dictionary
        if not isinstance(character_data, dict):
            error(f"FAILURE: Character data for {character_name} is corrupted (not a dictionary)", category="file_operations")
            error(f"FAILURE: Loaded data type: {type(character_data)}, value: {character_data}", category="file_operations")
            return False
            
    except Exception as e:
        error(f"FAILURE: Error loading character data", exception=e, category="file_operations")
        return False
    
    # Create file backup before any changes
    backup_path = create_character_backup(character_path, "update")
    if backup_path is None:
        warning("FILE_OP: Could not create backup, but proceeding with update", category="file_operations")
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
10. HIT DICE RULE: IGNORE all references to hit dice, Hit Dice, HD, or hit dice restoration. Do NOT add hitDice, hitDiceRestored, or maxHitDice fields. The system does not track hit dice.
11. REST HEALING: For long rests, simply restore hitPoints to maxHitPoints and restore spell slots. For short rests, restore some hitPoints based on the description. Do not implement hit dice mechanics.
12. CURRENCY MANAGEMENT: Your primary function is to calculate additions and subtractions. NEVER replace the entire currency object. An instruction like "kept 13 gold" after a transaction means you must calculate the *change* (e.g., a subtraction) to reach that state. Do not simply return '{{"currency": {{"gold": 13}}}}' as this will delete the character's silver and copper. Always return the *change* to be applied.
13. STATUS-CONDITION SYNCHRONIZATION: Always maintain consistency between status, condition, and hitPoints fields:
    - When status changes to "alive" and hitPoints > 0, automatically set condition to "none" and clear condition_affected array
    - When hitPoints > 0 and status is "alive", condition cannot be "unconscious"
    - When status is "unconscious", condition must be "unconscious" and condition_affected must include "unconscious"
    - When healing an unconscious character above 0 HP, clear unconscious from both condition and condition_affected fields

EQUIPMENT UPDATE EXAMPLES:
CORRECT (updating one item): {{"equipment": [{{"item_name": "Jeweled dagger", "description": "updated description", "magical": true}}]}}
WRONG (would delete all other items): {{"equipment": [...]}} with multiple items

DANGEROUS EXAMPLE (DO NOT DO):
{{"spellcasting": {{"spellSlots": {{...}}}}}} // This deletes ability, DC, bonus, and spells!

SAFE EXAMPLE:
{{"spellcasting": {{"ability": "wisdom", "spellSaveDC": 13, "spellAttackBonus": 5, "spells": {{...}}, "spellSlots": {{...}}}}}} // This preserves all data

CONDITION MANAGEMENT EXAMPLES:
CORRECT (healing unconscious character): {{"hitPoints": 12, "status": "alive", "condition": "none", "condition_affected": []}}
WRONG (inconsistent state): {{"hitPoints": 12, "status": "alive", "condition": "unconscious"}} // Condition contradicts status!

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
            debug(f"STATE_CHANGE: Attempt {attempt} of {max_attempts}", category="character_updates")
            
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
                    error(f"CRITICAL WARNING: {warning}", category="character_validation")
                error("FAILURE: Aborting update to prevent data loss. AI response may be incomplete.", category="character_validation")
                
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
                debug("FILE_OP: Debug info saved to debug_critical_field_loss.json", category="file_operations")
                
                if attempt == max_attempts:
                    error("FAILURE: Max attempts reached. Update failed to preserve critical data.", category="character_validation")
                    return False
                attempt += 1
                continue
            
            # Role-specific normalization
            updated_data = normalize_status_and_condition(updated_data, character_role)
            
            # Purge invalid fields before validation
            updated_data, removed_fields = purge_invalid_fields(updated_data, schema, character_name)
            if removed_fields:
                warning(f"VALIDATION: Purged {len(removed_fields)} invalid fields: {', '.join(removed_fields)}", category="character_validation")
            
            # Validate updated data
            is_valid, error_msg = validate_character_data(updated_data, schema, character_name)
            
            if not is_valid:
                error(f"VALIDATION: Validation failed: {error_msg}", category="character_validation")
                if attempt == max_attempts:
                    error("FAILURE: Max attempts reached. Reverting changes.", category="character_updates")
                    return False
                
                # Add validation error feedback to the prompt for next attempt
                if "item_subtype" in error_msg and "is not one of" in error_msg:
                    # Extract the problematic subtype
                    subtype_start = error_msg.find("'") + 1
                    subtype_end = error_msg.find("'", subtype_start)
                    invalid_subtype = error_msg[subtype_start:subtype_end] if subtype_start > 0 and subtype_end > subtype_start else "unknown"
                    
                    feedback_message = f"\n\nPREVIOUS ATTEMPT FAILED: The item_subtype '{invalid_subtype}' is not valid. Valid item_subtype values are: ['scroll', 'potion', 'wand', 'ring', 'amulet', 'cloak', 'boots', 'gloves', 'helmet', 'rod', 'staff', 'food', 'other']. For food items like trail rations, use 'food' as the item_subtype."
                    messages[-1]["content"] += feedback_message
                else:
                    # Generic validation error feedback
                    feedback_message = f"\n\nPREVIOUS ATTEMPT FAILED: {error_msg}. Please fix the validation error in your next response."
                    messages[-1]["content"] += feedback_message
                
                attempt += 1
                continue
            
            # Save updated character data
            if safe_write_json(character_path, updated_data):
                info(f"SUCCESS: Successfully updated {character_name} ({character_role})!", category="character_updates")
                
                # Log the changes
                changed_fields = list(updates.keys())
                debug(f"STATE_CHANGE: Updated fields: {', '.join(changed_fields)}", category="character_updates")
                
                # AI Character Validation after successful update
                try:
                    validator = AICharacterValidator()
                    validated_data, validation_success = validator.validate_character_file_safe(character_path)
                    
                    if validation_success and validator.corrections_made:
                        debug("VALIDATION: Character auto-validated with corrections...", category="character_validation")
                    elif validation_success:
                        debug("VALIDATION: Character validated - no corrections needed", category="character_validation")
                    else:
                        warning("VALIDATION: Character validation failed, but update completed", category="character_validation")
                        
                except Exception as e:
                    warning(f"VALIDATION: Character validation error", exception=e, category="character_validation")
                    # Don't fail the update if validation has issues
                
                # AI Character Effects Validation after AC validation
                try:
                    effects_validator = AICharacterEffectsValidator()
                    effects_validated_data, effects_success = effects_validator.validate_character_effects_safe(character_path)
                    
                    if effects_success and effects_validator.corrections_made:
                        debug("VALIDATION: Character effects auto-validated with corrections...", category="character_validation")
                    elif effects_success:
                        debug("VALIDATION: Character effects validated - no corrections needed", category="character_validation")
                    else:
                        warning("VALIDATION: Character effects validation failed, but update completed", category="character_validation")
                        
                except Exception as e:
                    warning(f"VALIDATION: Character effects validation error", exception=e, category="character_validation")
                    # Don't fail the update if validation has issues
                
                return True
            else:
                error("FAILURE: Failed to save character data", category="file_operations")
                return False
                
        except json.JSONDecodeError as e:
            error(f"FAILURE: JSON decode error (attempt {attempt})", exception=e, category="ai_processing")
            debug(f"AI_CALL: Raw response: {raw_response}", category="ai_processing")
            
        except Exception as e:
            error(f"FAILURE: Error during update (attempt {attempt})", exception=e, category="character_updates")
        
        if attempt < max_attempts:
            attempt += 1
            time.sleep(1)
        else:
            break
    
    error(f"FAILURE: Failed to update character after {max_attempts} attempts", category="character_updates")
    return False

def update_multiple_characters(character_updates: List[Dict[str, any]]) -> Dict[str, any]:
    """
    Update multiple characters in parallel with batching support
    
    Args:
        character_updates: List of dicts, each containing:
            - character_name: str
            - changes: str  
            - character_role: Optional[str]
    
    Returns:
        Dict with results:
            - total: int (total characters to update)
            - successful: List[str] (character names)
            - failed: List[Dict[str, str]] (character_name and error message)
            - messages: List[str] (all messages)
    """
    total_updates = len(character_updates)
    info(f"PARALLEL: Starting parallel update for {total_updates} characters", category="character_updates")
    
    results = {
        'total': total_updates,
        'successful': [],
        'failed': [],
        'messages': []
    }
    
    # Process in batches if more than BATCH_SIZE
    for batch_start in range(0, total_updates, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_updates)
        batch = character_updates[batch_start:batch_end]
        batch_size = len(batch)
        
        if total_updates > BATCH_SIZE:
            info(f"PARALLEL: Processing batch {batch_start//BATCH_SIZE + 1} ({batch_size} characters)", category="character_updates")
        
        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(batch_size, MAX_PARALLEL_WORKERS)) as executor:
            # Submit all tasks
            future_to_character = {
                executor.submit(_process_single_character, update): update['character_name']
                for update in batch
            }
            
            # Process completed tasks as they finish
            for future in concurrent.futures.as_completed(future_to_character):
                character_name = future_to_character[future]
                
                try:
                    name, success, message = future.result()
                    results['messages'].append(message)
                    
                    if success:
                        results['successful'].append(name)
                    else:
                        results['failed'].append({
                            'character_name': name,
                            'error': message
                        })
                        
                except Exception as e:
                    error_msg = f"Exception processing {character_name}: {str(e)}"
                    error(f"PARALLEL: {error_msg}", exception=e, category="character_updates")
                    results['failed'].append({
                        'character_name': character_name,
                        'error': error_msg
                    })
                    results['messages'].append(error_msg)
    
    # Summary
    success_count = len(results['successful'])
    fail_count = len(results['failed'])
    info(f"PARALLEL: Completed {total_updates} updates - {success_count} successful, {fail_count} failed", category="character_updates")
    
    return results

def update_character_info(character_name, changes, character_role=None):
    """
    Backward compatible wrapper that uses parallel processing internally
    
    Args:
        character_name (str): Name of the character to update
        changes (str): Description of changes to make
        character_role (str, optional): 'player' or 'npc', auto-detected if None
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Use parallel system with single character
    character_update = {
        'character_name': character_name,
        'changes': changes,
        'character_role': character_role
    }
    
    results = update_multiple_characters([character_update])
    
    # Return simple boolean for backward compatibility
    return character_name in results['successful']

# Backward compatibility functions
def updatePlayerInfo(player_name, changes):
    """Backward compatibility wrapper for player updates"""
    return update_character_info(player_name, changes, character_role='player')

def updateNPCInfo(npc_name, changes):
    """Backward compatibility wrapper for NPC updates"""
    return update_character_info(npc_name, changes, character_role='npc')

def update_party_members(changes: str, include_player: bool = True, include_npcs: bool = True) -> Dict[str, any]:
    """
    Update all active party members with the same changes
    
    Args:
        changes: Description of changes to apply to all party members
        include_player: Whether to include player characters
        include_npcs: Whether to include NPC party members
    
    Returns:
        Dict with results from update_multiple_characters
    """
    # Load party tracker to get active party members
    party_data = safe_read_json("party_tracker.json")
    if not party_data:
        error("PARALLEL: Could not load party tracker", category="character_updates")
        return {
            'total': 0,
            'successful': [],
            'failed': [],
            'messages': ['Could not load party tracker']
        }
    
    character_updates = []
    
    # Add player character if requested
    if include_player and 'player' in party_data:
        player_name = party_data['player'].get('name')
        if player_name:
            character_updates.append({
                'character_name': player_name,
                'changes': changes,
                'character_role': 'player'
            })
    
    # Add NPC party members if requested
    if include_npcs and 'npc_party' in party_data:
        for npc in party_data['npc_party']:
            npc_name = npc.get('name')
            if npc_name:
                character_updates.append({
                    'character_name': npc_name,
                    'changes': changes,
                    'character_role': 'npc'
                })
    
    if not character_updates:
        warning("PARALLEL: No party members found to update", category="character_updates")
        return {
            'total': 0,
            'successful': [],
            'failed': [],
            'messages': ['No party members found to update']
        }
    
    info(f"PARALLEL: Updating {len(character_updates)} party members", category="character_updates")
    return update_multiple_characters(character_updates)

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
        error(f"FAILURE: Error listing backups", exception=e, category="file_operations")
    
    return backups

if __name__ == "__main__":
    # Test the unified system
    debug("INITIALIZATION: Testing unified character update system...", category="testing")
    
    # Test with a player character
    result = update_character_info("norn", "Add 100 experience points", character_role='player')
    debug(f"TEST: Player update result: {result}", category="testing")
    
    # Test with an NPC
    result = update_character_info("test_guard", "Increase level to 3", character_role='npc')
    debug(f"TEST: NPC update result: {result}", category="testing")