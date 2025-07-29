# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
NeverEndingQuest Core Engine - Combat Manager
Copyright (c) 2024 MoonlightByte
Licensed under Fair Source License 1.0

This software is free for non-commercial and educational use.
Commercial competing use is prohibited for 2 years from release.
See LICENSE file for full terms.
"""

# ============================================================================
# COMBAT_MANAGER.PY - TURN-BASED COMBAT SYSTEM
# ============================================================================
#
# ARCHITECTURE ROLE: Game Systems Layer - Combat Management
#
# This module provides comprehensive turn-based combat management for the Mythic Bastionland
# system, implementing AI-driven combat encounters with Guard/Vigour mechanics and
# simultaneous combat with intelligent resource tracking.
#
# KEY RESPONSIBILITIES:
# - Turn-based combat orchestration with initiative order management
# - AI-powered combat decision making for NPCs and monsters
# - Combat state validation and rule compliance verification
# - Glory point calculation and reward distribution
# - Combat logging and debugging support with per-encounter directories
# - Real-time combat status display and resource tracking
# - Preroll dice caching system to prevent AI manipulation
#

"""
Combat Manager Module for NeverEndingQuest

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
# This module implements Mythic Bastionland combat mechanics using AI-driven simulation
# with strict rule validation. It demonstrates our multi-model AI strategy
# by using specialized models for combat-specific interactions.
# 
# KEY RESPONSIBILITIES:
# - Manage turn-based combat encounters with initiative tracking
# - Validate combat actions against Mythic Bastionland rules
# - Coordinate Guard/Vigour tracking, status effects, and combat state
# - Generate and manage pre-rolled dice to prevent AI confusion
# - Cache prerolls per combat round to ensure consistency
# - Track combat rounds through AI responses
# - Provide specialized combat AI prompts and validation
# - Real-time dynamic state display for combat awareness
# 
# COMBAT STATE DISPLAY PHILOSOPHY:
# - REAL-TIME AWARENESS: Shows current Guard, Vigour, conditions during combat
# - RESOURCE TRACKING: Displays Knight abilities and status for tactical decisions
# - DYNAMIC UPDATES: Reflects changes immediately as they occur
# - AI CLARITY: Provides authoritative current state to prevent confusion
# 
# COMBAT INFORMATION ARCHITECTURE:
# - DYNAMIC STATE DISPLAY: Current Guard, Vigour, active conditions
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
# - Real-time Guard and status tracking with state synchronization
# - Dynamic Virtue damage tracking for Knight resource management
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
# while maintaining strict Mythic Bastionland rule compliance through AI validation.
# ============================================================================

import json
import os
import time
import re
import random
import subprocess
from datetime import datetime
from utils.xp import main as calculate_xp
from openai import OpenAI
# Import model configurations from config.py
from config import (
    OPENAI_API_KEY,
    COMBAT_MAIN_MODEL,
    # Use the existing validation model instead of COMBAT_VALIDATION_MODEL
    DM_VALIDATION_MODEL, 
    COMBAT_DIALOGUE_SUMMARY_MODEL,
    DM_MINI_MODEL
)
from updates.update_character_info import update_character_info, normalize_character_name
import updates.update_encounter as update_encounter
import updates.update_party_tracker as update_party_tracker
# Import the preroll generator
from core.generators.generate_prerolls import generate_prerolls
# Import safe JSON functions
from utils.encoding_utils import safe_json_load
from utils.file_operations import safe_write_json
import core.ai.cumulative_summary as cumulative_summary
from utils.enhanced_logger import debug, info, warning, error, game_event, set_script_name

# Set script name for logging
set_script_name(__name__)

# Remove color constants - no longer used
# Color codes removed per CLAUDE.md guidelines

# Temperature
TEMPERATURE = 0.8

def get_combat_temperature(encounter_data, validation_attempt=0):
    """
    Calculate temperature for main combat processing based on encounter complexity.
    More creatures = lower temperature for better logical processing.
    Additional reduction applied for validation failures to improve consistency.
    
    Args:
        encounter_data: The encounter data containing creature information
        validation_attempt: The current validation attempt number (0 = first try)
    
    Returns:
        float: Temperature value between 0.1 and 0.8
    """
    creatures = encounter_data.get("creatures", [])
    creature_count = len(creatures)
    
    # Base temperature based on creature count
    if creature_count > 8:
        base_temp = 0.4
        complexity = "massive"
    elif creature_count > 6:
        base_temp = 0.5
        complexity = "very complex"
    elif creature_count > 4:
        base_temp = 0.6
        complexity = "complex"
    else:
        base_temp = 0.8
        complexity = "normal"
    
    # Apply reduction for validation failures
    # Each failure reduces temperature by 0.1, max reduction of 0.4
    temperature_reduction = min(validation_attempt * 0.1, 0.4)
    final_temp = max(base_temp - temperature_reduction, 0.1)  # Never go below 0.1
    
    # Round to 2 decimal places to avoid floating-point display issues
    final_temp = round(final_temp, 2)
    
    # Log the temperature selection
    if validation_attempt == 0:
        print(f"[COMBAT_MANAGER] Using temperature {final_temp} for {complexity} encounter ({creature_count} creatures)")
    else:
        print(f"[COMBAT_MANAGER] Lowering temperature from {base_temp:.1f} to {final_temp} after validation failure (attempt {validation_attempt + 1})")
    
    return final_temp

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

conversation_history_file = "modules/conversation_history/combat_conversation_history.json"
second_model_history_file = "modules/conversation_history/second_model_history.json"
third_model_history_file = "modules/conversation_history/third_model_history.json"

# Create a combat_logs directory if it doesn't exist
os.makedirs("combat_logs", exist_ok=True)

# Constants for chat history generation
HISTORY_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


def load_npc_with_fuzzy_match(npc_name, path_manager):
    """
    Load NPC data with fuzzy name matching support.
    First tries exact match, then falls back to fuzzy matching if needed.
    
    Args:
        npc_name: The NPC name to look for
        path_manager: ModulePathManager instance
        
    Returns:
        tuple: (npc_data, matched_filename) or (None, None) if not found
    """
    from utils.encoding_utils import safe_json_load
    
    # First try exact match with normalized name
    formatted_npc_name = path_manager.format_filename(npc_name)
    npc_file = path_manager.get_character_path(formatted_npc_name)
    npc_data = safe_json_load(npc_file)
    
    if npc_data:
        debug(f"NPC_LOAD: Exact match found for '{npc_name}' -> '{formatted_npc_name}'", category="combat_manager")
        return npc_data, formatted_npc_name
    
    # If exact match fails, try fuzzy matching
    debug(f"NPC_LOAD: Exact match failed for '{formatted_npc_name}', attempting fuzzy match", category="combat_manager")
    
    # Get all character files in the module
    import glob
    # Use the unified characters directory
    character_dir = "characters"
    character_files = glob.glob(os.path.join(character_dir, "*.json"))
    
    best_match = None
    best_score = 0
    best_filename = None
    
    for char_file in character_files:
        # Skip backup files
        if char_file.endswith(".bak") or char_file.endswith("_BU.json") or "backup" in char_file:
            continue
            
        # Load the character data to check if it's an NPC
        char_data = safe_json_load(char_file)
        # Check both character_type (correct field) and characterType (legacy) for compatibility
        char_type = char_data.get("character_type") or char_data.get("characterType")
        if char_data and char_type == "npc":
            char_name = char_data.get("name", "")
            # Simple fuzzy matching - check if key words from requested name are in character name
            requested_words = set(formatted_npc_name.lower().split("_"))
            char_words = set(char_name.lower().replace(" ", "_").split("_"))
            
            # Debug log for fuzzy matching
            debug(f"NPC_FUZZY: Comparing '{formatted_npc_name}' with '{char_name}' from {char_file}", category="combat_manager")
            debug(f"NPC_FUZZY: Requested words: {requested_words}, Character words: {char_words}", category="combat_manager")
            
            # Calculate match score based on word overlap
            common_words = requested_words.intersection(char_words)
            if common_words:
                score = len(common_words) / max(len(requested_words), len(char_words))
                
                if score > best_score:
                    best_score = score
                    best_match = char_data
                    # Extract just the filename without path for consistency
                    best_filename = os.path.splitext(os.path.basename(char_file))[0]
    
    # Use best match if score is high enough (threshold: 0.5)
    if best_match and best_score >= 0.5:
        info(f"NPC_FUZZY_MATCH: Success - '{npc_name}' matched to '{best_match['name']}' (score: {best_score:.2f})", category="combat_manager")
        return best_match, best_filename
    else:
        warning(f"NPC_FUZZY_MATCH: Failed for '{npc_name}' (best score: {best_score:.2f})", category="combat_manager")
        return None, None


def get_current_area_id():
    party_tracker = safe_json_load("party_tracker.json")
    if not party_tracker:
        error("FILE_OP: Failed to load party_tracker.json", category="file_operations")
        return None
    return party_tracker["worldConditions"]["currentAreaId"]

def get_location_data(location_id):
    from utils.module_path_manager import ModulePathManager
    from utils.encoding_utils import safe_json_load
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
    # Prompts are now in the prompts/ directory at project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(script_dir, '..', '..')
    file_path = os.path.join(project_root, 'prompts', filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except Exception as e:
        error(f"FILE_OP: Failed to read prompt file {filename}: {str(e)}", category="file_operations")
        return ""

def load_monster_stats(monster_name):
    # Import the path manager
    from utils.module_path_manager import ModulePathManager
    from utils.encoding_utils import safe_json_load
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
  - Example: updateCharacterInfo for "ExampleChar_Cleric" (player) or "Scout Kira" (NPC)
  
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
    
    # Log key validation context
    try:
        response_json = json.loads(response)
        combat_round = response_json.get("combat_round", "unknown")
        num_actions = len(response_json.get("actions", []))
        has_plan = "plan" in response_json
        debug(f"VALIDATION_CONTEXT: Round={combat_round}, Actions={num_actions}, HasPlan={has_plan}", category="combat_validation")
    except:
        debug("VALIDATION_CONTEXT: Unable to parse response JSON for context", category="combat_validation")
    
    # Load validation prompt from file
    validation_prompt = read_prompt_from_file('combat/mythic_combat_validation_prompt.txt')
    
    # Start with validation prompt
    validation_conversation = [
        {"role": "system", "content": validation_prompt}
    ]
    
    # Dynamic context based on encounter size
    num_creatures = len(encounter_data.get("creatures", []))
    if num_creatures > 6:
        # For large encounters (7+ participants), provide more context
        context_pairs = 20  # 40 messages = ~2.5 rounds for 8 participants
        debug(f"VALIDATION: Using extended context ({context_pairs} pairs) for large encounter with {num_creatures} creatures", category="combat_validation")
    else:
        # Standard encounters can use less context
        context_pairs = 12  # 24 messages = ~2 rounds for 4-6 participants
        debug(f"VALIDATION: Using standard context ({context_pairs} pairs) for encounter with {num_creatures} creatures", category="combat_validation")
    
    # Add previous user/assistant pairs for context
    if conversation_history and len(conversation_history) > (context_pairs * 2):
        # Get the messages based on context size
        # +1 to exclude current user input since we'll add it separately
        recent_messages = conversation_history[-(context_pairs * 2 + 1):-1]
        
        # Filter to only user/assistant messages (no system messages)
        context_messages = [
            msg for msg in recent_messages 
            if msg["role"] in ["user", "assistant"]
        ][-(context_pairs * 2):]  # Ensure we only get the right number of pairs
        
        # Add context header and messages
        validation_conversation.append({
            "role": "system", 
            "content": f"=== PREVIOUS COMBAT CONTEXT (last {context_pairs} exchanges) ==="
        })
        validation_conversation.extend(context_messages)
    
    # Add current validation data
    validation_conversation.extend([
        {"role": "system", "content": "=== CURRENT VALIDATION DATA ==="},
        {"role": "system", "content": f"Encounter Data:\n{json.dumps(encounter_data, indent=2)}"},
        {"role": "user", "content": f"Player Input: {user_input}"},
        {"role": "assistant", "content": response}
    ])

    max_validation_retries = 5
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
                
                # Extract feedback components and sanitize them for Windows console
                # CRITICAL: Must sanitize to prevent Unicode characters from crashing Windows console
                feedback_obj = validation_json.get("feedback", {})
                positive = sanitize_unicode_for_logging(feedback_obj.get("positive", "None."))
                negative = sanitize_unicode_for_logging(feedback_obj.get("negative", "No reason provided."))
                recommendation = sanitize_unicode_for_logging(feedback_obj.get("recommendation", "No recommendation provided."))

                # Log validation results with encounter context
                # Create debug/combat directory if it doesn't exist
                import os
                from datetime import datetime
                debug_combat_dir = os.path.join("debug", "combat")
                os.makedirs(debug_combat_dir, exist_ok=True)
                
                # Create timestamped filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Remove last 3 digits of microseconds
                encounter_id = encounter_data.get("encounterId", "unknown").replace("/", "_")
                validation_filename = f"validation_{timestamp}_{encounter_id}_attempt{attempt + 1}.json"
                validation_file_path = os.path.join(debug_combat_dir, validation_filename)
                
                with open(validation_file_path, "w") as log_file:
                    log_entry = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "encounter_size": num_creatures,
                        "context_pairs": context_pairs,
                        "attempt": attempt + 1,
                        "valid": is_valid,
                        "feedback": {
                            "positive": sanitize_unicode_for_logging(positive),
                            "negative": sanitize_unicode_for_logging(negative),
                            "recommendation": sanitize_unicode_for_logging(recommendation)
                        },
                        "response": sanitize_unicode_for_logging(response)
                    }
                    json.dump(log_entry, log_file)
                    log_file.write("\n")

                if is_valid:
                    print(f"[COMBAT_MANAGER] Validation PASSED")
                    # Optionally log the positive feedback
                    debug(f"VALIDATION: Passed. Positive feedback: {positive}", category="combat_validation")
                    return True
                else:
                    print(f"[COMBAT_MANAGER] Validation FAILED: {sanitize_unicode_for_logging(negative)}")
                    debug(f"VALIDATION: Failed. Negative feedback: {sanitize_unicode_for_logging(negative)}", category="combat_validation")
                    
                    # Extract specific validation rule that failed from the negative feedback
                    negative_lower = negative.lower()
                    if "round" in negative_lower and ("increment" in negative_lower or "advance" in negative_lower):
                        debug("VALIDATION_RULE: ROUND_TRACKING_ACCURACY violation detected", category="combat_validation")
                    elif "golden rule" in negative_lower or "mid-round" in negative_lower:
                        debug("VALIDATION_RULE: GOLDEN_RULE_VIOLATION detected", category="combat_validation")
                    elif "hp" in negative_lower or "hit point" in negative_lower or "damage" in negative_lower:
                        debug("VALIDATION_RULE: HP_TRACKING violation detected", category="combat_validation")
                    elif "death" in negative_lower or "dead" in negative_lower or "0 hp" in negative_lower:
                        debug("VALIDATION_RULE: DEATH_DETECTION violation detected", category="combat_validation")
                    elif "initiative" in negative_lower and "order" in negative_lower:
                        debug("VALIDATION_RULE: INITIATIVE_ORDER violation detected", category="combat_validation")
                    elif "player" in negative_lower and ("roll" in negative_lower or "dice" in negative_lower):
                        debug("VALIDATION_RULE: PLAYER_INTERACTION_FLOW violation detected", category="combat_validation")
                    elif "plan" in negative_lower:
                        debug("VALIDATION_RULE: PLAN_VALIDATION violation detected", category="combat_validation")
                    elif "json" in negative_lower or "format" in negative_lower:
                        debug("VALIDATION_RULE: JSON_STRUCTURE violation detected", category="combat_validation")
                    elif "updatecharacterinfo" in negative_lower or "updateencounter" in negative_lower:
                        debug("VALIDATION_RULE: ACTION_USAGE violation detected", category="combat_validation")
                    elif "ammunition" in negative_lower or "equipment" in negative_lower:
                        debug("VALIDATION_RULE: RESOURCE_USAGE violation detected", category="combat_validation")
                    else:
                        debug("VALIDATION_RULE: UNKNOWN - could not categorize validation failure", category="combat_validation")
                    
                    # Construct comprehensive feedback message for the AI
                    full_feedback = (
                        f"Your previous response was invalid. Here is a breakdown:\n\n"
                        f"## What You Did Correctly (Keep This):\n- {positive}\n\n"
                        f"## What You Did Incorrectly (You Must Fix This):\n- {negative}\n\n"
                        f"## Corrective Action Required:\n- {recommendation}"
                    )
                    
                    debug(f"VALIDATION: Full feedback for AI:\n{full_feedback}", category="combat_validation")
                    
                    # Return the full, structured feedback
                    return full_feedback
                    
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
    
    # Filter out dead creatures - they should not be in the initiative order
    active_creatures = [c for c in creatures if c.get("status", "unknown").lower() != "dead"]
    
    if not active_creatures:
        return "All creatures are dead"
    
    # Sort by initiative (descending), then alphabetically for ties
    sorted_creatures = sorted(active_creatures, key=lambda x: (-x.get("initiative", 0), x.get("name", "")))
    
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

        from utils.module_path_manager import ModulePathManager
        from utils.encoding_utils import safe_json_load
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
    fields_to_update = ['guard', 'virtues', 'equipment', 'knight_data', 'glory']

    for field in fields_to_update:
        if field in updated_data:
            if field in ['equipment', 'knight_data']:
                # For arrays, replace the entire array
                original_data[field] = updated_data[field]
            elif field == 'glory':
                # For Glory, only update if the new value is greater than the existing value
                if updated_data[field] > original_data.get(field, 0):
                    original_data[field] = updated_data[field]
            else:
                # For simple fields like guard, just update the value
                original_data[field] = updated_data[field]

    return original_data

# DEPRECATED: This function is no longer used and has been replaced by the new XP awarding system
# that uses update_character_info directly with proper synchronization.
# The new system:
# 1. Awards XP through update_character_info with "Awarded X experience points" message
# 2. Uses atomic file operations with proper locking
# 3. Has XP protection to prevent reduction
# 4. Includes comprehensive debug logging
# Keeping this function for reference only - DO NOT USE
def update_json_schema(ai_response, player_info, encounter_data, party_tracker_data):
    # This old function tried to extract XP from AI responses and update characters
    # It has been replaced by the more robust XP awarding system in the main combat loop
    warning("DEPRECATED: update_json_schema called but is no longer used", category="xp_tracking")
    return player_info  # Return unchanged data

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
    from utils.module_path_manager import ModulePathManager
    from utils.encoding_utils import safe_json_load
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
                try:
                    # Use fuzzy matching for NPC loading
                    npc_data, matched_filename = load_npc_with_fuzzy_match(creature['name'], path_manager)
                    if not npc_data:
                        error(f"FAILURE: Failed to load NPC file for: {creature['name']}", category="file_operations")
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
    """Create minimal encounter data for system prompt with only essential fields"""
    if not encounter_data or not isinstance(encounter_data, dict):
        return encounter_data
    
    # Create minimal structure with only essential fields
    minimal_data = {
        "encounterId": encounter_data.get("encounterId"),
        "encounterSummary": encounter_data.get("encounterSummary", ""),
        "creatures": []
    }
    
    # Process each creature to keep only essential fields
    for creature in encounter_data.get("creatures", []):
        minimal_creature = {
            "name": creature.get("name")
        }
        
        # Add type information
        if creature.get("type"):
            minimal_creature["type"] = creature["type"]
        
        # Add monster/npc specific type info
        if creature.get("monsterType"):
            minimal_creature["monsterType"] = creature["monsterType"]
        if creature.get("npcType"):
            minimal_creature["npcType"] = creature["npcType"]
        
        # Add armor class for all creatures (important for combat)
        if "armorClass" in creature:
            minimal_creature["armorClass"] = creature["armorClass"]
        
        # Add conditions (will be important when not empty)
        if "conditions" in creature and creature["conditions"]:
            minimal_creature["conditions"] = creature["conditions"]
        
        # Add actions (even though currently bugged and empty)
        if "actions" in creature:
            minimal_creature["actions"] = creature["actions"]
        
        minimal_data["creatures"].append(minimal_creature)
    
    debug("STATE_CHANGE: Created minimal encounter data for system prompt", category="combat_events")
    return minimal_data

def compress_old_combat_rounds(conversation_history, current_round, keep_recent_rounds=2):
    """
    Compress old combat rounds in conversation history to reduce token usage.
    Keeps the last 'keep_recent_rounds' rounds uncompressed for context.
    """
    try:
        # Debug logging
        debug(f"COMPRESSION: Called with current_round={current_round}, keep_recent_rounds={keep_recent_rounds}", category="combat_events")
        debug(f"COMPRESSION: Conversation history has {len(conversation_history)} messages", category="combat_events")
        
        # Don't compress if we're in early rounds
        if current_round <= keep_recent_rounds:
            debug(f"COMPRESSION: Skipping - too early (round {current_round} <= {keep_recent_rounds})", category="combat_events")
            return conversation_history
        
        # Check if compression is needed
        rounds_to_compress = []
        for round_num in range(1, current_round - keep_recent_rounds):
            # Check if this round is already compressed
            already_compressed = any(
                msg.get('role') == 'assistant' and 
                f"COMBAT ROUND {round_num} SUMMARY:" in msg.get('content', '')
                for msg in conversation_history
            )
            if not already_compressed:
                rounds_to_compress.append(round_num)
            else:
                debug(f"COMPRESSION: Round {round_num} already compressed", category="combat_events")
        
        if not rounds_to_compress:
            debug("COMPRESSION: No rounds need compression", category="combat_events")
            return conversation_history
        
        debug(f"COMPRESSION: Compressing rounds {rounds_to_compress}", category="combat_events")
        
        # Find round boundaries
        round_boundaries = {}
        current_tracking_round = None
        
        for i, msg in enumerate(conversation_history):
            content = msg.get('content', '')
            
            # Check for combat round markers in DM notes
            if msg.get('role') == 'user' and 'COMBAT ROUND' in content:
                match = re.search(r'COMBAT ROUND (\d+)', content)
                if match:
                    round_num = int(match.group(1))
                    if round_num in rounds_to_compress:
                        current_tracking_round = round_num
                        if round_num not in round_boundaries:
                            round_boundaries[round_num] = []
                        round_boundaries[round_num].append(i)
            
            # Check for combat_round field in AI responses
            elif msg.get('role') == 'assistant' and '"combat_round"' in content:
                try:
                    # Extract JSON from content
                    json_match = re.search(r'\{.*"combat_round"\s*:\s*(\d+).*\}', content, re.DOTALL)
                    if json_match:
                        round_num = int(json_match.group(1))
                        if round_num in rounds_to_compress:
                            current_tracking_round = round_num
                            if round_num not in round_boundaries:
                                round_boundaries[round_num] = []
                            round_boundaries[round_num].append(i)
                except:
                    pass
            
            # Continue tracking messages for current round
            elif current_tracking_round and current_tracking_round in round_boundaries:
                round_boundaries[current_tracking_round].append(i)
                
                # Stop tracking when we hit the next round
                next_round_match = re.search(r'COMBAT ROUND (\d+)', content)
                if next_round_match and int(next_round_match.group(1)) != current_tracking_round:
                    current_tracking_round = None
        
        # Compress each round
        new_conversation = []
        processed_indices = set()
        
        for i, msg in enumerate(conversation_history):
            if i in processed_indices:
                continue
            
            # Check if this starts a round to compress
            round_to_compress = None
            for round_num, indices in round_boundaries.items():
                if i == indices[0]:
                    round_to_compress = round_num
                    break
            
            if round_to_compress:
                # Extract messages for this round
                indices = round_boundaries[round_to_compress]
                round_messages = []
                for idx in indices:
                    if idx < len(conversation_history):
                        round_messages.append(conversation_history[idx])
                
                # Generate summary
                summary = generate_combat_round_summary(round_to_compress, round_messages)
                
                if summary:
                    # Add compressed round
                    new_conversation.append({
                        "role": "assistant",
                        "content": f"COMBAT ROUND {round_to_compress} SUMMARY:\n{json.dumps(summary, indent=2)}"
                    })
                    
                    # Add transition message
                    if round_to_compress < current_round - keep_recent_rounds:
                        new_conversation.append({
                            "role": "user",
                            "content": f"Round {round_to_compress} ends and Round {round_to_compress + 1} begins"
                        })
                    
                    processed_indices.update(indices)
                    info(f"COMPRESSION: Compressed round {round_to_compress}", category="combat_events")
                else:
                    # Keep original if compression fails
                    for idx in indices:
                        new_conversation.append(conversation_history[idx])
                        processed_indices.add(idx)
            else:
                # Keep message as-is
                new_conversation.append(msg)
                processed_indices.add(i)
        
        return new_conversation
        
    except Exception as e:
        error(f"COMPRESSION: Error compressing combat rounds", exception=e, category="combat_events")
        return conversation_history

def generate_combat_round_summary(round_num, round_messages):
    """Generate a structured summary of a combat round using AI"""
    try:
        # Extract content from messages
        round_content = "\n\n".join([
            f"[{msg.get('role', 'unknown')}]: {msg.get('content', '')}"
            for msg in round_messages
        ])
        
        prompt = f"""Convert this combat round into a structured JSON summary optimized for AI consumption.

Round {round_num} Combat Log:
{round_content}

Create a JSON summary with EXACTLY this structure:
{{
  "round": {round_num},
  "actions": [
    {{"actor": "name", "init": number, "action": "action_type", "target": "target_name", "roll": "dice+mod=total vs AC/DC", "result": "hit/miss/save/fail", "damage": "X type" or "heal": "X", "effects": "HP changes, conditions, etc"}}
  ],
  "deaths": ["list of creatures that died this round"],
  "status_changes": ["new conditions or effects applied"],
  "resource_usage": {{"character": "resources used (spell slots, abilities, etc)"}},
  "narrative_highlights": ["2-4 evocative single sentences capturing key dramatic moments, critical hits, deaths, powerful spells, or memorable character actions"],
  "round_end_state": {{
    "alive": ["Name (current/max HP)"],
    "dead": ["Name"],
    "conditions": {{"Name": ["conditions"]}}
  }}
}}

Focus on mechanical accuracy for the actions. For narrative_highlights, extract the most dramatic or memorable moments that happened this round - critical hits, character deaths, powerful spells, clutch saves, or impactful dialogue. Keep each highlight to one evocative sentence."""

        # Use the mini model for efficiency
        response = client.chat.completions.create(
            model=DM_MINI_MODEL,
            messages=[
                {"role": "system", "content": "You are a combat log analyzer. Extract mechanical game information and key narrative moments. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        summary = json.loads(response.choices[0].message.content)
        return summary
        
    except Exception as e:
        error(f"COMPRESSION: Failed to generate round {round_num} summary", exception=e, category="combat_events")
        return None

def run_combat_simulation(encounter_id, party_tracker_data, location_info):
   """Main function to run the combat simulation"""
   print(f"\n[COMBAT_MANAGER] ========== COMBAT SIMULATION START ==========")
   print(f"[COMBAT_MANAGER] Encounter ID: {encounter_id}")
   print(f"[COMBAT_MANAGER] Location: {location_info.get('name', 'Unknown')}")
   debug(f"INITIALIZATION: Starting combat simulation for encounter {encounter_id}", category="combat_events")
   
   # Initialize path manager
   from utils.module_path_manager import ModulePathManager
   from utils.encoding_utils import safe_json_load
   try:
       party_tracker = safe_json_load("party_tracker.json")
       current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
       path_manager = ModulePathManager(current_module)
   except:
       path_manager = ModulePathManager()

   # Check if combat history file exists and has content to determine if we are resuming.
   if os.path.exists(conversation_history_file) and os.path.getsize(conversation_history_file) > 100:
       conversation_history = load_json_file(conversation_history_file)
       is_resuming = True
       print("[COMBAT_MANAGER] Resuming existing combat session.")
   else:
       is_resuming = False
       conversation_history = [
           {"role": "system", "content": read_prompt_from_file('combat/mythic_combat_prompt.txt')},
           {"role": "system", "content": f"Current Combat Encounter: {encounter_id}"},
           {"role": "system", "content": ""}, # Player data placeholder
           {"role": "system", "content": ""}, # Monster templates placeholder
           {"role": "system", "content": ""}, # Location info placeholder
       ]
       print("[COMBAT_MANAGER] Starting new combat session.")
   
   # Initialize and reset secondary model histories
   second_model_history = []
   third_model_history = []
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
           # Use fuzzy matching for NPC loading
           npc_data, matched_filename = load_npc_with_fuzzy_match(creature["name"], path_manager)
           if npc_data and matched_filename:
               # Use the matched filename as the key to avoid duplicates
               if matched_filename not in npc_templates:
                   npc_templates[matched_filename] = npc_data
           else:
               error(f"FAILURE: Failed to load NPC file for: {creature['name']}", category="file_operations")
   
   # Populate the system messages ONLY if it's a new combat session
   if not is_resuming:
       conversation_history[2]["content"] = f"Player Character:\n{json.dumps(filter_dynamic_fields(player_info), indent=2)}"
       conversation_history[3]["content"] = f"Monster Templates:\n{json.dumps({k: filter_dynamic_fields(v) for k, v in monster_templates.items()}, indent=2)}"
       if not monster_templates and any(c["type"] == "enemy" for c in encounter_data["creatures"]):
           error("FAILURE: No monster templates were loaded!", category="file_operations")
           return None, None
       
       conversation_history[4]["content"] = f"Location:\n{json.dumps(location_info, indent=2)}"
       conversation_history.append({"role": "system", "content": f"NPC Templates:\n{json.dumps({k: filter_dynamic_fields(v) for k, v in npc_templates.items()}, indent=2)}"})
       conversation_history.append({"role": "system", "content": f"Encounter Details:\n{json.dumps(filter_encounter_for_system_prompt(encounter_data), indent=2)}"})
       
       log_conversation_structure(conversation_history)
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
               # For NPCs, look up their true max HP from their character file using fuzzy match
               npc_data, matched_filename = load_npc_with_fuzzy_match(creature_name, path_manager)
               if npc_data:
                   creature_max_hp = npc_data["maxHitPoints"]
               else:
                   error(f"FAILURE: Failed to get correct max HP for {creature_name}", category="combat_events")
                   creature_max_hp = creature.get("maxHitPoints", "Unknown")
           else:
               # For monsters, use the encounter data
               creature_max_hp = creature.get("maxHitPoints", "Unknown")
           
           dynamic_state_parts.append(f"\n{creature_name}:")
           dynamic_state_parts.append(f"  - HP: {creature_hp}/{creature_max_hp}")
           dynamic_state_parts.append(f"  - Status: {creature_status}")
           dynamic_state_parts.append(f"  - Condition: {creature_condition}")
   
   all_dynamic_state = "\n".join(dynamic_state_parts)
   
   # Initialize round tracking and generate prerolls
   # Use combat_round as primary, fall back to current_round
   round_num = encounter_data.get('combat_round', encounter_data.get('current_round', 1))
   preroll_text = generate_prerolls(encounter_data, round_num=round_num)
   
   encounter_data['preroll_cache'] = {
       'round': round_num,
       'rolls': preroll_text,
       'preroll_id': f"{round_num}-{random.randint(1000,9999)}"
   }
   save_json_file(json_file_path, encounter_data)
   debug(f"STATE_CHANGE: Saved prerolls for round {round_num}", category="combat_events")
   
   # --- START: RESUMPTION AND INITIAL SCENE LOGIC ---
   if is_resuming:
       # This is a resumed session. Inject a message to get a re-engagement narration.
       print("[COMBAT_MANAGER] Injecting 'player has returned' message to re-engage AI.")
       resume_prompt = "Dungeon Master Note: The game session is resuming after a pause. The player has returned. Please provide a brief narration to re-establish the scene and prompt the player for their next action, based on the last known state from the conversation history."
       
       # Add the resume prompt to the history only if it's not already the last message.
       if not conversation_history or conversation_history[-1].get('content') != resume_prompt:
           conversation_history.append({"role": "user", "content": resume_prompt})
           save_json_file(conversation_history_file, conversation_history)

       # Get the AI's re-engagement response
       try:
           print("[COMBAT_MANAGER] Getting re-engagement narration from AI...")
           # Use base temperature for re-engagement (no validation failures)
           temperature_used = get_combat_temperature(encounter_data, validation_attempt=0)
           
           response = client.chat.completions.create(
               model=COMBAT_MAIN_MODEL,
               temperature=temperature_used,
               messages=conversation_history
           )
           resume_response_content = response.choices[0].message.content.strip()
           
           conversation_history.append({"role": "assistant", "content": resume_response_content})
           save_json_file(conversation_history_file, conversation_history)

           parsed_response = json.loads(resume_response_content)
           narration = parsed_response.get("narration", "The battle continues! What do you do?")
           print(f"Dungeon Master: {narration}")

       except Exception as e:
           error("FAILURE: Could not get re-engagement narration.", exception=e, category="combat_events")
           print("Dungeon Master: The battle continues! What will you do next?")
   else:
       # This is a new combat. Use the original logic to get the initial scene.
       debug("AI_CALL: Getting initial scene description...", category="combat_events")
       initiative_order = get_initiative_order(encounter_data)
       
       initial_prompt_text = f"""The setup scene for the combat has already been given and described to the party. Now, describe the combat situation and the enemies the party faces."""

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

Player: {initial_prompt_text}"""

       conversation_history.append({"role": "user", "content": initial_prompt})
       save_json_file(conversation_history_file, conversation_history)

       max_retries = 3
       initial_response = None
       initial_conversation_length = len(conversation_history)
       
       for attempt in range(max_retries):
           try:
               # Calculate temperature with attempt number for dynamic adjustment
               temperature_used = get_combat_temperature(encounter_data, validation_attempt=attempt)
               
               response = client.chat.completions.create(
                   model=COMBAT_MAIN_MODEL, 
                   temperature=temperature_used, 
                   messages=conversation_history
               )
               initial_response = response.choices[0].message.content.strip()
               conversation_history.append({"role": "assistant", "content": initial_response})
               
               if not is_valid_json(initial_response):
                   if attempt < max_retries - 1:
                       conversation_history.append({"role": "user", "content": "Invalid JSON format. Please try again."})
                       continue
                   else: break

               # FIX: Use the correct variable for the user input parameter
               validation_result = validate_combat_response(initial_response, encounter_data, initial_prompt_text, conversation_history)
               
               if validation_result is True:
                   break
               else:
                   if attempt < max_retries - 1:
                       # validation_result is now the full feedback string
                       conversation_history.append({"role": "user", "content": validation_result})
                       continue
                   else: break
           except Exception as e:
               error(f"FAILURE: AI call for initial scene failed on attempt {attempt + 1}", exception=e, category="combat_events")
               if attempt >= max_retries - 1: break
       
       # FIX: Simplified cleanup logic
       conversation_history = conversation_history[:initial_conversation_length]
       if initial_response:
           conversation_history.append({"role": "assistant", "content": initial_response})
           save_json_file(conversation_history_file, conversation_history)
           try:
               parsed_response = json.loads(initial_response)
               print(f"Dungeon Master: {parsed_response['narration']}")
           except (json.JSONDecodeError, KeyError):
               print(f"Dungeon Master: {initial_response}") # Print raw if parsing fails
       else:
           error("FAILURE: Could not get a valid initial scene from AI.", category="combat_events")
           return None, None # Exit if we can't start combat
   # --- END: RESUMPTION AND INITIAL SCENE LOGIC ---
   
   # Combat loop
   debug("[COMBAT_MANAGER] Entering main combat loop", category="combat_events")
   
   # Update status to show combat is active
   try:
       from core.managers.status_manager import status_manager
       status_manager.update_status("Combat in progress - awaiting your action", is_processing=False)
   except Exception as e:
       debug(f"Could not update status: {e}", category="status")
   while True:
       # Ensure all character data is synced to the encounter
       debug("[COMBAT_MANAGER] Syncing character data to encounter", category="combat_events")
       
       # Clear processing status when ready for player input
       try:
           from core.managers.status_manager import status_manager
           status_manager.update_status("", is_processing=False)
       except Exception as e:
           debug(f"Could not clear status: {e}", category="status")
       sync_active_encounter()
       
       # REFRESH CONVERSATION HISTORY WITH LATEST DATA
       debug("STATE_CHANGE: Refreshing conversation history with latest character data...", category="combat_events")
       
       # Reload player info FOR CONVERSATION HISTORY ONLY - use same pattern as NPCs
       # This prevents XP reset bug by not overwriting the in-memory player_info object
       player_name = normalize_character_name(player_info["name"])
       player_file = path_manager.get_character_path(player_name)
       try:
           # Load fresh data for conversation history without overwriting player_info
           fresh_player_data = safe_json_load(player_file)
           if not fresh_player_data:
               error(f"FAILURE: Failed to load player file: {player_file}", category="file_operations")
           else:
               # Update conversation history with fresh data (same pattern as NPCs)
               conversation_history[2]["content"] = f"Player Character:\n{json.dumps(filter_dynamic_fields(fresh_player_data), indent=2)}"
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
               # Use fuzzy matching for NPC reloading
               npc_data, matched_filename = load_npc_with_fuzzy_match(creature["name"], path_manager)
               if npc_data and matched_filename:
                   # Update the NPC in the templates dictionary
                   npc_templates[matched_filename] = npc_data
               else:
                   error(f"FAILURE: Failed to reload NPC file for: {creature['name']}", category="file_operations")
       
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
                   # For NPCs, look up their true max HP from their character file using fuzzy match
                   npc_data, matched_filename = load_npc_with_fuzzy_match(creature_name, path_manager)
                   if npc_data:
                       creature_max_hp = npc_data["maxHitPoints"]
                   else:
                       error(f"FAILURE: Failed to get correct max HP for {creature_name}", category="combat_events")
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
       # Use combat_round as primary, fall back to current_round
       current_round = encounter_data.get('combat_round', encounter_data.get('current_round', 1))
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
       # Try to use AI-powered live initiative tracker
       live_tracker = None
       try:
           from .initiative_tracker_ai import generate_live_initiative_tracker
           # Get recent conversation for analysis (last 20 messages)
           recent_conversation = conversation_history[-20:] if len(conversation_history) > 20 else conversation_history
           live_tracker = generate_live_initiative_tracker(encounter_data, recent_conversation, current_round)
           if live_tracker:
               debug("AI_TRACKER: Successfully generated live initiative tracker", category="combat_events")
       except Exception as e:
           debug(f"AI_TRACKER: Failed to generate live tracker: {e}", category="combat_events")
       
       # Use AI tracker if available, otherwise fall back to simple format
       if live_tracker:
           initiative_display = live_tracker
       else:
           debug("AI_TRACKER: Using fallback initiative order", category="combat_events")
           initiative_order = get_initiative_order(encounter_data)
           initiative_display = f"Initiative Order: {initiative_order}"
       
       # Create a focused, streamlined per-turn prompt
       # Most rules are in the system prompt. This prompt focuses on DYNAMIC state.
       user_input_with_note = f"""--- CURRENT COMBAT STATE ---
Round: {current_round}
{initiative_display}
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

Player: {user_input_text}

Now, continue the combat flow by narrating and resolving all remaining monster and NPC turns for the current round in initiative order until you get to my turn or, if I'm done this turn, then narrate the rest of this round.

Your response narratively MUST stop at one of two points:
1.  When you have resolved the turn for the LAST creature in the current round's initiative order.
2.  When the initiative order returns to my turn again.

Do not narrate or process any actions from the next round in this response. The goal is to complete the current round of actions and then pause. If you do need to stop, please engage me creatively so I don't get bored."""
       
       # Clean old DM notes before adding new user input
       conversation_history = clean_old_dm_notes(conversation_history)
       
       # Add user input to conversation history
       conversation_history.append({"role": "user", "content": user_input_with_note})
       save_json_file(conversation_history_file, conversation_history)
       
       # Get AI response with validation and retries
       max_retries = 5
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
                   from core.managers.status_manager import status_manager
                   status_manager.update_status("Combat AI processing your action...", is_processing=True)
               except Exception as e:
                   debug(f"Could not update status: {e}", category="status")
               
               # Calculate temperature with attempt number for dynamic adjustment
               temperature_used = get_combat_temperature(encounter_data, validation_attempt=attempt)
               
               response = client.chat.completions.create(
                   model=COMBAT_MAIN_MODEL,
                   temperature=temperature_used,
                   messages=conversation_history
               )
               ai_response = response.choices[0].message.content.strip()
               
               print(f"[COMBAT_MANAGER] AI response received ({len(ai_response)} chars)")
               
               
               # Write raw response to debug file
               os.makedirs("debug", exist_ok=True)
               with open("debug/debug_ai_response.json", "w") as debug_file:
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
                           "error_type": "json_format",
                           "temperature_used": temperature_used
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
                           "error_type": "multiple_update_encounter",
                           "temperature_used": temperature_used
                       })
                       continue
                   else:
                       warning("VALIDATION: Max retries exceeded for multiple updateEncounter correction. Using last response.", category="combat_validation")
               
               # Validate the combat logic
               print(f"[COMBAT_MANAGER] Validating combat response (Attempt {attempt + 1}/{max_retries})")
               
               # Update status to show validation is happening
               try:
                   from core.managers.status_manager import status_manager
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
                   
                   # The validation result is now the full feedback string
                   feedback = validation_result
                   
                   # Log the specific validation failure for debugging
                   debug(f"VALIDATION_ATTEMPT: {attempt + 1} failed", category="combat_validation")
                   
                   if attempt < max_retries - 1:
                       # Add error feedback temporarily for next attempt
                       conversation_history.append({
                           "role": "user",
                           "content": feedback
                       })
                       # Log this validation attempt
                       validation_attempts.append({
                           "attempt": attempt + 1,
                           "assistant_response": ai_response,
                           "validation_error": feedback,
                           "error_type": "combat_logic",
                           "temperature_used": temperature_used
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
                   "validation_result": "success",
                   "temperature_used": temperature_used
               })
       
       # Write validation attempts to log file
       if validation_attempts:
           # Create debug/combat directory if it doesn't exist
           debug_combat_dir = os.path.join("debug", "combat")
           os.makedirs(debug_combat_dir, exist_ok=True)
           
           # Create timestamped filename
           from datetime import datetime
           timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Remove last 3 digits of microseconds
           encounter_id = encounter_data.get("encounterId", "unknown").replace("/", "_")
           validation_count = len(validation_attempts)
           validation_filename = f"validation_session_{timestamp}_{encounter_id}_attempts{validation_count}.json"
           validation_log_path = os.path.join(debug_combat_dir, validation_filename)
           try:
               # Create new validation log for this session
               validation_log = []
               
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
               warning(f"FAILURE: Failed to write validation log", category="file_operations")
       
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
                   from core.managers.status_manager import status_manager
                   status_manager.update_status("Processing combat outcomes...", is_processing=True)
               except Exception as e:
                   debug(f"Could not update status: {e}", category="status")
           
           for i, action in enumerate(actions):
               action_type = action.get('action', action.get('type', 'unknown'))
               print(f"[COMBAT_MANAGER] Action {i+1}: {action_type}")
           
           # Extract and update combat round if provided
           if 'combat_round' in parsed_response:
               new_round = parsed_response['combat_round']
               # Use combat_round from encounter data, not current_round
               current_combat_round = encounter_data.get('combat_round', encounter_data.get('current_round', 1))
               
               debug(f"ROUND_TRACKING: parsed_response has combat_round={new_round}, encounter has combat_round={current_combat_round}", category="combat_events")
               
               # Only update if round advances (never go backward)
               if isinstance(new_round, int) and new_round > current_combat_round:
                   debug(f"STATE_CHANGE: Combat advancing from round {current_combat_round} to round {new_round}", category="combat_events")
                   encounter_data['combat_round'] = new_round
                   # Also update current_round for backwards compatibility
                   encounter_data['current_round'] = new_round
                   # Save the updated encounter data
                   save_json_file(f"modules/encounters/encounter_{encounter_id}.json", encounter_data)
                   
                   # Compress old combat rounds if we're at round 3 or higher
                   if new_round >= 3:
                       debug(f"COMPRESSION: Checking for round compression (current round: {new_round})", category="combat_events")
                       debug(f"COMPRESSION: About to call compress_old_combat_rounds with round {new_round}", category="combat_events")
                       compressed_history = compress_old_combat_rounds(
                           conversation_history, 
                           new_round, 
                           keep_recent_rounds=2
                       )
                       
                       # Save compressed history
                       if len(compressed_history) < len(conversation_history):
                           debug(f"COMPRESSION: History compressed from {len(conversation_history)} to {len(compressed_history)} messages", category="combat_events")
                           conversation_history = compressed_history
                           save_json_file(conversation_history_file, conversation_history)
                           info(f"COMPRESSION: Combat history compressed and saved", category="combat_events")
                       else:
                           debug(f"COMPRESSION: No compression occurred (still {len(conversation_history)} messages)", category="combat_events")
                           
               elif isinstance(new_round, int) and new_round < current_round:
                   warning(f"VALIDATION: Ignoring backward round progression from {current_round} to {new_round}", category="combat_events")
           
               
       except json.JSONDecodeError as e:
           debug(f"VALIDATION: JSON parsing error - {str(e)}", category="combat_events")
           debug("VALIDATION: Raw AI response:", category="combat_events")
           debug(ai_response, category="combat_events")
           continue
       
       # --- ACTION PROCESSING: CONSOLIDATE AND EXECUTE ---
       # This new block prevents race conditions by consolidating all character
       # updates into a single, authoritative save at the end of combat.

       # A dictionary to hold all change descriptions for each character.
       # e.g., {'eirik_hearthwise': ['used a crossbow bolt', 'took 5 damage'], ...}
       final_character_updates = {}

       # Check if combat is ending in this turn.
       is_combat_ending = any(a.get("action", "").lower() == "exit" for a in actions)

       # Display narration immediately, as it describes the events of the turn.
       print(f"Dungeon Master: {narration}")
       import sys
       sys.stdout.flush()

       # STEP 1: GATHER all intended changes from the AI's actions.
       for action in actions:
           action_type = action.get("action", "").lower()
           parameters = action.get("parameters", {})

           if action_type in ["updateplayerinfo", "updatecharacterinfo", "updatenpcinfo"]:
               char_name_key = "characterName" if "characterName" in parameters else "npcName"
               character_name = parameters.get(char_name_key)
               changes = parameters.get("changes")

               if character_name and changes:
                   if character_name not in final_character_updates:
                       final_character_updates[character_name] = []
                   final_character_updates[character_name].append(changes)
                   info(f"CONSOLIDATING: Queued change for {character_name}: '{changes}'", category="combat_events")

           elif action_type == "updateencounter":
               # Encounter updates are separate and can be processed immediately.
               encounter_id_for_update = parameters.get("encounterId", encounter_id)
               changes = parameters.get("changes", "")
               info(f"STATE_UPDATE: Processing immediate encounter update: {changes}", category="encounter_management")
               try:
                   updated_encounter_data = update_encounter.update_encounter(encounter_id_for_update, changes)
                   if updated_encounter_data:
                       encounter_data = normalize_encounter_status(updated_encounter_data)
               except Exception as e:
                   error(f"FAILURE: Failed to update encounter", exception=e, category="encounter_management")
           
           elif action_type == "exit" and is_combat_ending:
               # If combat is ending, add the authoritative HP and XP to our dictionary.
               info("CONSOLIDATING: 'exit' action detected. Calculating final HP and XP.", category="combat_events")
               xp_narrative, xp_awarded = calculate_xp()
               info(f"XP_AWARD: Calculated {xp_awarded} XP per participant.", category="xp_tracking")
               conversation_history.append({"role": "user", "content": f"XP Awarded: {xp_narrative}"})
               save_json_file(conversation_history_file, conversation_history)

               for creature in encounter_data.get("creatures", []):
                   if creature.get("type") in ["player", "npc"]:
                       character_name = creature.get("name")
                       if character_name:
                           if character_name not in final_character_updates:
                               final_character_updates[character_name] = []
                           
                           final_hp = creature.get("currentHitPoints")
                           final_character_updates[character_name].append(f"set hitPoints to {final_hp}")
                           
                           if xp_awarded > 0:
                               final_character_updates[character_name].append(f"awarded {xp_awarded} experience points")

       # STEP 2: EXECUTE the consolidated updates. This is the only place character files are saved.
       if final_character_updates:
           info("STATE_UPDATE: Applying all consolidated updates.", category="character_updates")
           for character_name, changes_list in final_character_updates.items():
               # Join all changes into one comprehensive request string.
               final_change_string = "Following the turn's events: " + ", and ".join(changes_list) + "."
               info(f"FINAL_CHANGE_STRING for {character_name}: {final_change_string}", category="character_updates")

               try:
                   update_success = update_character_info(character_name, final_change_string)
                   if not update_success:
                       error(f"FAILURE: Final consolidated update failed for {character_name}.", category="character_updates")
               except Exception as e:
                   error(f"FAILURE: Critical error during consolidated update for {character_name}", exception=e, category="character_updates")

       # STEP 3: If combat ended, perform final cleanup and exit the simulation.
       if is_combat_ending:
           if 'worldConditions' in party_tracker_data and 'activeCombatEncounter' in party_tracker_data['worldConditions']:
               last_encounter_id = party_tracker_data["worldConditions"]["activeCombatEncounter"]
               if last_encounter_id:
                   party_tracker_data["worldConditions"]["lastCompletedEncounter"] = last_encounter_id
               party_tracker_data['worldConditions']['activeCombatEncounter'] = ""
               debug(f"STATE_CHANGE: Cleared active combat encounter. Last completed is now {last_encounter_id}", category="combat_events")
               safe_write_json("party_tracker.json", party_tracker_data)

           info("AI_CALL: Generating final combat summary...", category="ai_operations")
           dialogue_summary_result = summarize_dialogue(conversation_history, location_info, party_tracker_data)
           
           info("FILE_OP: Saving final combat chat history log...", category="combat_logs")
           generate_chat_history(conversation_history, encounter_id)
           
           # Reload the player_info object from disk one last time before returning it.
           # This ensures the main loop receives the fully updated state.
           player_info = safe_json_load(player_file)

           info("SUCCESS: Combat complete. Exiting simulation.", category="combat_events")
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
    except Exception as e:
        error(f"FAILURE: Failed to load party tracker", exception=e, category="file_operations")
        return
    
    # Get active combat encounter
    active_combat_encounter = party_tracker_data["worldConditions"].get("activeCombatEncounter")
    
    if not active_combat_encounter:
        info("STATE_CHANGE: No active combat encounter located.", category="combat_events")
        return
    
    # Get location data to pass to the simulation
    current_location_id = party_tracker_data["worldConditions"]["currentLocationId"]
    location_data = get_location_data(current_location_id)
    
    if not location_data:
        error(f"FAILURE: Failed to find location {current_location_id}", category="location_transitions")
        return
    
    # Run the combat simulation, passing the loaded location_data
    dialogue_summary, updated_player_info = run_combat_simulation(active_combat_encounter, party_tracker_data, location_data)
    
    info("SUCCESS: Combat simulation completed.", category="combat_events")
    if dialogue_summary:
        info(f"SUMMARY: Dialogue Summary: {dialogue_summary}", category="combat_events")

if __name__ == "__main__":
    main()