# ============================================================================
# COMBAT_MANAGER.PY - TURN-BASED COMBAT SYSTEM
# ============================================================================
#
# ARCHITECTURE ROLE: Game Systems Layer - Combat Management
#
# This module provides comprehensive turn-based combat management for the 5th edition
# Dungeon Master system, implementing AI-driven combat encounters with full rule
# compliance and intelligent resource tracking.
#
# KEY RESPONSIBILITIES:
# - Turn-based combat orchestration with initiative order management
# - AI-powered combat decision making for NPCs and monsters
# - Combat state validation and rule compliance verification
# - Experience point calculation and reward distribution
# - Combat logging and debugging support with per-encounter directories
# - Real-time combat status display and resource tracking
# - Preroll dice caching system to prevent AI manipulation
#

"""
Combat Manager Module for DungeonMasterAI

Handles combat encounters between players, NPCs, and monsters.

Features:
- Manages turn-based combat with initiative order
- Processes player actions and AI responses
- Generates combat summaries and experience rewards
- Maintains combat logs for debugging and analysis
- Round-based preroll caching to ensure dice consistency
- Real-time combat state display with dynamic resource tracking

Combat Logging System:
- Creates per-encounter logs in the combat_logs/{encounter_id}/ directory
- Generates both timestamped and "latest" versions of each log
- Maintains a combined log of all encounters in all_combat_latest.json
- Filters out system messages for cleaner, more readable logs

"""
# ============================================================================
# COMBAT_MANAGER.PY - GAME SYSTEMS LAYER - COMBAT
# ============================================================================
# 
# ARCHITECTURE ROLE: Game Systems Layer - Turn-Based Combat Management
# 
# This module implements 5e combat mechanics using AI-driven simulation
# with strict rule validation. It demonstrates our multi-model AI strategy
# by using specialized models for combat-specific interactions.
# 
# KEY RESPONSIBILITIES:
# - Manage turn-based combat encounters with initiative tracking
# - Validate combat actions against 5e rules
# - Coordinate HP tracking, status effects, and combat state
# - Generate and manage pre-rolled dice to prevent AI confusion
# - Cache prerolls per combat round to ensure consistency
# - Track combat rounds through AI responses
# - Provide specialized combat AI prompts and validation
# - Real-time dynamic state display for combat awareness
# 
# COMBAT STATE DISPLAY PHILOSOPHY:
# - REAL-TIME AWARENESS: Shows current HP, spell slots, conditions during combat
# - RESOURCE TRACKING: Displays available spell slots for tactical decisions
# - DYNAMIC UPDATES: Reflects changes immediately as they occur
# - AI CLARITY: Provides authoritative current state to prevent confusion
# 
# COMBAT INFORMATION ARCHITECTURE:
# - DYNAMIC STATE DISPLAY: Current HP, spell slots, active conditions
# - STATIC REFERENCE: Character abilities remain in system messages
# - SEPARATION PRINCIPLE: Combat state vs character capabilities
# - TACTICAL FOCUS: Information relevant to immediate combat decisions
# 
# COMBAT FLOW:
# Encounter Start -> Initiative Roll -> Turn Management -> Action Resolution ->
# Validation -> State Update -> Dynamic State Display -> Win/Loss Conditions
# 
# AI INTEGRATION:
# - Specialized combat model for turn-based interactions
# - Pre-rolled dice system prevents AI attack count confusion
# - Combat-specific validation model for rule compliance
# - Real-time HP and status tracking with state synchronization
# - Dynamic spell slot tracking for spellcaster resource management
# 
# ARCHITECTURAL INTEGRATION:
# - Called by action_handler.py for combat-related actions
# - Uses generate_prerolls.py for dice management
# - Integrates with party_tracker.json for state persistence
# - Implements our "Defense in Depth" validation strategy
# 
# DESIGN PATTERNS:
# - State Machine: Combat phases and turn management
# - Strategy Pattern: Different AI models for different combat aspects
# - Observer Pattern: Real-time combat state updates
# 
# This module exemplifies our approach to complex game system management
# while maintaining strict 5e rule compliance through AI validation.
# ============================================================================

import json
import os
import time
import re
import random
import subprocess
from datetime import datetime
from xp import main as calculate_xp
from openai import OpenAI
# Import model configurations from config.py
from config import (
    OPENAI_API_KEY,
    COMBAT_MAIN_MODEL,
    # Use the existing validation model instead of COMBAT_VALIDATION_MODEL
    DM_VALIDATION_MODEL, 
    COMBAT_DIALOGUE_SUMMARY_MODEL
)
from update_character_info import update_character_info, normalize_character_name
import update_encounter
import update_party_tracker
# Import the preroll generator
from generate_prerolls import generate_prerolls
# Import safe JSON functions
from encoding_utils import safe_json_load
from file_operations import safe_write_json
import cumulative_summary
from enhanced_logger import debug, info, warning, error, game_event, set_script_name

# Set script name for logging
set_script_name(__name__)

# Remove color constants - no longer used
# Color codes removed per CLAUDE.md guidelines

# Temperature
TEMPERATURE = 0.8

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

conversation_history_file = "modules/conversation_history/combat_conversation_history.json"
second_model_history_file = "modules/conversation_history/second_model_history.json"
third_model_history_file = "modules/conversation_history/third_model_history.json"

# Create a combat_logs directory if it doesn't exist
os.makedirs("combat_logs", exist_ok=True)

# Constants for chat history generation
HISTORY_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


def process_defeated_creatures(encounter_data, party_tracker_data):
    """
    Finds defeated named creatures in an encounter and triggers the
    moveBackgroundNPC action to permanently remove them from the world state.
    """
    # Import the action handler locally to prevent circular import errors
    import action_handler
    from enhanced_logger import info, warning, error

    if not encounter_data or not isinstance(encounter_data.get('creatures'), list):
        warning("PROCESS_DEFEATED: Invalid or missing encounter data. Skipping.", category="combat_resolution")
        return

    info("PROCESS_DEFEATED: Checking for defeated named creatures to remove from world state.", category="combat_resolution")
    
    current_location_id = party_tracker_data.get("worldConditions", {}).get("currentLocationId")
    if not current_location_id:
        error("PROCESS_DEFEATED: Could not determine current location ID from party tracker.", category="combat_resolution")
        return

    for creature in encounter_data.get('creatures', []):
        creature_status = creature.get('status', 'alive').lower()
        creature_type = creature.get('type', 'unknown').lower()
        creature_name = creature.get('name')

        # Process creatures that are 'dead' or 'defeated'
        if creature_status in ['dead', 'defeated']:
            # Remove any named non-player creature (enemies, NPCs, named monsters)
            # Skip players and generic unnamed creatures
            if creature_type != 'player' and creature_name:
                
                info(f"PROCESS_DEFEATED: Found defeated creature '{creature_name}'. Triggering removal.", category="combat_resolution")
                
                # Prepare the action to remove the NPC from the location file
                removal_action = {
                    "action": "moveBackgroundNPC",
                    "parameters": {
                        "npcName": creature_name,
                        "context": f"Killed during combat encounter in location {current_location_id}.",
                        "currentLocation": current_location_id
                    }
                }
                
                # Use the existing action_handler to process the removal.
                # We pass None for location_data and conversation_history as this is a backend process.
                action_handler.process_action(removal_action, party_tracker_data, None, None)


def get_current_area_id():
    party_tracker = safe_json_load("party_tracker.json")
    if not party_tracker:
        error("FILE_OP: Failed to load party_tracker.json", category="file_operations")
        return None
    return party_tracker["worldConditions"]["currentAreaId"]

def get_location_data(location_id):
    from module_path_manager import ModulePathManager
    from encoding_utils import safe_json_load
    # Get current module from party tracker for consistent path resolution
    try:
        party_tracker = safe_json_load("party_tracker.json")
        current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
        path_manager = ModulePathManager(current_module)
    except:
        path_manager = ModulePathManager()  # Fallback to reading from file
    
    current_area_id = get_current_area_id()
    debug(f"STATE_CHANGE: Current area ID: {current_area_id}", category="combat_events")
    area_file = path_manager.get_area_path(current_area_id)
    debug(f"FILE_OP: Attempting to load area file: {area_file}", category="file_operations")

    if not os.path.exists(area_file):
        error(f"FILE_OP: Area file {area_file} does not exist", category="file_operations")
        return None

    area_data = safe_json_load(area_file)
    if not area_data:
        error(f"FILE_OP: Failed to load area file: {area_file}", category="file_operations")
        return None
    debug(f"FILE_OP: Loaded area data: {json.dumps(area_data, indent=2)}", category="file_operations")

    for location in area_data["locations"]:
        if location["locationId"] == location_id:
            debug(f"VALIDATION: Found location data for ID {location_id}", category="combat_events")
            return location

    error(f"VALIDATION: Location with ID {location_id} not found in area data", category="combat_events")
    return None

def read_prompt_from_file(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except Exception as e:
        error(f"FILE_OP: Failed to read prompt file {filename}: {str(e)}", category="file_operations")
        return ""

def load_monster_stats(monster_name):
    # Import the path manager
    from module_path_manager import ModulePathManager
    from encoding_utils import safe_json_load
    # Get current module from party tracker for consistent path resolution
    try:
        party_tracker = safe_json_load("party_tracker.json")
        current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
        path_manager = ModulePathManager(current_module)
    except:
        path_manager = ModulePathManager()  # Fallback to reading from file
    
    # Get the correct path for the monster file
    monster_file = path_manager.get_monster_path(monster_name)

    monster_stats = safe_json_load(monster_file)
    if not monster_stats:
        error(f"FILE_OP: Failed to load monster file: {monster_file}", category="file_operations")
    return monster_stats

def load_json_file(file_path):
    data = safe_json_load(file_path)
    if data is None:
        # If file doesn't exist or has invalid JSON, return an empty list
        return []
    return data

def save_json_file(file_path, data):
    try:
        safe_write_json(file_path, data)
    except Exception as e:
        error(f"FILE_OP: Failed to save {file_path}: {str(e)}", category="file_operations")

def clean_old_dm_notes(conversation_history):
    """
    Clean up old Dungeon Master Notes from conversation history while preserving critical information.
    Keeps round tracking, HP status, and basic combat state for the last 3 rounds.
    This reduces token usage while maintaining enough context for proper combat flow.
    """
    # Find all DM note indices
    dm_note_indices = []
    for i, message in enumerate(conversation_history):
        if message.get("role") == "user" and "Dungeon Master Note:" in message.get("content", ""):
            dm_note_indices.append(i)
    
    # Keep the last 3 DM notes fully intact, clean older ones
    keep_full_count = 3
    
    for i, message in enumerate(conversation_history):
        if (message.get("role") == "user" and 
            "Dungeon Master Note:" in message.get("content", "")):
            
            # Check if this is one of the recent DM notes to keep
            note_index_in_list = dm_note_indices.index(i) if i in dm_note_indices else -1
            if note_index_in_list >= len(dm_note_indices) - keep_full_count:
                # Keep this note fully intact
                continue
            
            # Clean older DM notes but preserve essential information
            content = message["content"]
            
            # Extract round information
            round_match = re.search(r"COMBAT ROUND (\d+)", content)
            round_info = f"Round {round_match.group(1)}" if round_match else ""
            
            # Extract HP state information
            hp_pattern = r"HP: \d+/\d+"
            hp_matches = re.findall(hp_pattern, content)
            hp_info = ", ".join(hp_matches) if hp_matches else ""
            
            # Extract player's message
            player_split = content.split("Player:", 1)
            player_msg = player_split[1].strip() if len(player_split) == 2 else ""
            
            # Construct cleaned message with essential info
            cleaned_parts = []
            if round_info:
                cleaned_parts.append(round_info)
            if hp_info:
                cleaned_parts.append(f"HP: {hp_info}")
            if player_msg:
                cleaned_parts.append(f"Player: {player_msg}")
            
            if cleaned_parts:
                message["content"] = f"Dungeon Master Note: {'. '.join(cleaned_parts)}"
            else:
                message["content"] = "Dungeon Master Note: [Previous turn]"
    
    return conversation_history

def is_valid_json(json_string):
    try:
        json_object = json.loads(json_string)
        if not isinstance(json_object, dict):
            return False
        if "narration" not in json_object or not isinstance(json_object["narration"], str):
            return False
        if "actions" not in json_object or not isinstance(json_object["actions"], list):
            return False
        # Optional plan field - if present, must be a string
        if "plan" in json_object and not isinstance(json_object["plan"], str):
            return False
        return True
    except json.JSONDecodeError:
        return False

def write_debug_output(content, filename="debug_second_model.json"):
    try:
        with open(filename, "w") as debug_file:
            json.dump(content, debug_file, indent=2)
    except Exception as e:
        debug(f"FILE_OP: Writing debug output failed - {str(e)}", category="file_operations")

def parse_json_safely(text):
    """Extract and parse JSON from text, handling various formats"""
    # First, try to parse as-is
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract from code block
    try:
        match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except json.JSONDecodeError:
        pass

    # If all else fails, try to find any JSON-like structure
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except json.JSONDecodeError:
        pass

    # If we still can't parse it, raise an exception
    raise json.JSONDecodeError("Unable to parse JSON from the given text", text, 0)

def check_multiple_update_encounter(actions):
    """Check if there are multiple updateEncounter actions that should be consolidated"""
    if not isinstance(actions, list):
        return False
    
    update_encounter_count = 0
    for action in actions:
        if isinstance(action, dict) and action.get("action", "").lower() == "updateencounter":
            update_encounter_count += 1
    
    return update_encounter_count > 1

def create_consolidation_prompt(parsed_response):
    """Create a retry prompt for consolidating multiple updateEncounter actions"""
    actions = parsed_response.get("actions", [])
    
    # Extract all updateEncounter changes
    encounter_changes = []
    encounter_id = None
    
    for action in actions:
        if action.get("action", "").lower() == "updateencounter":
            params = action.get("parameters", {})
            if not encounter_id:
                encounter_id = params.get("encounterId", "")
            changes = params.get("changes", "")
            if changes:
                encounter_changes.append(changes)
    
    # Create the consolidated changes description
    # Add proper punctuation between changes
    consolidated_changes = ". ".join(encounter_changes)
    if not consolidated_changes.endswith("."):
        consolidated_changes += "."
    
    retry_prompt = f"""Your previous response contained multiple updateEncounter actions, but these must be consolidated into ONE action.

IMPORTANT RULES:
1. ALL monster/enemy changes must be in ONE updateEncounter action
2. updateCharacterInfo is ONLY for players and NPCs (never monsters)
3. updateEncounter is ONLY for monsters/enemies (never players or NPCs)

You had {len(encounter_changes)} separate updateEncounter actions with these changes:
{chr(10).join(f'- {change}' for change in encounter_changes)}

Please provide a new response with:
1. The same narration and combat_round
2. ONE updateEncounter action combining all monster changes: "{consolidated_changes}"
3. Keep all other actions (updateCharacterInfo, exit, etc.) unchanged

Remember: One updateEncounter for ALL monster changes, separate updateCharacterInfo for each player/NPC change."""
    
    return retry_prompt

def create_multiple_update_requery_prompt(parsed_response):
    """Create a requery prompt when multiple updateEncounter actions are detected"""
    actions = parsed_response.get("actions", [])
    
    # Count updateEncounter actions
    update_encounter_count = 0
    for action in actions:
        if isinstance(action, dict) and action.get("action", "").lower() == "updateencounter":
            update_encounter_count += 1
    
    retry_prompt = f"""Your response contained {update_encounter_count} updateEncounter actions. This is incorrect - you must use ONLY ONE updateEncounter action that describes ALL monster changes.

CRITICAL ACTION DISTINCTION - NEVER CONFUSE THESE:
- updateCharacterInfo: Use ONLY for players (your character) and NPCs (allies/neutral characters)
  - These have their own character files that store their HP, inventory, etc.
  - Example: updateCharacterInfo for "Eirik Hearthwise" (player) or "Scout Kira" (NPC)
  
- updateEncounter: Use ONLY for monsters/enemies in the encounter
  - These exist only within the encounter file
  - Use ONE updateEncounter action that describes ALL monster changes
  - Example: updateEncounter describing "Goblin takes 10 damage (HP 15 -> 5). Orc takes 8 damage (HP 20 -> 12)."

REMEMBER: 
- The encounter file references player/NPC files but doesn't store their HP
- Monster HP is stored directly in the encounter file
- Use exactly ONE updateEncounter action for ALL monster changes in a turn

Please provide a corrected response that:
1. Uses exactly ONE updateEncounter action for all monster changes
2. Uses updateCharacterInfo for any player/NPC changes
3. Consolidates all monster updates into the single updateEncounter's changes field"""
    
    return retry_prompt

def sanitize_unicode_for_logging(text):
    """
    Replace common Unicode characters with ASCII equivalents for logging compatibility.
    Prevents UnicodeEncodeError when logging to files on Windows.
    """
    if not isinstance(text, str):
        return text
    
    # Replace common Unicode characters with ASCII equivalents
    replacements = {
        '\u2192': '->',  # Right arrow
        '\u2190': '<-',  # Left arrow
        '\u2194': '<->',  # Left-right arrow
        '\u2014': '--',  # Em dash
        '\u2013': '-',   # En dash
        '\u201c': '"',   # Left double quotation mark
        '\u201d': '"',   # Right double quotation mark
        '\u2018': "'",   # Left single quotation mark
        '\u2019': "'",   # Right single quotation mark
        '\u2026': '...',  # Horizontal ellipsis
    }
    
    for unicode_char, ascii_replacement in replacements.items():
        text = text.replace(unicode_char, ascii_replacement)
    
    return text

def validate_combat_response(response, encounter_data, user_input, conversation_history=None):
    """
    Validate a combat response for accuracy in HP tracking, combat flow, etc.
    Returns True if valid, or a string with the reason for failure if invalid.
    """
    print(f"[COMBAT_MANAGER] Starting validation for combat response")
    debug("VALIDATION: Validating combat response...", category="combat_validation")
    
    # Load validation prompt from file
    validation_prompt = read_prompt_from_file('combat_validation_prompt.txt')
    
    # Start with validation prompt
    validation_conversation = [
        {"role": "system", "content": validation_prompt}
    ]
    
    # Add previous 12 user/assistant pairs for context
    if conversation_history and len(conversation_history) > 24:
        # Get the last 25 messages (12 pairs + current user input)
        # But exclude the current user input since we'll add it separately
        recent_messages = conversation_history[-25:-1]  # Last 24 messages before current
        
        # Filter to only user/assistant messages (no system messages)
        context_messages = [
            msg for msg in recent_messages 
            if msg["role"] in ["user", "assistant"]
        ][-24:]  # Ensure we only get last 24 (12 pairs)
        
        # Add context header and messages
        validation_conversation.append({
            "role": "system", 
            "content": "=== PREVIOUS COMBAT CONTEXT (last 12 exchanges) ==="
        })
        validation_conversation.extend(context_messages)
    
    # Add current validation data
    validation_conversation.extend([
        {"role": "system", "content": "=== CURRENT VALIDATION DATA ==="},
        {"role": "system", "content": f"Encounter Data:\n{json.dumps(encounter_data, indent=2)}"},
        {"role": "user", "content": f"Player Input: {user_input}"},
        {"role": "assistant", "content": response}
    ])

    max_validation_retries = 3
    for attempt in range(max_validation_retries):
        try:
            validation_result = client.chat.completions.create(
                model=DM_VALIDATION_MODEL,
                temperature=0.3,  # Lower temperature for more consistent validation
                messages=validation_conversation
            )

            validation_response = validation_result.choices[0].message.content.strip()
            
            try:
                validation_json = parse_json_safely(validation_response)
                is_valid = validation_json.get("valid", False)
                reason = validation_json.get("reason", "No reason provided")
                recommendation = validation_json.get("recommendation", "")

                # Log validation results
                with open("combat_validation_log.json", "a") as log_file:
                    log_entry = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "valid": is_valid,
                        "reason": sanitize_unicode_for_logging(reason),
                        "recommendation": sanitize_unicode_for_logging(recommendation),
                        "response": sanitize_unicode_for_logging(response)
                    }
                    json.dump(log_entry, log_file)
                    log_file.write("\n")

                if is_valid:
                    print(f"[COMBAT_MANAGER] Validation PASSED")
                    debug("VALIDATION: Combat response validation passed", category="combat_validation")
                    return True
                else:
                    print(f"[COMBAT_MANAGER] Validation FAILED: {sanitize_unicode_for_logging(reason)}")
                    debug(f"VALIDATION: Combat response validation failed. Reason: {sanitize_unicode_for_logging(reason)}", category="combat_validation")
                    if recommendation:
                        return {"reason": sanitize_unicode_for_logging(reason), "recommendation": sanitize_unicode_for_logging(recommendation)}
                    else:
                        return sanitize_unicode_for_logging(reason)
                    
            except json.JSONDecodeError:
                debug(f"VALIDATION: Invalid JSON from validation model (Attempt {attempt + 1}/{max_validation_retries})", category="combat_validation")
                debug(f"VALIDATION: Problematic response: {validation_response}", category="combat_validation")
                continue
                
        except Exception as e:
            debug(f"VALIDATION: Validation error - {str(e)}", category="combat_validation")
            continue
    
    # If we've exhausted all retries and still don't have a valid result
    warning("VALIDATION: Validation failed after max retries, assuming response is valid", category="combat_validation")
    return True

def normalize_encounter_status(encounter_data):
    """Normalizes status values in encounter data to lowercase"""
    if not encounter_data or not isinstance(encounter_data, dict):
        return encounter_data
        
    # Convert status values to lowercase
    for creature in encounter_data.get('creatures', []):
        if 'status' in creature:
            creature['status'] = creature['status'].lower()
    
    return encounter_data

def get_initiative_order(encounter_data):
    """Generate initiative order string for combat validation context"""
    if not encounter_data or not isinstance(encounter_data, dict):
        return "Initiative order unknown"
        
    creatures = encounter_data.get("creatures", [])
    if not creatures:
        return "No creatures in encounter"
    
    # Sort by initiative (descending), then alphabetically for ties
    sorted_creatures = sorted(creatures, key=lambda x: (-x.get("initiative", 0), x.get("name", "")))
    
    order_parts = []
    for creature in sorted_creatures:
        name = creature.get("name", "Unknown")
        initiative = creature.get("initiative", 0)
        status = creature.get("status", "unknown")
        order_parts.append(f"{name} ({initiative}, {status})")
    
    return " -> ".join(order_parts)

def log_conversation_structure(conversation):
    """Log the structure of the conversation history for debugging"""
    debug("VALIDATION: Conversation Structure:", category="combat_validation")
    debug(f"Total messages: {len(conversation)}", category="combat_validation")
    
    roles = {}
    for i, msg in enumerate(conversation):
        role = msg.get("role", "unknown")
        content_preview = msg.get("content", "")[:50].replace("\n", " ") + "..."
        roles[role] = roles.get(role, 0) + 1
        debug(f"  [{i}] {role}: {content_preview}", category="combat_validation")
    
    debug("Message count by role:", category="combat_validation")
    for role, count in roles.items():
        debug(f"  {role}: {count}", category="combat_validation")
    # Empty line for debug output


def summarize_dialogue(conversation_history_param, location_data, party_tracker_data):
    debug("AI_CALL: Activating the third model...", category="ai_operations")
    
    # Extract clean narrative content from conversation history
    clean_conversation = []
    for message in conversation_history_param:
        if message.get("role") == "system":
            continue  # Skip system messages
        elif message.get("role") == "user":
            clean_conversation.append(f"Player: {message.get('content', '')}")
        elif message.get("role") == "assistant":
            content = message.get("content", "")
            try:
                # Try to parse JSON and extract narration
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "narration" in parsed:
                    clean_conversation.append(f"Dungeon Master: {parsed['narration']}")
                else:
                    clean_conversation.append(f"Dungeon Master: {content}")
            except json.JSONDecodeError:
                # If not JSON, use as-is
                clean_conversation.append(f"Dungeon Master: {content}")
    
    clean_text = "\n\n".join(clean_conversation)
    
    dialogue_summary_prompt = [
        {"role": "system", "content": "Your task is to provide a concise summary of the combat encounter in the world's most popular 5th Edition roleplayign game dialogue between the dungeon master running the combat encounter and the player. Focus on capturing the key events, actions, and outcomes of the encounter. Be sure to include the experience points awarded, which will be provided in the conversation history. The summary should be written in a narrative style suitable for presenting to the main dungeon master. Include in your summary any defeated monsters or corpses left behind after combat."},
        {"role": "user", "content": clean_text}
    ]

    # Generate dialogue summary
    response = client.chat.completions.create(
        model=COMBAT_DIALOGUE_SUMMARY_MODEL, # Use imported model
        temperature=TEMPERATURE,
        messages=dialogue_summary_prompt
    )

    dialogue_summary = response.choices[0].message.content.strip()

    current_location_id = party_tracker_data["worldConditions"]["currentLocationId"]
    debug(f"STATE_CHANGE: Current location ID: {current_location_id}", category="encounter_setup")

    if location_data and location_data.get("locationId") == current_location_id:
        encounter_id = party_tracker_data["worldConditions"]["activeCombatEncounter"]
        new_encounter = {
            "encounterId": encounter_id,
            "summary": dialogue_summary,
            "impact": "To be determined",
            "worldConditions": {
                "year": int(party_tracker_data["worldConditions"]["year"]),
                "month": party_tracker_data["worldConditions"]["month"],
                "day": int(party_tracker_data["worldConditions"]["day"]),
                "time": party_tracker_data["worldConditions"]["time"]
            }
        }
        if "encounters" not in location_data:
            location_data["encounters"] = []
        location_data["encounters"].append(new_encounter)
        if not location_data.get("adventureSummary"):
            location_data["adventureSummary"] = dialogue_summary
        else:
            location_data["adventureSummary"] += f"\n\n{dialogue_summary}"

        from module_path_manager import ModulePathManager
        from encoding_utils import safe_json_load
        # Get current module from party tracker for consistent path resolution
        try:
            party_tracker = safe_json_load("party_tracker.json")
            current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
            path_manager = ModulePathManager(current_module)
        except:
            path_manager = ModulePathManager()  # Fallback to reading from file
        current_area_id = get_current_area_id()
        area_file = path_manager.get_area_path(current_area_id)
        area_data = safe_json_load(area_file)
        if not area_data:
            error(f"FILE_OP: Failed to load area file: {area_file}", category="file_operations")
            return dialogue_summary
        
        for i, loc in enumerate(area_data["locations"]):
            if loc["locationId"] == current_location_id:
                area_data["locations"][i] = location_data
                break
        
        if not safe_write_json(area_file, area_data):
            error(f"FILE_OP: Failed to save area file: {area_file}", category="file_operations")
        debug(f"STATE_CHANGE: Encounter {encounter_id} added to {area_file}.", category="encounter_setup")

        conversation_history_param.append({"role": "assistant", "content": f"Combat Summary: {dialogue_summary}"})
        conversation_history_param.append({"role": "user", "content": "The combat has concluded. What would you like to do next?"})

        debug(f"FILE_OP: Attempting to write to file: {conversation_history_file}", category="file_operations")
        if not safe_write_json(conversation_history_file, conversation_history_param):
            error("FILE_OP: Failed to save conversation history", category="file_operations")
        else:
            debug("FILE_OP: Conversation history saved successfully", category="file_operations")
        info("SUCCESS: Conversation history updated with encounter summary.", category="combat_events")
    else:
        error(f"VALIDATION: Location {current_location_id} not found in location data or location data is incorrect.", category="combat_events")
    return dialogue_summary

def merge_updates(original_data, updated_data):
    fields_to_update = ['hitPoints', 'equipment', 'attacksAndSpellcasting', 'experience_points']

    for field in fields_to_update:
        if field in updated_data:
            if field in ['equipment', 'attacksAndSpellcasting']:
                # For arrays, replace the entire array
                original_data[field] = updated_data[field]
            elif field == 'experience_points':
                # For XP, only update if the new value is greater than the existing value
                if updated_data[field] > original_data.get(field, 0):
                    original_data[field] = updated_data[field]
            else:
                # For simple fields like hitpoints, just update the value
                original_data[field] = updated_data[field]

    return original_data

def update_json_schema(ai_response, player_info, encounter_data, party_tracker_data):
    # Extract XP information if present
    xp_info = None
    if "XP Awarded:" in ai_response:
        xp_info = ai_response.split("XP Awarded:")[-1].strip()

    # Update player information, including XP
    player_name = normalize_character_name(player_info['name'])
    player_changes = f"Update the character's experience points. XP Awarded: {xp_info}"
    update_success = update_character_info(player_name, player_changes)
    
    if update_success:
        debug(f"SUCCESS: Successfully updated player XP", category="xp_tracking")
        # CRITICAL FIX: Reload the player data after update to get the new XP
        from module_path_manager import ModulePathManager
        from encoding_utils import safe_json_load
        
        # Get current module from party tracker
        current_module = party_tracker_data.get("module", "").replace(" ", "_")
        path_manager = ModulePathManager(current_module)
        player_file = path_manager.get_character_path(player_name)
        
        # Reload the updated player data
        updated_player_info = safe_json_load(player_file)
        if updated_player_info:
            debug(f"SUCCESS: Reloaded player data with updated XP: {updated_player_info.get('experience_points', 'unknown')}", category="xp_tracking")
        else:
            error("FAILURE: Failed to reload updated player data", category="character_updates")
            updated_player_info = player_info  # Fallback to original if reload fails
    else:
        error("FAILURE: Failed to update player info", category="character_updates")
        updated_player_info = player_info  # Keep original on failure

    # Update encounter information (monsters only, no XP)
    encounter_id = encounter_data['encounterId']
    encounter_changes = "Combat has ended. Update status of monster creatures as needed."
    updated_encounter_data = update_encounter.update_encounter(encounter_id, encounter_changes)

    # Update NPCs if needed (no XP for NPCs)
    for creature in encounter_data['creatures']:
        if creature['type'] == 'npc':
            from module_path_manager import ModulePathManager
            path_manager = ModulePathManager()
            npc_name = path_manager.format_filename(creature['name']) # Format for file access
            npc_changes = "Update NPC status after combat."
            update_character_info(npc_name, npc_changes)

    # Update party tracker: store last combat encounter before removing active one
    if 'worldConditions' in party_tracker_data and 'activeCombatEncounter' in party_tracker_data['worldConditions']:
        # Save the encounter ID before clearing it
        last_encounter_id = party_tracker_data["worldConditions"]["activeCombatEncounter"]
        if last_encounter_id:  # Only save if not empty
            party_tracker_data["worldConditions"]["lastCompletedEncounter"] = last_encounter_id
        # Clear the active encounter
        party_tracker_data['worldConditions']['activeCombatEncounter'] = ""

    # Save the updated party_tracker.json file
    if not safe_write_json("party_tracker.json", party_tracker_data):
        error("FILE_OP: Failed to save party_tracker.json", category="file_operations")

    return updated_player_info, updated_encounter_data, party_tracker_data

def generate_chat_history(conversation_history, encounter_id):
    """
    Generate a lightweight combat chat history without system messages
    for a specific encounter ID
    """
    # Create a formatted timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime(HISTORY_TIMESTAMP_FORMAT)

    # Create directory for this encounter if it doesn't exist
    encounter_dir = f"combat_logs/{encounter_id}"
    os.makedirs(encounter_dir, exist_ok=True)

    # Create a unique filename based on encounter ID and timestamp
    output_file = f"{encounter_dir}/combat_chat_{timestamp}.json"

    try:
        # Filter out system messages and keep only user and assistant messages
        chat_history = [msg for msg in conversation_history if msg["role"] != "system"]

        # Write the filtered chat history to the output file
        if not safe_write_json(output_file, chat_history):
            error(f"FILE_OP: Failed to save chat history to {output_file}", category="file_operations")

        # Print statistics
        system_count = len(conversation_history) - len(chat_history)
        total_count = len(conversation_history)
        user_count = sum(1 for msg in chat_history if msg["role"] == "user")
        assistant_count = sum(1 for msg in chat_history if msg["role"] == "assistant")

        info("SUCCESS: Combat chat history updated!", category="combat_events")
        debug(f"Encounter ID: {encounter_id}", category="combat_events")
        debug(f"System messages removed: {system_count}", category="combat_events")
        debug(f"SUMMARY: User messages: {user_count}", category="combat_logs")
        debug(f"SUMMARY: Assistant messages: {assistant_count}", category="combat_logs")
        debug(f"SUMMARY: Total messages (including system): {total_count}", category="combat_logs")
        info(f"SUCCESS: Output saved to: {output_file}", category="combat_logs")

        # Also create/update the latest version of this encounter for easy reference
        latest_file = f"{encounter_dir}/combat_chat_latest.json"
        if not safe_write_json(latest_file, chat_history):
            error("FILE_OP: Failed to save latest chat history", category="file_operations")
        info(f"SUCCESS: Latest version also saved to: {latest_file}", category="combat_logs")

        # Save a combined latest file for all encounters as well
        all_latest_file = f"combat_logs/all_combat_latest.json"
        try:
            # Load existing all-combat history if it exists
            if os.path.exists(all_latest_file):
                with open(all_latest_file, "r", encoding="utf-8") as f:
                    all_combat_data = json.load(f)
            else:
                all_combat_data = {}

            # Add or update this encounter's data
            all_combat_data[encounter_id] = {
                "timestamp": timestamp,
                "messageCount": len(chat_history),
                "history": chat_history
            }

            # Write the combined file
            with open(all_latest_file, "w", encoding="utf-8") as f:
                json.dump(all_combat_data, f, indent=2)

        except Exception as e:
            error(f"FAILURE: Error updating combined combat log", exception=e, category="combat_logs")

    except Exception as e:
        error(f"FAILURE: Error generating combat chat history", exception=e, category="combat_logs")

def sync_active_encounter():
    """Sync player and NPC data to the active encounter file if one exists"""
    from module_path_manager import ModulePathManager
    from encoding_utils import safe_json_load
    # Get current module from party tracker for consistent path resolution
    try:
        party_tracker = safe_json_load("party_tracker.json")
        current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
        path_manager = ModulePathManager(current_module)
    except:
        path_manager = ModulePathManager()  # Fallback to reading from file
    
    # Check if there's an active combat encounter
    try:
        party_tracker = safe_json_load("party_tracker.json")
        if not party_tracker:
            error("FAILURE: Failed to load party_tracker.json", category="file_operations")
            return
        
        active_encounter_id = party_tracker.get("worldConditions", {}).get("activeCombatEncounter", "")
        if not active_encounter_id:
            # No active encounter, nothing to sync
            return
            
        # Load the encounter file
        encounter_file = f"modules/encounters/encounter_{active_encounter_id}.json"
        encounter_data = safe_json_load(encounter_file)
        if not encounter_data:
            error(f"FAILURE: Failed to load encounter file: {encounter_file}", category="file_operations")
            return {}
            
        # Track if any changes were made
        changes_made = False
            
        # Update player and NPC data in the encounter
        for creature in encounter_data.get("creatures", []):
            if creature["type"] == "player":
                player_file = path_manager.get_character_path(normalize_character_name(creature['name']))
                try:
                    player_data = safe_json_load(player_file)
                    if not player_data:
                        error(f"FAILURE: Failed to load player file: {player_file}", category="file_operations")
                        # Update combat-relevant fields
                        if creature.get("currentHitPoints") != player_data.get("hitPoints"):
                            creature["currentHitPoints"] = player_data.get("hitPoints")
                            changes_made = True
                        if creature.get("maxHitPoints") != player_data.get("maxHitPoints"):
                            creature["maxHitPoints"] = player_data.get("maxHitPoints")
                            changes_made = True
                        if creature.get("status") != player_data.get("status"):
                            creature["status"] = player_data.get("status")
                            changes_made = True
                        if creature.get("conditions") != player_data.get("condition_affected"):
                            creature["conditions"] = player_data.get("condition_affected", [])
                            changes_made = True
                except Exception as e:
                    error(f"FAILURE: Failed to sync player data to encounter", exception=e, category="encounter_setup")
                    
            elif creature["type"] == "npc":
                npc_name = path_manager.format_filename(creature['name'])
                npc_file = path_manager.get_character_path(npc_name)
                try:
                    npc_data = safe_json_load(npc_file)
                    if not npc_data:
                        error(f"FAILURE: Failed to load NPC file: {npc_file}", category="file_operations")
                    else:
                        # Update combat-relevant fields
                        if creature.get("currentHitPoints") != npc_data.get("hitPoints"):
                            creature["currentHitPoints"] = npc_data.get("hitPoints")
                            changes_made = True
                        if creature.get("maxHitPoints") != npc_data.get("maxHitPoints"):
                            creature["maxHitPoints"] = npc_data.get("maxHitPoints")
                            changes_made = True
                        if creature.get("status") != npc_data.get("status"):
                            creature["status"] = npc_data.get("status")
                            changes_made = True
                        if creature.get("conditions") != npc_data.get("condition_affected"):
                            creature["conditions"] = npc_data.get("condition_affected", [])
                            changes_made = True
                except Exception as e:
                    error(f"FAILURE: Failed to sync NPC data to encounter", exception=e, category="encounter_setup")
        
        # Save the encounter file if changes were made
        if changes_made:
            if not safe_write_json(encounter_file, encounter_data):
                error(f"FAILURE: Failed to save encounter file: {encounter_file}", category="file_operations")
            debug(f"SUCCESS: Active encounter {active_encounter_id} synced with latest character data", category="encounter_setup")
            
    except Exception as e:
        error(f"FAILURE: Error in sync_active_encounter", exception=e, category="encounter_setup")

def filter_dynamic_fields(data):
    """Remove dynamic combat fields from character/monster data for system prompts"""
    dynamic_fields = ['hitPoints', 'maxHitPoints', 'status', 'condition', 'condition_affected', 
                     'temporaryEffects', 'currentHitPoints']
    return {k: v for k, v in data.items() if k not in dynamic_fields}

def filter_encounter_for_system_prompt(encounter_data):
    """Remove preroll cache and other private data from encounter before sharing with AI"""
    if not encounter_data or not isinstance(encounter_data, dict):
        return encounter_data
    
    # Create a copy to avoid modifying original data
    filtered_data = encounter_data.copy()
    
    # Remove preroll cache - this should never be visible to the AI
    if 'preroll_cache' in filtered_data:
        del filtered_data['preroll_cache']
    
    # Remove any other internal tracking fields that shouldn't be shared
    internal_fields = ['turn_tracker', 'debug_info', 'system_notes']
    for field in internal_fields:
        if field in filtered_data:
            del filtered_data[field]
    
    debug("STATE_CHANGE: Filtered encounter data for system prompt, removed preroll cache", category="combat_events")
    return filtered_data

def run_combat_simulation(encounter_id, party_tracker_data, location_info):
   """Main function to run the combat simulation"""
   print(f"\n[COMBAT_MANAGER] ========== COMBAT SIMULATION START ==========")
   print(f"[COMBAT_MANAGER] Encounter ID: {encounter_id}")
   print(f"[COMBAT_MANAGER] Location: {location_info.get('location_name', 'Unknown')}")
   print(f"[COMBAT_MANAGER] Starting INTERACTIVE combat with player turns")
   debug(f"INITIALIZATION: Starting combat simulation for encounter {encounter_id}", category="combat_events")
   
   # Initialize path manager
   from module_path_manager import ModulePathManager
   from encoding_utils import safe_json_load
   # Get current module from party tracker for consistent path resolution
   try:
       party_tracker = safe_json_load("party_tracker.json")
       current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
       path_manager = ModulePathManager(current_module)
   except:
       path_manager = ModulePathManager()  # Fallback to reading from file

   # Initialize conversation history with the original structure
   conversation_history = [
       {"role": "system", "content": read_prompt_from_file('combat_sim_prompt.txt')},
       {"role": "system", "content": f"Current Combat Encounter: {encounter_id}"},
       {"role": "system", "content": ""}, # Will hold player data
       {"role": "system", "content": ""}, # Will hold monster templates
       {"role": "system", "content": ""}, # Will hold location info
   ]
   
   # Initialize secondary model histories
   second_model_history = []
   third_model_history = []
   
   # Save empty histories to files to reset them
   save_json_file(conversation_history_file, conversation_history)
   save_json_file(second_model_history_file, second_model_history)
   save_json_file(third_model_history_file, third_model_history)
   
   # Load encounter data
   json_file_path = f"modules/encounters/encounter_{encounter_id}.json"
   print(f"[COMBAT_MANAGER] Loading encounter file: {json_file_path}")
   try:
       encounter_data = safe_json_load(json_file_path)
       if not encounter_data:
           print(f"[COMBAT_MANAGER] Failed to load encounter file")
           error(f"FAILURE: Failed to load encounter file {json_file_path}", category="file_operations")
           return None, None
       print(f"[COMBAT_MANAGER] Encounter loaded: {len(encounter_data.get('creatures', []))} creatures")
   except Exception as e:
       print(f"[COMBAT_MANAGER] Exception loading encounter: {str(e)}")
       error(f"FAILURE: Failed to load encounter file {json_file_path}", exception=e, category="file_operations")
       return None, None
   
   # Initialize data containers
   player_info = None
   monster_templates = {}
   npc_templates = {}
   
   # Extract data for all creatures in the encounter
   for creature in encounter_data["creatures"]:
       if creature["type"] == "player":
           player_name = normalize_character_name(creature["name"])
           player_file = path_manager.get_character_path(player_name)
           print(f"[COMBAT_MANAGER] Loading player: {creature['name']} from {player_file}")
           try:
               player_info = safe_json_load(player_file)
               if not player_info:
                   print(f"[COMBAT_MANAGER] Failed to load player file")
                   error(f"FAILURE: Failed to load player file: {player_file}", category="file_operations")
                   return None, None
               print(f"[COMBAT_MANAGER] Player loaded successfully")
           except Exception as e:
               print(f"[COMBAT_MANAGER] Exception loading player: {str(e)}")
               error(f"FAILURE: Failed to load player file {player_file}", exception=e, category="file_operations")
               return None, None
       
       elif creature["type"] == "enemy":
           monster_type = creature["monsterType"]
           if monster_type not in monster_templates:
               monster_file = path_manager.get_monster_path(monster_type)
               print(f"[COMBAT_MANAGER] Loading monster: {creature['name']} (type: {monster_type})")
               debug(f"FILE_OP: Attempting to load monster file: {monster_file}", category="file_operations")
               try:
                   monster_data = safe_json_load(monster_file)
                   if monster_data:
                       monster_templates[monster_type] = monster_data
                       print(f"[COMBAT_MANAGER] Monster loaded successfully: {monster_type}")
                       debug(f"SUCCESS: Successfully loaded monster: {monster_type}", category="file_operations")
                   else:
                       print(f"[COMBAT_MANAGER] Failed to load monster file")
                       error(f"FILE_OP: Failed to load monster file: {monster_file}", category="file_operations")
               except FileNotFoundError as e:
                   error(f"FAILURE: Monster file not found: {monster_file}", category="file_operations")
                   error(f"FAILURE: {str(e)}", category="file_operations")
                   # Check available files for debugging
                   monster_dir = f"{path_manager.module_dir}/monsters"
                   if os.path.exists(monster_dir):
                       debug(f"FILE_OP: Available monster files in {monster_dir}:", category="file_operations")
                       for f in os.listdir(monster_dir):
                           debug(f"  - {f}", category="combat_validation")
                   return None, None
               except json.JSONDecodeError as e:
                   error(f"FAILURE: Invalid JSON in monster file {monster_file}", exception=e, category="file_operations")
                   return None, None
               except Exception as e:
                   error(f"FAILURE: Failed to load monster file {monster_file}", exception=e, category="file_operations")
                   error(f"FAILURE: Exception type: {type(e).__name__}", category="file_operations")
                   import traceback
                   traceback.print_exc()
                   return None, None
       
       elif creature["type"] == "npc":
           # Ensure npc_name is correctly formatted for file access
           npc_file_name_part = path_manager.format_filename(creature["name"]) # Handle names like "NPC_1"
           npc_file = path_manager.get_character_path(npc_file_name_part)
           if npc_file_name_part not in npc_templates: # Check against the base name
               try:
                   npc_data = safe_json_load(npc_file)
                   if npc_data:
                       npc_templates[npc_file_name_part] = npc_data
                   else:
                       error(f"FAILURE: Failed to load NPC file: {npc_file}", category="file_operations")
               except Exception as e:
                   error(f"FAILURE: Failed to load NPC file {npc_file}", exception=e, category="file_operations")
   
   # Populate the system messages with JSON data (filtering out dynamic fields)
   conversation_history[2]["content"] = f"Player Character:\n{json.dumps(filter_dynamic_fields(player_info), indent=2)}"
   conversation_history[3]["content"] = f"Monster Templates:\n{json.dumps({k: filter_dynamic_fields(v) for k, v in monster_templates.items()}, indent=2)}"
   # Verify that we loaded all necessary data
   if not monster_templates and any(c["type"] == "enemy" for c in encounter_data["creatures"]):
       error("FAILURE: No monster templates were loaded!", category="file_operations")
       return None, None
   
   debug(f"INITIALIZATION: Loaded {len(monster_templates)} monster template(s)", category="file_operations")
   for k, v in monster_templates.items():
       debug(f"  - {k}: {v.get('name', 'Unknown')}", category="combat_validation")
   
   conversation_history[4]["content"] = f"Location:\n{json.dumps(location_info, indent=2)}"
   conversation_history.append({"role": "system", "content": f"NPC Templates:\n{json.dumps({k: filter_dynamic_fields(v) for k, v in npc_templates.items()}, indent=2)}"})
   conversation_history.append({"role": "system", "content": f"Encounter Details:\n{json.dumps(filter_encounter_for_system_prompt(encounter_data), indent=2)}"})
   
   # Log the conversation structure for debugging
   log_conversation_structure(conversation_history)
   
   # Save the updated conversation history
   save_json_file(conversation_history_file, conversation_history)
   
   # Prepare initial dynamic state info for all creatures
   dynamic_state_parts = []
   
   # Player info
   player_name_display = player_info["name"]
   current_hp = player_info.get("hitPoints", 0)
   max_hp = player_info.get("maxHitPoints", 0)
   player_status = player_info.get("status", "alive")
   player_condition = player_info.get("condition", "none")
   player_conditions = player_info.get("condition_affected", [])
   
   dynamic_state_parts.append(f"{player_name_display}:")
   dynamic_state_parts.append(f"  - HP: {current_hp}/{max_hp}")
   dynamic_state_parts.append(f"  - Status: {player_status}")
   dynamic_state_parts.append(f"  - Condition: {player_condition}")
   if player_conditions:
       dynamic_state_parts.append(f"  - Active Conditions: {', '.join(player_conditions)}")
   
   # Creature info
   for creature in encounter_data["creatures"]:
       if creature["type"] != "player":
           creature_name = creature.get("name", "Unknown Creature")
           creature_hp = creature.get("currentHitPoints", "Unknown")
           creature_status = creature.get("status", "alive")
           creature_condition = creature.get("condition", "none")
           
           # Get the actual max HP from the correct source
           if creature["type"] == "npc":
               # For NPCs, look up their true max HP from their character file
               npc_name = path_manager.format_filename(creature_name)
               npc_file = path_manager.get_character_path(npc_name)
               try:
                   with open(npc_file, "r") as file:
                       npc_data = json.load(file)
                       creature_max_hp = npc_data["maxHitPoints"]
               except Exception as e:
                   error(f"FAILURE: Failed to get correct max HP for {creature_name}", exception=e, category="combat_events")
                   creature_max_hp = creature.get("maxHitPoints", "Unknown")
           else:
               # For monsters, use the encounter data
               creature_max_hp = creature.get("maxHitPoints", "Unknown")
           
           dynamic_state_parts.append(f"\n{creature_name}:")
           dynamic_state_parts.append(f"  - HP: {creature_hp}/{creature_max_hp}")
           dynamic_state_parts.append(f"  - Status: {creature_status}")
           dynamic_state_parts.append(f"  - Condition: {creature_condition}")
   
   all_dynamic_state = "\n".join(dynamic_state_parts)
   
   # Initialize round tracking and generate prerolls for the initial scene
   round_num = 1
   encounter_data['current_round'] = round_num
   preroll_text = generate_prerolls(encounter_data, round_num=round_num)
   
   # Cache the prerolls
   encounter_data['preroll_cache'] = {
       'round': round_num,
       'rolls': preroll_text,
       'preroll_id': f"{round_num}-{random.randint(1000,9999)}"
   }
   
   # Save the encounter data with initial preroll cache to disk
   save_json_file(json_file_path, encounter_data)
   debug(f"STATE_CHANGE: Saved initial prerolls for round {round_num}", category="combat_events")
   
   # Get initial scene description before first user input
   debug("AI_CALL: Getting initial scene description...", category="combat_events")
   # Generate initiative order for validation context
   initiative_order = get_initiative_order(encounter_data)
   
   initial_prompt = f"""Dungeon Master Note: Respond with valid JSON containing a 'narration' field, 'combat_round' field, and an 'actions' array. This is the start of combat, so please describe the scene and set initiative order, but don't take any actions yet. Start off by hooking the player and engaging them for the start of combat the way any world class dungeon master would.

Important Character Field Definitions:
- 'status' field: Overall life/death state - ONLY use 'alive', 'dead', 'unconscious', or 'defeated' (lowercase)
- 'condition' field: 5e status conditions - use 'none' when no conditions, or valid 5e conditions like 'blinded', 'charmed', 'poisoned', etc.
- NEVER set condition to 'alive' - that goes in the status field
- NEVER set status to 'none' - use 'alive' for conscious characters

Combat Round Tracking:
- MANDATORY: Include "combat_round": 1 in your response (this is round 1)
- Track rounds throughout combat and increment when all creatures have acted

Current dynamic state for all creatures:
{all_dynamic_state}

Initiative Order: {initiative_order}

{preroll_text}

Player: The setup scene for the combat has already been given and described to the party. Now, describe the combat situation and the enemies the party faces."""

   conversation_history.append({"role": "user", "content": initial_prompt})
   save_json_file(conversation_history_file, conversation_history)

   # Get AI response for initial scene with validation and retries
   max_retries = 3
   valid_response = False
   initial_response = None
   validation_attempts = []  # Store all validation attempts for logging
   initial_conversation_length = len(conversation_history)  # Mark where validation started
   
   for attempt in range(max_retries):
       try:
           response = client.chat.completions.create(
               model=COMBAT_MAIN_MODEL,
               temperature=TEMPERATURE,
               messages=conversation_history
           )
           initial_response = response.choices[0].message.content.strip()
           
           # Write raw response to debug file
           with open("debug_initial_response.json", "w") as debug_file:
               json.dump({"raw_initial_response": initial_response}, debug_file, indent=2)
           
           # Temporarily add AI response for validation context
           conversation_history.append({"role": "assistant", "content": initial_response})
           
           # Check if the response is valid JSON
           if not is_valid_json(initial_response):
               debug(f"VALIDATION: Invalid JSON response for initial scene (Attempt {attempt + 1}/{max_retries})", category="combat_validation")
               if attempt < max_retries - 1:
                   # Add error feedback temporarily for next attempt
                   error_msg = "Your previous response was not a valid JSON object with 'narration' and 'actions' fields. Please provide a valid JSON response for the initial scene."
                   conversation_history.append({
                       "role": "user",
                       "content": error_msg
                   })
                   # Log this validation attempt
                   validation_attempts.append({
                       "attempt": attempt + 1,
                       "assistant_response": initial_response,
                       "validation_error": error_msg,
                       "error_type": "json_format"
                   })
                   continue
               else:
                   warning("VALIDATION: Max retries exceeded for JSON validation. Using last response.", category="combat_validation")
                   break
           
           # Parse the JSON response
           parsed_response = json.loads(initial_response)
           narration = parsed_response["narration"]
           actions = parsed_response["actions"]
           
           # Check for multiple updateEncounter actions
           if check_multiple_update_encounter(actions):
               debug(f"VALIDATION: Multiple updateEncounter actions detected (Attempt {attempt + 1}/{max_retries})", category="combat_validation")
               if attempt < max_retries - 1:
                   # Add requery feedback for next attempt
                   requery_msg = create_multiple_update_requery_prompt(parsed_response)
                   conversation_history.append({
                       "role": "user",
                       "content": requery_msg
                   })
                   # Log this validation attempt
                   validation_attempts.append({
                       "attempt": attempt + 1,
                       "assistant_response": initial_response,
                       "validation_error": requery_msg,
                       "error_type": "multiple_update_encounter"
                   })
                   continue
               else:
                   warning("VALIDATION: Max retries exceeded for multiple updateEncounter correction. Using last response.", category="combat_validation")
           
           # Validate the combat logic
           print(f"[COMBAT_MANAGER] Validating initial combat response (Attempt {attempt + 1}/{max_retries})")
           debug("VALIDATION: Validating combat response...", category="combat_validation")
           validation_result = validate_combat_response(initial_response, encounter_data, "The combat begins. Describe the scene and the enemies we face.", conversation_history)
           
           if validation_result is True:
               valid_response = True
               print(f"[COMBAT_MANAGER] Initial scene validation PASSED on attempt {attempt + 1}")
               debug("VALIDATION: Combat response validation passed", category="combat_validation")
               debug(f"SUCCESS: Response validated successfully on attempt {attempt + 1}", category="combat_validation")
               break
           else:
               debug(f"VALIDATION: Response validation failed (Attempt {attempt + 1}/{max_retries})", category="combat_validation")
               
               # Handle both string and dict validation results
               if isinstance(validation_result, dict):
                   reason = validation_result["reason"]
                   recommendation = validation_result.get("recommendation", "")
                   feedback = f"Your previous response had issues with the combat logic: {sanitize_unicode_for_logging(reason)}"
                   if recommendation:
                       feedback += f"\n\n{sanitize_unicode_for_logging(recommendation)}"
               else:
                   reason = validation_result
                   feedback = f"Your previous response had issues with the combat logic: {sanitize_unicode_for_logging(reason)}"
               
               debug(f"VALIDATION: Reason: {sanitize_unicode_for_logging(reason)}", category="combat_validation")
               if attempt < max_retries - 1:
                   # Add error feedback temporarily for next attempt
                   error_msg = f"{feedback}. Please correct these issues and provide a valid initial scene description."
                   conversation_history.append({
                       "role": "user",
                       "content": error_msg
                   })
                   # Log this validation attempt
                   validation_attempts.append({
                       "attempt": attempt + 1,
                       "assistant_response": initial_response,
                       "validation_error": error_msg,
                       "error_type": "combat_logic",
                       "reason": sanitize_unicode_for_logging(reason)
                   })
                   continue
               else:
                   warning("VALIDATION: Max retries exceeded for combat validation. Using last response.", category="combat_validation")
                   break
       except Exception as e:
           error(f"FAILURE: Failed to get or validate initial scene response (Attempt {attempt + 1}/{max_retries})", exception=e, category="combat_events")
           if attempt < max_retries - 1:
               continue
           else:
               warning("VALIDATION: Max retries exceeded. Using last response if available.", category="combat_validation")
               break
   
   # Clean up conversation history based on validation outcome
   if valid_response or initial_response:
       # Remove all validation attempts from conversation history
       conversation_history = conversation_history[:initial_conversation_length]
       
       # Add only the final assistant response
       if initial_response:
           conversation_history.append({"role": "assistant", "content": initial_response})
       
       # Log successful validation if it occurred
       if valid_response and validation_attempts:
           validation_attempts.append({
               "attempt": "final",
               "assistant_response": initial_response,
               "validation_result": "success"
           })
   
   # Write validation attempts to log file
   if validation_attempts:
       validation_log_path = os.path.join(os.path.dirname(conversation_history_file), "combat_validation_log.json")
       try:
           # Load existing log or create new one (JSONL format)
           validation_log = []
           if os.path.exists(validation_log_path):
               with open(validation_log_path, 'r') as f:
                   for line in f:
                       line = line.strip()
                       if line:
                           try:
                               validation_log.append(json.loads(line))
                           except json.JSONDecodeError:
                               continue
           
           # Add current validation session
           validation_log.append({
               "timestamp": datetime.now().isoformat(),
               "encounter_id": encounter_data.get("encounter_id", "unknown"),
               "scene_type": "initial_scene",
               "validation_attempts": validation_attempts,
               "final_outcome": "success" if valid_response else "failed_after_retries"
           })
           
           # Write updated log
           with open(validation_log_path, 'w') as f:
               json.dump(validation_log, f, indent=2)
               
       except Exception as e:
           warning(f"FAILURE: Failed to write validation log", exception=e, category="file_operations")
   
   # Save the cleaned conversation history
   save_json_file(conversation_history_file, conversation_history)
   
   # Display initial scene if we have a response
   if initial_response:
       try:
           parsed_response = json.loads(initial_response)
           narration = parsed_response["narration"]
           print(f"[COMBAT_MANAGER] Initial combat narration ready")
           print(f"Dungeon Master: {narration}")
           # Flush to ensure first combat message is captured by web interface
           import sys
           sys.stdout.flush()
       except Exception as e:
           print(f"[COMBAT_MANAGER] Failed to parse initial response")
           error(f"FAILURE: Failed to parse initial response", exception=e, category="combat_events")
   else:
       error("FAILURE: Failed to get an initial scene description after multiple attempts", category="combat_events")
   
   # Combat loop
   print(f"[COMBAT_MANAGER] Entering main combat loop")
   
   # Update status to show combat is active
   try:
       from status_manager import status_manager
       status_manager.update_status("Combat in progress - awaiting your action", is_processing=False)
   except Exception as e:
       debug(f"Could not update status: {e}", category="status")
   while True:
       # Ensure all character data is synced to the encounter
       print(f"[COMBAT_MANAGER] Syncing character data to encounter")
       
       # Clear processing status when ready for player input
       try:
           from status_manager import status_manager
           status_manager.update_status("", is_processing=False)
       except Exception as e:
           debug(f"Could not clear status: {e}", category="status")
       sync_active_encounter()
       
       # REFRESH CONVERSATION HISTORY WITH LATEST DATA
       debug("STATE_CHANGE: Refreshing conversation history with latest character data...", category="combat_events")
       
       # Reload player info
       player_name = normalize_character_name(player_info["name"])
       player_file = path_manager.get_character_path(player_name)
       try:
           player_info = safe_json_load(player_file)
           if not player_info:
               error(f"FAILURE: Failed to load player file: {player_file}", category="file_operations")
           else:
               # Replace player data in conversation history (with dynamic fields filtered)
               conversation_history[2]["content"] = f"Player Character:\n{json.dumps(filter_dynamic_fields(player_info), indent=2)}"
       except Exception as e:
           error(f"FAILURE: Failed to reload player file {player_file}", exception=e, category="file_operations")
       
       # Reload encounter data
       json_file_path = f"modules/encounters/encounter_{encounter_id}.json"
       try:
           encounter_data = safe_json_load(json_file_path)
           if encounter_data:
               # Find and update the encounter data in conversation history
               for i, msg in enumerate(conversation_history):
                   if msg["role"] == "system" and "Encounter Details:" in msg["content"]:
                       conversation_history[i]["content"] = f"Encounter Details:\n{json.dumps(filter_encounter_for_system_prompt(encounter_data), indent=2)}"
                       break
       except Exception as e:
           error(f"FAILURE: Failed to reload encounter file {json_file_path}", exception=e, category="file_operations")
       
       # Reload NPC data
       for creature in encounter_data["creatures"]:
           if creature["type"] == "npc":
               npc_name = path_manager.format_filename(creature["name"])
               npc_file = path_manager.get_character_path(npc_name)
               try:
                   with open(npc_file, "r") as file:
                       npc_data = json.load(file)
                       # Update the NPC in the templates dictionary
                       npc_templates[npc_name] = npc_data
               except Exception as e:
                   error(f"FAILURE: Failed to reload NPC file {npc_file}", exception=e, category="file_operations")
       
       # Replace NPC templates in conversation history (with dynamic fields filtered)
       for i, msg in enumerate(conversation_history):
           if msg["role"] == "system" and "NPC Templates:" in msg["content"]:
               conversation_history[i]["content"] = f"NPC Templates:\n{json.dumps({k: filter_dynamic_fields(v) for k, v in npc_templates.items()}, indent=2)}"
               break
       
       # Save updated conversation history
       save_json_file(conversation_history_file, conversation_history)
       
       # Display player stats and get input
       player_name_display = player_info["name"]
       current_hp = player_info.get("hitPoints", 0)
       max_hp = player_info.get("maxHitPoints", 0)
       current_xp = player_info.get("experience_points", 0)
       next_level_xp = player_info.get("exp_required_for_next_level", 0)
       current_time_str = party_tracker_data["worldConditions"].get("time", "Unknown")
       
       stats_display = f"[{current_time_str}][HP:{current_hp}/{max_hp}][XP:{current_xp}/{next_level_xp}]"
       
       try:
           user_input_text = input(f"{stats_display} {player_name_display}: ")
       except EOFError:
           error("FAILURE: EOF when reading a line in run_combat_simulation", category="combat_events")
           break
       
       # Skip empty input to prevent infinite loop
       if not user_input_text or not user_input_text.strip():
           continue
       
       # Prepare dynamic state info for all creatures
       dynamic_state_parts = []
       
       # Player info
       player_status = player_info.get("status", "alive")
       player_condition = player_info.get("condition", "none")
       player_conditions = player_info.get("condition_affected", [])
       
       dynamic_state_parts.append(f"{player_name_display}:")
       dynamic_state_parts.append(f"  - HP: {current_hp}/{max_hp}")
       dynamic_state_parts.append(f"  - Status: {player_status}")
       dynamic_state_parts.append(f"  - Condition: {player_condition}")
       if player_conditions:
           dynamic_state_parts.append(f"  - Active Conditions: {', '.join(player_conditions)}")
       
       # Add spell slot information for player if they have spellcasting
       spellcasting = player_info.get("spellcasting", {})
       if spellcasting and "spellSlots" in spellcasting:
           spell_slots = spellcasting["spellSlots"]
           slot_parts = []
           for level in range(1, 10):  # Spell levels 1-9
               level_key = f"level{level}"
               if level_key in spell_slots:
                   slot_data = spell_slots[level_key]
                   current_slots = slot_data.get("current", 0)
                   max_slots = slot_data.get("max", 0)
                   if max_slots > 0:  # Only show levels with available slots
                       slot_parts.append(f"L{level}:{current_slots}/{max_slots}")
           if slot_parts:
               dynamic_state_parts.append(f"  - Spell Slots: {' '.join(slot_parts)}")
       
       # Creature info
       for creature in encounter_data["creatures"]:
           if creature["type"] != "player":
               creature_name = creature.get("name", "Unknown Creature")
               creature_hp = creature.get("currentHitPoints", "Unknown")
               creature_status = creature.get("status", "alive")
               creature_condition = creature.get("condition", "none")
               
               # Get the actual max HP from the correct source
               npc_data = None
               if creature["type"] == "npc":
                   # For NPCs, look up their true max HP from their character file
                   npc_name = path_manager.format_filename(creature_name)
                   npc_file = path_manager.get_character_path(npc_name)
                   try:
                       with open(npc_file, "r") as file:
                           npc_data = json.load(file)
                           creature_max_hp = npc_data["maxHitPoints"]
                   except Exception as e:
                       error(f"FAILURE: Failed to get correct max HP for {creature_name}", exception=e, category="combat_events")
                       creature_max_hp = creature.get("maxHitPoints", "Unknown")
               else:
                   # For monsters, use the encounter data
                   creature_max_hp = creature.get("maxHitPoints", "Unknown")
               
               dynamic_state_parts.append(f"\n{creature_name}:")
               dynamic_state_parts.append(f"  - HP: {creature_hp}/{creature_max_hp}")
               dynamic_state_parts.append(f"  - Status: {creature_status}")
               dynamic_state_parts.append(f"  - Condition: {creature_condition}")
               
               # Add spell slot information for NPCs if they have spellcasting
               if creature["type"] == "npc" and npc_data:
                   npc_spellcasting = npc_data.get("spellcasting", {})
                   if npc_spellcasting and "spellSlots" in npc_spellcasting:
                       npc_spell_slots = npc_spellcasting["spellSlots"]
                       npc_slot_parts = []
                       for level in range(1, 10):  # Spell levels 1-9
                           level_key = f"level{level}"
                           if level_key in npc_spell_slots:
                               slot_data = npc_spell_slots[level_key]
                               current_slots = slot_data.get("current", 0)
                               max_slots = slot_data.get("max", 0)
                               if max_slots > 0:  # Only show levels with available slots
                                   npc_slot_parts.append(f"L{level}:{current_slots}/{max_slots}")
                       if npc_slot_parts:
                           dynamic_state_parts.append(f"  - Spell Slots: {' '.join(npc_slot_parts)}")
       
       all_dynamic_state = "\n".join(dynamic_state_parts)
       
       # Check if we need new prerolls based on round progression
       current_round = encounter_data.get('current_round', 1)
       cached_round = encounter_data.get('preroll_cache', {}).get('round', 0)
       
       if current_round > cached_round:
           # Generate fresh prerolls for new round
           preroll_text = generate_prerolls(encounter_data, round_num=current_round)
           encounter_data['preroll_cache'] = {
               'round': current_round,
               'rolls': preroll_text,
               'preroll_id': f"{current_round}-{random.randint(1000,9999)}"
           }
           # Save the encounter data with preroll cache to disk
           save_json_file(json_file_path, encounter_data)
           debug(f"STATE_CHANGE: Generated new prerolls for round {current_round}", category="combat_events")
       else:
           # Use cached prerolls for current round
           preroll_text = encounter_data.get('preroll_cache', {}).get('rolls', '')
           if preroll_text:
               preroll_id = encounter_data.get('preroll_cache', {}).get('preroll_id', 'unknown')
               debug(f"STATE_CHANGE: Reusing cached prerolls for round {current_round} (ID: {preroll_id})", category="combat_events")
           else:
               # Fallback if cache missing
               preroll_text = generate_prerolls(encounter_data, round_num=current_round)
               encounter_data['preroll_cache'] = {
                   'round': current_round,
                   'rolls': preroll_text,
                   'preroll_id': f"{current_round}-{random.randint(1000,9999)}"
               }
               # Save the encounter data with preroll cache to disk
               save_json_file(json_file_path, encounter_data)
               debug(f"STATE_CHANGE: Generated fallback prerolls for round {current_round}", category="combat_events")
       
       # Generate initiative order for validation context
       initiative_order = get_initiative_order(encounter_data)
       
       # Create a focused, streamlined per-turn prompt
       # Most rules are in the system prompt. This prompt focuses on DYNAMIC state.
       user_input_with_note = f"""--- CURRENT COMBAT STATE ---
Round: {current_round}
Initiative Order: {initiative_order}
All Creatures State:
{all_dynamic_state}

--- PRE-ROLLED DICE FOR NPCS/MONSTERS ---

CRITICAL DICE USAGE - YOU MUST FOLLOW THESE RULES:
1. For an NPC/Monster ATTACK ROLL: You MUST use a die from the '== CREATURE ATTACKS ==' list for that specific creature.
2. For an NPC/Monster SAVING THROW: You MUST use a die from the '== SAVING THROWS ==' list for that specific creature.
3. The '== GENERIC DICE ==' pool is ONLY for damage rolls, spell effects, or other non-attack/non-save rolls.
FAILURE TO USE THE CORRECT POOL IS A CRITICAL ERROR.

{preroll_text}
--- END OF STATE & DICE ---

Player: {user_input_text}"""
       
       # Clean old DM notes before adding new user input
       conversation_history = clean_old_dm_notes(conversation_history)
       
       # Add user input to conversation history
       conversation_history.append({"role": "user", "content": user_input_with_note})
       save_json_file(conversation_history_file, conversation_history)
       
       # Get AI response with validation and retries
       max_retries = 3
       valid_response = False
       ai_response = None
       validation_attempts = []  # Store all validation attempts for logging
       initial_conversation_length = len(conversation_history)  # Mark where validation started
       
       for attempt in range(max_retries):
           try:
               print(f"[COMBAT_MANAGER] Making AI call for player action (attempt {attempt + 1}/{max_retries})")
               print(f"[COMBAT_MANAGER] Processing player input: {user_input_text[:50]}..." if len(user_input_text) > 50 else f"[COMBAT_MANAGER] Processing player input: {user_input_text}")
               
               # Update status to show AI is processing
               try:
                   from status_manager import status_manager
                   status_manager.update_status("Combat AI processing your action...", is_processing=True)
               except Exception as e:
                   debug(f"Could not update status: {e}", category="status")
               
               response = client.chat.completions.create(
                   model=COMBAT_MAIN_MODEL,
                   temperature=TEMPERATURE,
                   messages=conversation_history
               )
               ai_response = response.choices[0].message.content.strip()
               
               print(f"[COMBAT_MANAGER] AI response received ({len(ai_response)} chars)")
               
               
               # Write raw response to debug file
               with open("debug_ai_response.json", "w") as debug_file:
                   json.dump({"raw_ai_response": ai_response}, debug_file, indent=2)
               
               # Temporarily add AI response for validation context
               conversation_history.append({"role": "assistant", "content": ai_response})
               
               # Check if the response is valid JSON
               if not is_valid_json(ai_response):
                   debug(f"VALIDATION: Invalid JSON response from AI (Attempt {attempt + 1}/{max_retries})", category="combat_validation")
                   if attempt < max_retries - 1:
                       # Add error feedback temporarily for next attempt
                       error_msg = "Your previous response was not a valid JSON object with 'narration' and 'actions' fields. Please provide a valid JSON response."
                       conversation_history.append({
                           "role": "user",
                           "content": error_msg
                       })
                       # Log this validation attempt
                       validation_attempts.append({
                           "attempt": attempt + 1,
                           "assistant_response": ai_response,
                           "validation_error": error_msg,
                           "error_type": "json_format"
                       })
                       continue
                   else:
                       warning("VALIDATION: Max retries exceeded for JSON validation. Skipping this response.", category="combat_validation")
                       break
               
               # Parse the JSON response
               parsed_response = json.loads(ai_response)
               narration = parsed_response["narration"]
               actions = parsed_response["actions"]
               
               # Check for multiple updateEncounter actions
               if check_multiple_update_encounter(actions):
                   debug(f"VALIDATION: Multiple updateEncounter actions detected (Attempt {attempt + 1}/{max_retries})", category="combat_validation")
                   if attempt < max_retries - 1:
                       # Add requery feedback for next attempt
                       requery_msg = create_multiple_update_requery_prompt(parsed_response)
                       conversation_history.append({
                           "role": "user",
                           "content": requery_msg
                       })
                       # Log this validation attempt
                       validation_attempts.append({
                           "attempt": attempt + 1,
                           "assistant_response": ai_response,
                           "validation_error": requery_msg,
                           "error_type": "multiple_update_encounter"
                       })
                       continue
                   else:
                       warning("VALIDATION: Max retries exceeded for multiple updateEncounter correction. Using last response.", category="combat_validation")
               
               # Validate the combat logic
               print(f"[COMBAT_MANAGER] Validating combat response (Attempt {attempt + 1}/{max_retries})")
               
               # Update status to show validation is happening
               try:
                   from status_manager import status_manager
                   status_manager.update_status("Validating combat actions...", is_processing=True)
               except Exception as e:
                   debug(f"Could not update status: {e}", category="status")
               
               validation_result = validate_combat_response(ai_response, encounter_data, user_input_text, conversation_history)
               
               if validation_result is True:
                   valid_response = True
                   print(f"[COMBAT_MANAGER] Combat response validation PASSED on attempt {attempt + 1}")
                   debug(f"SUCCESS: Response validated successfully on attempt {attempt + 1}", category="combat_validation")
                   break
               else:
                   debug(f"VALIDATION: Response validation failed (Attempt {attempt + 1}/{max_retries})", category="combat_validation")
                   
                   # Handle both string and dict validation results
                   if isinstance(validation_result, dict):
                       reason = validation_result["reason"]
                       recommendation = validation_result.get("recommendation", "")
                       feedback = f"Your previous response had issues with the combat logic: {reason}"
                       if recommendation:
                           feedback += f"\n\n{recommendation}"
                   else:
                       reason = validation_result
                       feedback = f"Your previous response had issues with the combat logic: {sanitize_unicode_for_logging(reason)}"
                   
                   debug(f"VALIDATION: Reason: {sanitize_unicode_for_logging(reason)}", category="combat_validation")
                   if attempt < max_retries - 1:
                       # Add error feedback temporarily for next attempt
                       error_msg = f"{feedback}. Please correct these issues and try again."
                       conversation_history.append({
                           "role": "user",
                           "content": error_msg
                       })
                       # Log this validation attempt
                       validation_attempts.append({
                           "attempt": attempt + 1,
                           "assistant_response": ai_response,
                           "validation_error": error_msg,
                           "error_type": "combat_logic",
                           "reason": sanitize_unicode_for_logging(reason)
                       })
                       continue
                   else:
                       warning("VALIDATION: Max retries exceeded for combat validation. Using last response.", category="combat_validation")
                       break
           except Exception as e:
               error(f"FAILURE: Failed to get or validate AI response (Attempt {attempt + 1}/{max_retries})", exception=e, category="combat_events")
               if attempt < max_retries - 1:
                   continue
               else:
                   warning("VALIDATION: Max retries exceeded. Skipping this response.", category="combat_validation")
                   break
       
       # Clean up conversation history based on validation outcome
       if valid_response or ai_response:
           # Remove all validation attempts from conversation history
           conversation_history = conversation_history[:initial_conversation_length]
           
           # Add only the final assistant response
           if ai_response:
               conversation_history.append({"role": "assistant", "content": ai_response})
           
           # Log successful validation if it occurred
           if valid_response and validation_attempts:
               validation_attempts.append({
                   "attempt": "final",
                   "assistant_response": ai_response,
                   "validation_result": "success"
               })
       
       # Write validation attempts to log file
       if validation_attempts:
           validation_log_path = os.path.join(os.path.dirname(conversation_history_file), "combat_validation_log.json")
           try:
               # Load existing log or create new one (JSONL format)
               validation_log = []
               if os.path.exists(validation_log_path):
                   with open(validation_log_path, 'r') as f:
                       for line in f:
                           line = line.strip()
                           if line:
                               try:
                                   validation_log.append(json.loads(line))
                               except json.JSONDecodeError:
                                   continue
               
               # Add current validation session
               validation_log.append({
                   "timestamp": datetime.now().isoformat(),
                   "encounter_id": encounter_data.get("encounter_id", "unknown"),
                   "user_input": user_input_text,
                   "validation_attempts": validation_attempts,
                   "final_outcome": "success" if valid_response else "failed_after_retries"
               })
               
               # Write updated log
               with open(validation_log_path, 'w') as f:
                   json.dump(validation_log, f, indent=2)
                   
           except Exception as e:
               warning(f"FAILURE: Failed to write validation log", exception=e, category="file_operations")
       
       # Save the cleaned conversation history
       save_json_file(conversation_history_file, conversation_history)
       
       if not ai_response:
           error("FAILURE: Failed to get a valid AI response after multiple attempts", category="combat_events")
           continue
       
       # Process the validated response
       try:
           parsed_response = json.loads(ai_response)
           narration = parsed_response["narration"]
           actions = parsed_response["actions"]
           
           print(f"[COMBAT_MANAGER] Processing {len(actions)} combat actions")
           
           # Update status to show actions are being processed
           if len(actions) > 0:
               try:
                   from status_manager import status_manager
                   status_manager.update_status("Processing combat outcomes...", is_processing=True)
               except Exception as e:
                   debug(f"Could not update status: {e}", category="status")
           
           for i, action in enumerate(actions):
               action_type = action.get('action', action.get('type', 'unknown'))
               print(f"[COMBAT_MANAGER] Action {i+1}: {action_type}")
           
           # Extract and update combat round if provided
           if 'combat_round' in parsed_response:
               new_round = parsed_response['combat_round']
               current_round = encounter_data.get('current_round', 1)
               
               # Only update if round advances (never go backward)
               if isinstance(new_round, int) and new_round > current_round:
                   debug(f"STATE_CHANGE: Combat advancing from round {current_round} to round {new_round}", category="combat_events")
                   encounter_data['current_round'] = new_round
                   # Save the updated encounter data
                   save_json_file(f"modules/encounters/encounter_{encounter_id}.json", encounter_data)
               elif isinstance(new_round, int) and new_round < current_round:
                   warning(f"VALIDATION: Ignoring backward round progression from {current_round} to {new_round}", category="combat_events")
           
               
       except json.JSONDecodeError as e:
           debug(f"VALIDATION: JSON parsing error - {str(e)}", category="combat_events")
           debug("VALIDATION: Raw AI response:", category="combat_events")
           debug(ai_response, category="combat_events")
           continue
       
       # Check if this response includes an exit action BEFORE displaying narration
       has_exit_action = False
       for action in actions:
           if action.get("action", "").lower() == "exit":
               has_exit_action = True
               break
       
       # Only display narration if there's no exit action
       if not has_exit_action:
           print(f"Dungeon Master: {narration}")
           # Flush to ensure combat messages are captured by web interface
           import sys
           sys.stdout.flush()
       
       # Process actions
       for action in actions:
           action_type = action.get("action", "").lower()
           parameters = action.get("parameters", {})
           
           if action_type == "updateplayerinfo" or action_type == "updatecharacterinfo":
               # Handle both legacy and new action types
               if action_type == "updateplayerinfo":
                   character_name = normalize_character_name(player_info["name"])
               else:
                   character_name = normalize_character_name(parameters.get("characterName", player_info["name"]))
               
               changes = parameters.get("changes", "")
               print(f"[COMBAT_MANAGER] Updating character: {character_name}")
               try:
                   success = update_character_info(character_name, changes)
                   if success:
                       print(f"[COMBAT_MANAGER] Character update successful: {character_name}")
                       debug(f"SUCCESS: Character info updated successfully for {character_name}", category="character_updates")
                   else:
                       print(f"[COMBAT_MANAGER] Character update failed: {character_name}")
                       error(f"FAILURE: Failed to update character info for {character_name}", category="character_updates")
               except Exception as e:
                   print(f"[COMBAT_MANAGER] Exception during character update: {str(e)}")
                   error(f"FAILURE: Failed to update character info", exception=e, category="character_updates")
           
           elif action_type == "updatenpcinfo":
               # Legacy NPC update - redirect to unified system
               npc_name_for_update = path_manager.format_filename(parameters.get("npcName", ""))
               changes = parameters.get("changes", "")
               print(f"[COMBAT_MANAGER] Updating NPC: {npc_name_for_update}")
               
               # Debug logging for character update transaction
               debug_log = {
                   "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "action_type": action_type,
                   "raw_action": action,
                   "extracted_character_name": npc_name_for_update,
                   "extracted_changes": changes,
                   "original_parameters": parameters
               }
               
               try:
                   debug("STATE_CHANGE: Character update transaction starting...", category="npc_management")
                   debug(f"STATE_CHANGE: Character Name: {npc_name_for_update}", category="npc_management")
                   debug(f"STATE_CHANGE: Changes requested: {changes}", category="npc_management")
                   debug(f"STATE_CHANGE: Raw action object: {json.dumps(action, indent=2)}", category="npc_management")
                   
                   success = update_character_info(npc_name_for_update, changes)
                   
                   debug_log["update_result"] = "success" if success else "failed"
                   
                   if success:
                       print(f"[COMBAT_MANAGER] NPC update successful: {npc_name_for_update}")
                       debug(f"SUCCESS: Character {npc_name_for_update} info updated successfully", category="npc_management")
                   else:
                       print(f"[COMBAT_MANAGER] NPC update failed: {npc_name_for_update}")
                       warning(f"FAILURE: Update failed for NPC {npc_name_for_update}", category="npc_management")
               except Exception as e:
                   print(f"[COMBAT_MANAGER] Exception during NPC update: {str(e)}")
                   error(f"FAILURE: Failed to update NPC info", exception=e, category="npc_management")
                   debug_log["error"] = str(e)
               
               # Write debug log to file
               try:
                   with open("npc_update_debug_log.json", "a") as debug_file:
                       json.dump(debug_log, debug_file)
                       debug_file.write("\n")
               except Exception as log_error:
                   error(f"FAILURE: Failed to write debug log", exception=log_error, category="file_operations")
           
           elif action_type == "updateencounter":
               encounter_id_for_update = parameters.get("encounterId", encounter_id)
               changes = parameters.get("changes", "")
               print(f"[COMBAT_MANAGER] Updating encounter: {encounter_id_for_update}")
               try:
                   updated_encounter_data = update_encounter.update_encounter(encounter_id_for_update, changes)
                   if updated_encounter_data:
                       # Normalize status values to lowercase
                       updated_encounter_data = normalize_encounter_status(updated_encounter_data)
                       encounter_data = updated_encounter_data
                       print(f"[COMBAT_MANAGER] Encounter update successful")
                       debug(f"SUCCESS: Encounter {encounter_id_for_update} updated successfully", category="encounter_management")
               except Exception as e:
                   print(f"[COMBAT_MANAGER] Encounter update failed: {str(e)}")
                   error(f"FAILURE: Failed to update encounter", exception=e, category="encounter_management")
           
           elif action_type == "exit":
               print(f"[COMBAT_MANAGER] Combat ending - preparing summary")
               debug("STATE_CHANGE: Combat has ended, preparing summary...", category="combat_events")
               
               # Clear the preroll cache when combat ends
               if 'preroll_cache' in encounter_data:
                   del encounter_data['preroll_cache']
                   save_json_file(json_file_path, encounter_data)
                   debug("SUCCESS: Cleared preroll cache for ended combat", category="combat_events")
               
               # --- START OF THE FIX ---
               # This new line permanently removes defeated named enemies from the world.
               try:
                   process_defeated_creatures(encounter_data, party_tracker_data)
               except Exception as e:
                   error("FAILURE: An error occurred while processing defeated creatures.", exception=e, category="combat_resolution")
               # --- END OF THE FIX ---
               
               print(f"[COMBAT_MANAGER] Calculating XP rewards")
               xp_narrative, xp_awarded = calculate_xp()
               print(f"[COMBAT_MANAGER] XP awarded: {xp_awarded}")
               # Still record this information in the conversation history, but don't print it to console
               conversation_history.append({"role": "user", "content": f"XP Awarded: {xp_narrative}"})
               save_json_file(conversation_history_file, conversation_history)
               
               # COMMENTED OUT: Manual player XP update - now handled by general character update
               # This was causing double XP for players (getting total XP instead of per-participant)
               # xp_update_response = f"Update the character's experience points. XP Awarded: {xp_awarded}"
               # updated_data_tuple = update_json_schema(xp_update_response, player_info, encounter_data, party_tracker_data)
               # if updated_data_tuple:
               #     player_info, _, _ = updated_data_tuple
               
               # CRITICAL FIX: Clear the active combat encounter from party_tracker.json to prevent the loop.
               # This is the essential logic from the old update_json_schema function.
               if 'worldConditions' in party_tracker_data and 'activeCombatEncounter' in party_tracker_data['worldConditions']:
                   last_encounter_id = party_tracker_data["worldConditions"]["activeCombatEncounter"]
                   if last_encounter_id:
                       party_tracker_data["worldConditions"]["lastCompletedEncounter"] = last_encounter_id
                   party_tracker_data['worldConditions']['activeCombatEncounter'] = ""
                   debug(f"STATE_CHANGE: Cleared active combat encounter. Last completed encounter is now {last_encounter_id}", category="combat_events")
                   
                   # Save the updated party_tracker.json file
                   if not safe_write_json("party_tracker.json", party_tracker_data):
                       error("FILE_OP: Failed to save party_tracker.json after clearing active encounter", category="file_operations")
                   else:
                       info("SUCCESS: Party tracker updated, active combat encounter cleared.", category="combat_events")
               
               # Generate dialogue summary
               print(f"[COMBAT_MANAGER] Generating combat summary")
               dialogue_summary_result = summarize_dialogue(conversation_history, location_info, party_tracker_data)
               
               # Generate chat history for debugging
               print(f"[COMBAT_MANAGER] Saving combat history")
               generate_chat_history(conversation_history, encounter_id)
               
               print(f"[COMBAT_MANAGER] Combat complete - exiting simulation")
               info("STATE_CHANGE: Combat encounter closed. Exiting combat simulation.", category="combat_events")
               return dialogue_summary_result, player_info

       # Save updated conversation history after processing all actions
       save_json_file(conversation_history_file, conversation_history)

def main():
    debug("INITIALIZATION: Starting main function in combat_manager", category="combat_events")
    
    # Load party tracker
    try:
        party_tracker_data = safe_json_load("party_tracker.json")
        if not party_tracker_data:
            error("FAILURE: Failed to load party_tracker.json", category="file_operations")
            return
        debug(f"FILE_OP: Loaded party_tracker: {party_tracker_data}", category="file_operations")
    except Exception as e:
        error(f"FAILURE: Failed to load party tracker", exception=e, category="file_operations")
        return
    
    # Get active combat encounter
    active_combat_encounter = party_tracker_data["worldConditions"].get("activeCombatEncounter")
    debug(f"STATE_CHANGE: Active combat encounter: {active_combat_encounter}", category="combat_events")
    
    if not active_combat_encounter:
        info("STATE_CHANGE: No active combat encounter located.", category="combat_events")
        return
    
    # Get location data
    current_location_id = party_tracker_data["worldConditions"]["currentLocationId"]
    current_area_id = get_current_area_id()
    
    debug(f"STATE_CHANGE: Current location ID: {current_location_id}", category="encounter_setup")
    debug(f"STATE_CHANGE: Current area ID: {current_area_id}", category="combat_events")
    
    location_data = get_location_data(current_location_id)
    
    if not location_data:
        error(f"FAILURE: Failed to find location {current_location_id}", category="location_transitions")
        return
    
    # Run the combat simulation
    dialogue_summary, updated_player_info = run_combat_simulation(active_combat_encounter, party_tracker_data, location_data)
    
    info("SUCCESS: Combat simulation completed.", category="combat_events")
    info(f"SUMMARY: Dialogue Summary: {dialogue_summary}", category="combat_events")

if __name__ == "__main__":
    main()