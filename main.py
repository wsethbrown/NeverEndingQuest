# ============================================================================
# MAIN.PY - GAME LOOP CONTROLLER
# ============================================================================
# 
# ARCHITECTURE ROLE: Primary Controller in MVC Pattern
# 
# This is the central orchestrator of the 5th edition Dungeon Master system, implementing
# the main game loop and coordinating all subsystems. It follows the Command Pattern
# where every game interaction is processed as a discrete action.
# 
# KEY RESPONSIBILITIES:
# - Game session management and main loop execution
# - Action parsing and routing to appropriate handlers
# - AI response validation and state synchronization
# - Conversation history management and context compression
# - Real-time user feedback and status reporting
# - DM Note generation for authoritative current game state
# 
# DM NOTE DESIGN PHILOSOPHY:
# - AUTHORITATIVE SOURCE: DM Note contains current, dynamic game state
# - REAL-TIME DATA: Always reflects most up-to-date character information
# - AI CLARITY: Single source of truth prevents conflicting information
# - DYNAMIC FOCUS: HP, spell slots, conditions, and active effects
# 
# DM NOTE CONTENT STRATEGY:
# Generated content includes:
#   - Current party status (HP, level, XP, spell slots)
#   - Active location and environmental conditions
#   - Time, date, and world state information
#   - Dynamic character states (not static reference data)
# 
# INFORMATION ARCHITECTURE:
# - DM NOTES: Current state, real-time data, authoritative information
# - SYSTEM MESSAGES: Static character reference (conversation_utils.py)
# - SEPARATION PRINCIPLE: Prevents AI confusion from version conflicts
# 
# ARCHITECTURAL INTEGRATION:
# - Coordinates with dm_wrapper.py for AI interactions
# - Uses action_handler.py for command processing
# - Manages state through party_tracker.json updates
# - Validates responses using multiple AI models
# - Integrates with ModulePathManager for file operations
# - Provides dynamic data to conversation_utils.py for context management
# 
# DATA FLOW:
# User Input -> Action Processing -> AI Response -> Validation -> State Update -> DM Note Refresh
# 
# This file embodies our "AI-First Design with Human Safety Nets" principle
# by combining powerful AI capabilities with rigorous validation layers and
# clear information architecture that prevents AI confusion.
# ============================================================================

import json
import subprocess
import os
import re
import sys
import codecs
from openai import OpenAI
from datetime import datetime, timedelta
from termcolor import colored

# Import encoding utilities
from encoding_utils import (
    sanitize_text,
    sanitize_dict,
    safe_json_load,
    safe_json_dump,
    fix_corrupted_location_name,
    setup_utf8_console
)

# Import other necessary modules
from combat_manager import run_combat_simulation
from plot_update import update_plot
from player_stats import get_player_stat
from update_world_time import update_world_time
from conversation_utils import update_conversation_history, update_character_data
from update_character_info import update_character_info

# Import new manager modules
import location_manager
from location_path_finder import LocationGraph
import action_handler
import cumulative_summary
from status_manager import (
    status_manager, status_ready, status_processing_ai, status_validating,
    status_retrying, status_transitioning_location, status_generating_summary,
    status_updating_journal, status_compressing_history, status_updating_character,
    status_updating_party, status_updating_plot, status_advancing_time, status_saving
)

# Import atomic file operations
from file_operations import safe_write_json, safe_read_json
from module_path_manager import ModulePathManager
from campaign_manager import CampaignManager

# Import training data collection
from simple_training_collector import log_complete_interaction

# Import model configurations from config.py
from config import (
    OPENAI_API_KEY,
    DM_MAIN_MODEL,
    DM_SUMMARIZATION_MODEL,
    DM_VALIDATION_MODEL
)

client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize location graph for path validation
location_graph = LocationGraph()
location_graph.load_module_data()

# Temperature Configuration (remains the same)
TEMPERATURE = 0.8

SOLID_GREEN = "\033[38;2;0;180;0m"  # Slightly darker solid green for player name
LIGHT_OFF_GREEN = "\033[38;2;100;180;100m"  # More muted light green for stats
GOLD = "\033[38;2;255;215;0m"  # Gold color for status messages
RESET_COLOR = "\033[0m"

json_file = "conversation_history.json"

needs_conversation_history_update = False

# Status display configuration
current_status_line = None

def display_status(message):
    """Display status message above the command prompt"""
    global current_status_line
    # Clear previous status line if exists
    if current_status_line is not None:
        print(f"\r{' ' * len(current_status_line)}\r", end='', flush=True)
    # Display new status
    status_display = f"{GOLD}[{message}]{RESET_COLOR}"
    print(f"\r{status_display}", flush=True)
    current_status_line = status_display

# Set up status callback
def status_callback(message, is_processing):
    """Callback for status manager to display status updates"""
    if is_processing:
        display_status(message)
    else:
        # Clear status when ready
        global current_status_line
        if current_status_line is not None:
            print(f"\r{' ' * len(current_status_line)}\r", end='', flush=True)
            current_status_line = None

# Register the callback
status_manager.set_callback(status_callback)

# Note: Old summarization functions removed - using cumulative summary system instead

# Add this new function near the top of the file
def exit_game():
    print("Fond farewell until we meet again!")
    exit()

def get_npc_stat(npc_name, stat_name, time_estimate):
    print(f"DEBUG: get_npc_stat called for {npc_name}, stat: {stat_name}")
    # Load party tracker to get correct module
    party_data = load_json_file("party_tracker.json")
    module_name = party_data.get("module", "").replace(" ", "_")
    path_manager = ModulePathManager(module_name)
    npc_file = path_manager.get_character_path(npc_name)
    try:
        with open(npc_file, "r", encoding="utf-8") as file:
            npc_stats = json.load(file)
    except FileNotFoundError:
        print(f"{npc_file} not found. Stat retrieval failed.")
        return "NPC stat not found"
    except json.JSONDecodeError:
        print(f"{npc_file} has an invalid JSON format. Stat retrieval failed.")
        return "NPC stat not found"

    stat_value = None
    modifier_value = None

    if npc_stats:
        if stat_name.lower() in npc_stats["abilities"]:
            stat_value = npc_stats["abilities"][stat_name.lower()]
            modifier_value = (stat_value - 10) // 2

    if stat_value is not None and modifier_value is not None:
        # Update the world time based on the time estimate (in minutes)
        update_world_time(time_estimate)

        return f"NPC's {stat_name.capitalize()}: {stat_value} (Modifier: {modifier_value})"
    else:
        return "NPC stat not found"

def parse_json_safely(text):
    # First, try to parse as-is
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract from code block
    json_content = extract_json_from_codeblock(text)
    try:
        return json.loads(json_content)
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

def create_module_validation_context(party_tracker_data, path_manager):
    """Create module data context for validation system to check location/NPC references"""
    try:
        current_area_id = party_tracker_data["worldConditions"]["currentAreaId"]
        current_module = party_tracker_data.get("module", "Unknown")
        
        validation_context = f"MODULE VALIDATION DATA:\nCurrent Module: {current_module}\nCurrent Area: {current_area_id}\n\n"
        
        # Get all valid locations in current area
        area_file = path_manager.get_area_path(current_area_id)
        try:
            with open(area_file, "r", encoding="utf-8") as file:
                area_data = json.load(file)
            
            valid_locations = []
            for location in area_data.get("locations", []):
                loc_id = location.get("locationId", "")
                loc_name = location.get("name", "")
                if loc_id and loc_name:
                    valid_locations.append(f"{loc_id} ({loc_name})")
            
            validation_context += f"VALID LOCATIONS in {current_area_id}:\n"
            if valid_locations:
                validation_context += "\n".join([f"- {loc}" for loc in valid_locations])
            else:
                validation_context += "- No locations found"
            validation_context += "\n\n"
                
        except (FileNotFoundError, json.JSONDecodeError):
            validation_context += f"ERROR: Could not load area data for {current_area_id}\n\n"
        
        # Get all valid NPCs in current module
        import os
        import glob
        character_files = glob.glob(f"{path_manager.module_dir}/characters/*.json")
        
        valid_npcs = []
        for char_file in character_files:
            try:
                with open(char_file, "r", encoding="utf-8") as file:
                    char_data = json.load(file)
                char_name = char_data.get("name", "")
                char_type = char_data.get("character_type", "unknown")
                if char_name:
                    valid_npcs.append(f"{char_name} ({char_type})")
            except (json.JSONDecodeError, KeyError):
                continue
        
        validation_context += "VALID CHARACTERS in module:\n"
        if valid_npcs:
            validation_context += "\n".join([f"- {npc}" for npc in valid_npcs])
        else:
            validation_context += "- No character files found"
        
        validation_context += "\n\nVALIDATION RULE: AI responses MUST ONLY reference locations and NPCs from the above lists. Any reference to non-existent locations or NPCs should be flagged as invalid."
        
        return validation_context
        
    except Exception as e:
        return f"MODULE VALIDATION DATA: Error loading module data - {str(e)}"

def validate_ai_response(primary_response, user_input, validation_prompt_text, conversation_history, party_tracker_data):
    status_validating()
    # Get the last two messages from the conversation history
    last_two_messages = conversation_history[-2:]

    # Ensure we have at least two messages
    while len(last_two_messages) < 2:
        last_two_messages.insert(0, {"role": "assistant", "content": "Previous context not available."})

    # Get location data from party tracker
    current_location_id = party_tracker_data["worldConditions"]["currentLocationId"]
    current_area_id = party_tracker_data["worldConditions"]["currentAreaId"]

    # Load the area data with correct module
    module_name = party_tracker_data.get("module", "").replace(" ", "_")
    path_manager = ModulePathManager(module_name)
    area_file = path_manager.get_area_path(current_area_id)
    try:
        with open(area_file, "r", encoding="utf-8") as file:
            area_data = json.load(file)
        location_data = next((loc for loc in area_data["locations"] if loc["locationId"] == current_location_id), None)
    except (FileNotFoundError, json.JSONDecodeError):
        location_data = None

    # Create the location details message
    if location_data:
        location_details = f"Location Details: {location_data['description']} {location_data.get('dmInstructions', '')}"
    else:
        location_details = "Location Details: Not available."
    
    # Check for transitionLocation action and add path validation
    if '"action": "transitionLocation"' in primary_response:
        try:
            # Extract the destination from the AI response
            destination_match = re.search(r'"newLocation":\s*"([^"]*)"', primary_response)
            if destination_match:
                destination = destination_match.group(1).strip()
                current_origin = current_location_id
                
                # Validate we have required data
                if not destination:
                    path_info = f"Path Validation ERROR: Empty destination in transitionLocation action."
                elif not current_origin:
                    path_info = f"Path Validation ERROR: Current location ID not available in party tracker."
                elif not location_graph:
                    path_info = f"Path Validation ERROR: Location graph not initialized."
                else:
                    # Validate path using location graph
                    success, path, message = location_graph.find_path(current_origin, destination)
                    
                    if success:
                        path_info = f"The party is currently at {current_origin} and desires to travel to {destination}. The path of travel is: {' -> '.join(path)}."
                    else:
                        path_info = f"The party is currently at {current_origin} and desires to travel to {destination}. WARNING: {message}"
                
                # Add path validation to location details
                location_details += f"\n\nPath Validation: {path_info}"
            else:
                # transitionLocation detected but no newLocation parameter found
                location_details += f"\n\nPath Validation ERROR: transitionLocation action detected but destination could not be extracted."
                
        except Exception as e:
            # Catch any unexpected errors in path validation
            location_details += f"\n\nPath Validation ERROR: Failed to validate path - {str(e)}"

    # Create user input context for validation
    user_input_context = f"VALIDATION CONTEXT: The user input that triggered this assistant response was: '{user_input}'"
    
    # Create module data context for location/NPC validation
    module_data_context = create_module_validation_context(party_tracker_data, path_manager)
    
    validation_conversation = [
        {"role": "system", "content": validation_prompt_text},
        {"role": "system", "content": location_details},
        {"role": "system", "content": user_input_context},
        {"role": "system", "content": module_data_context},
        last_two_messages[0],
        last_two_messages[1],
        {"role": "assistant", "content": primary_response}
    ]
    
    # DEBUG: Log what validation AI sees for createNewModule actions
    if '"action": "createNewModule"' in primary_response:
        print("DEBUG: *** VALIDATION DEBUG - createNewModule detected ***")
        print(f"DEBUG: User input that triggered this: {user_input}")
        print(f"DEBUG: Last two messages validation AI sees:")
        for i, msg in enumerate(last_two_messages):
            print(f"DEBUG: Message {i+1}: {msg['role']}: {msg['content'][:100]}...")
        print("DEBUG: *** END VALIDATION DEBUG ***")

    max_validation_retries = 3
    for attempt in range(max_validation_retries):
        validation_result = client.chat.completions.create(
            model=DM_VALIDATION_MODEL, # Use imported model name
            temperature=TEMPERATURE,
            messages=validation_conversation
        )

        validation_response = validation_result.choices[0].message.content.strip()

        try:
            validation_json = parse_json_safely(validation_response)
            is_valid = validation_json.get("valid", False)
            reason = validation_json.get("reason", "No reason provided")

            # Log only failed validations to prompt_validation.json
            if not is_valid:
                log_entry = {
                    "prompt": validation_conversation,
                    "response": validation_response,
                    "reason": reason
                }

                with open("prompt_validation.json", "a", encoding="utf-8") as log_file:
                    json.dump(log_entry, log_file)
                    log_file.write("\n")  # Add a newline for better readability

                return reason  # Return the failure reason
            else:
                print("DEBUG: Validation passed successfully")
                return True  # Return True for successful validation

        except json.JSONDecodeError:
            print(f"DEBUG: Invalid JSON from validation model (Attempt {attempt + 1}/{max_validation_retries})")
            print(f"Problematic response: {validation_response}")
            continue  # Retry the validation

    # If we've exhausted all retries and still don't have a valid JSON response
    print("DEBUG: Validation model consistently produced invalid JSON. Assuming primary response is valid.")
    return True

def load_validation_prompt():
    with open("validation_prompt.txt", "r", encoding="utf-8") as file:
        return file.read().strip()

def load_json_file(file_path):
    """Load a JSON file, with error handling and encoding sanitization"""
    return safe_json_load(file_path)

def process_conversation_history(history):
    print(f"DEBUG: Processing conversation history")
    for message in history:
        if message["role"] == "user" and message["content"].startswith("Leveling Dungeon Master Guidance"):
            message["content"] = "DM Guidance: Proceed with leveling up the player character or the party NPC given the 5th Edition role playing game rules. Only level the player character or party NPC one level at a time to ensure no mistakes are made. If you are leveling up a party NPC then pass all changes at once using the 'updateCharacterInfo' action. If you are leveling up a player character then you must ask the player for important decisions and choices they would have control over. After the player has provided the needed information then use the 'updateCharacterInfo' to pass all changes to the players character sheet and include the experience goal for the next level. Do not update the player's information in segements."
    
    # Apply DM note truncation to clean up bloated messages
    history = truncate_dm_notes(history)
    
    print(f"DEBUG: Conversation history processing complete")
    return history

def truncate_dm_notes(conversation_history):
    for message in conversation_history:
        if message["role"] == "user" and message["content"].startswith("Dungeon Master Note:"):
            parts = message["content"].split("Player:", 1)
            if len(parts) == 2:
                date_time = re.search(r"Current date and time: ([^.]+)", parts[0])
                if date_time:
                    message["content"] = f"Dungeon Master Note: {date_time.group(0)}. Player:{parts[1]}"
    return conversation_history

def check_and_process_location_transitions(conversation_history, party_tracker_data, path_manager):
    """
    Check if there are any unprocessed location transitions in the conversation history
    and process them to create summaries and compress the history.
    """
    # Find the most recent transition that hasn't been processed yet
    last_transition_index = None
    last_transition_content = None
    
    for i in range(len(conversation_history) - 1, -1, -1):
        msg = conversation_history[i]
        if msg.get("role") == "user" and "Location transition:" in msg.get("content", ""):
            last_transition_index = i
            last_transition_content = msg.get("content", "")
            break
    
    if last_transition_index is None:
        # No transitions found
        return conversation_history
    
    # Check if this transition has already been processed (has a summary right before it)
    if last_transition_index > 0:
        prev_msg = conversation_history[last_transition_index - 1]
        if prev_msg.get("role") == "assistant" and "=== LOCATION SUMMARY ===" in prev_msg.get("content", ""):
            # This transition has already been processed
            return conversation_history
    
    # Check if there's already a summary after this transition
    # If there are regular conversation messages after the transition, we should process it
    has_conversation_after = False
    for i in range(last_transition_index + 1, len(conversation_history)):
        msg = conversation_history[i]
        # Skip system messages and DM notes
        if msg.get("role") == "assistant" or (msg.get("role") == "user" and "Dungeon Master Note:" not in msg.get("content", "")):
            has_conversation_after = True
            break
    
    if not has_conversation_after:
        # No conversation after the transition yet, wait for next round
        return conversation_history
    
    # Extract the leaving location from the transition message
    # New format: "Location transition: [from_location] (ID) to [to_location] (ID)"
    # Old format: "Location transition: [from_location] to [to_location]"
    try:
        import re
        # Try to extract with IDs first (new format)
        id_pattern = r'Location transition: (.+?) \(([A-Z]\d+)\) to (.+?) \(([A-Z]\d+)\)'
        id_match = re.match(id_pattern, last_transition_content)
        
        if id_match:
            # New format with IDs
            leaving_location_name = id_match.group(1)
            leaving_location_id = id_match.group(2)
            print(f"DEBUG: Extracted from new format - Location: {leaving_location_name}, ID: {leaving_location_id}")
        else:
            # Fall back to old format
            parts = last_transition_content.split(" to ")
            if len(parts) == 2:
                from_part = parts[0].replace("Location transition: ", "").strip()
                leaving_location_name = from_part
                leaving_location_id = None
                print(f"DEBUG: Extracted from old format - Location: {leaving_location_name}")
            else:
                print("DEBUG: Could not parse transition message format")
                return conversation_history
    except Exception as e:
        print(f"DEBUG: Error parsing transition message: {str(e)}")
        return conversation_history
    
    print(f"DEBUG: Processing transition from {leaving_location_name}")
    
    try:
        # Generate enhanced adventure summary
        adventure_summary = cumulative_summary.generate_enhanced_adventure_summary(
            conversation_history,
            party_tracker_data,
            leaving_location_name
        )
        
        if adventure_summary:
            # Update journal with the summary
            cumulative_summary.update_journal_with_summary(
                adventure_summary,
                party_tracker_data,
                leaving_location_name
            )
            
            # Compress conversation history
            compressed_history = cumulative_summary.compress_conversation_history_on_transition(
                conversation_history,
                leaving_location_name
            )
            
            # Check if chunked compression is needed after creating the location summary
            try:
                from chunked_compression_integration import check_and_perform_chunked_compression
                if check_and_perform_chunked_compression():
                    print("DEBUG: Chunked compression performed after location transition")
                    # Reload the compressed history
                    compressed_history = load_json_file(json_file) or compressed_history
            except Exception as e:
                print(f"DEBUG: Chunked compression check failed: {e}")
            
            print("DEBUG: Location summary and compression completed")
            return compressed_history
        else:
            print("DEBUG: No adventure summary generated")
            return conversation_history
            
    except Exception as e:
        print(f"ERROR: Failed to process location transition: {str(e)}")
        import traceback
        traceback.print_exc()
        return conversation_history

def extract_json_from_codeblock(text):
    match = re.search(r'```json\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def process_ai_response(response, party_tracker_data, location_data, conversation_history):
    global needs_conversation_history_update
    
    try:
        json_content = extract_json_from_codeblock(response)
        parsed_response = json.loads(json_content)

        narration = parsed_response.get("narration", "")
        # Sanitize narration to handle problematic Unicode characters
        sanitized_narration = sanitize_text(narration)
        print(colored("Dungeon Master:", "blue"), colored(sanitized_narration, "blue"))

        conversation_history.append({"role": "assistant", "content": response})

        actions = parsed_response.get("actions", [])
        actions_processed = False
        for action in actions:
            # Call action_handler to process each action
            result = action_handler.process_action(action, party_tracker_data, location_data, conversation_history)
            actions_processed = True
            
            # Handle new dictionary return format
            if isinstance(result, dict):
                if result.get("status") == "exit":
                    return "exit"
                if result.get("needs_update"):
                    needs_conversation_history_update = True
                if result.get("status") == "needs_response":
                    # Get a new AI response
                    new_response = get_ai_response(conversation_history)
                    process_ai_response(new_response, party_tracker_data, location_data, conversation_history)
            # Backward compatibility for old return types (can be removed later)
            elif result == "exit":
                return "exit"
            elif isinstance(result, bool) and result:
                needs_conversation_history_update = True

        # Reload party tracker data if any actions were processed
        if actions_processed:
            party_tracker_data = load_json_file("party_tracker.json")

        save_conversation_history(conversation_history)

        return {"role": "assistant", "content": response}
    except json.JSONDecodeError as e:
        print(f"Error: Unable to parse AI response as JSON: {e}")
        print(f"Problematic response: {response}")
        conversation_history.append({"role": "assistant", "content": response}) # Still save if narration was printed
        # Sanitize response before printing in case of JSON parsing errors
        sanitized_response = sanitize_text(response)
        print(colored("Dungeon Master:", "blue"), colored(sanitized_response, "blue")) # Print raw response if JSON fails but it was a narration
        save_conversation_history(conversation_history)
        return {"role": "assistant", "content": response} # Return raw if parsing fails

def save_conversation_history(history):
    try:
        safe_json_dump(history, json_file)
    except Exception as e:
        print(colored(f"ERROR: Failed to save conversation history: {e}", "red"))

def get_ai_response(conversation_history):
    status_processing_ai()
    response = client.chat.completions.create(
        model=DM_MAIN_MODEL, # Use imported model name
        temperature=TEMPERATURE,
        messages=conversation_history
    )
    content = response.choices[0].message.content.strip()
    
    # Use the encoding utility to sanitize the AI response
    content = sanitize_text(content)
    
    # Log training data - complete conversation history and AI response
    try:
        log_complete_interaction(conversation_history, content)
    except Exception as e:
        print(f"Warning: Could not log training data: {e}")
    
    return content

def ensure_main_system_prompt(conversation_history, main_system_prompt_text):
    """
    Ensure the main system prompt is first in the conversation history.
    This removes any existing instances of the main prompt and adds it at the beginning.
    """
    # Remove all existing system prompts that appear to be the main system prompt
    # We'll identify the main system prompt by checking if it starts with the first few words
    # of the actual system prompt content
    main_prompt_start = main_system_prompt_text[:50]  # First 50 characters as identifier
    
    # Filter out any system message that starts with our identifier
    filtered_history = []
    for msg in conversation_history:
        if msg["role"] == "system" and msg["content"].startswith(main_prompt_start):
            continue  # Skip this message as it's likely our main system prompt
        filtered_history.append(msg)
    
    # Always place the main system prompt at the beginning
    return [{"role": "system", "content": main_system_prompt_text}] + filtered_history

def order_conversation_messages(conversation_history, main_system_prompt_text):
    """Order conversation messages with main system prompt first, followed by other system prompts"""
    main_prompt = None
    other_system_prompts = []
    non_system_messages = []

    for msg in conversation_history:
        if msg["role"] == "system":
            if msg["content"].startswith(main_system_prompt_text[:50]):
                main_prompt = msg
            else:
                other_system_prompts.append(msg)
        else:
            non_system_messages.append(msg)

    # Reconstruct with proper order
    ordered_history = []
    if main_prompt:
        ordered_history.append(main_prompt)
    ordered_history.extend(other_system_prompts)
    ordered_history.extend(non_system_messages)
    
    return ordered_history

def check_all_modules_plot_completion():
    """
    Check plot completion status for ALL available modules, not just the current one.
    Returns a dictionary with completion data for all modules.
    """
    import os
    import glob
    
    print("DEBUG: Starting comprehensive module plot completion check")
    
    modules_dir = "modules"
    all_modules_data = {
        "modules_checked": [],
        "all_complete": True,
        "completion_summary": {}
    }
    
    if not os.path.exists(modules_dir):
        print("DEBUG: No modules directory found")
        return all_modules_data
    
    # Find all valid module directories
    available_modules = []
    for item in os.listdir(modules_dir):
        module_path = os.path.join(modules_dir, item)
        if os.path.isdir(module_path) and not item.startswith('.') and item not in ['campaign_archives', 'campaign_summaries']:
            # Check if this directory has area JSON files (indicating it's a valid module)
            area_files = []
            
            # Check root directory (legacy structure)
            try:
                root_area_files = [f for f in os.listdir(module_path) 
                                 if os.path.isfile(os.path.join(module_path, f)) 
                                 and f.endswith('.json') 
                                 and len(f.split('.')[0]) <= 7  # Area codes like HH001, G001, SR001
                                 and not f.startswith('map_') 
                                 and not f.startswith('plot_')
                                 and not f.startswith('party_')
                                 and not f.startswith('module_')
                                 and f not in ['campaign.json', 'world_registry.json', 'module_context.json']]
                area_files.extend(root_area_files)
            except Exception as e:
                print(f"DEBUG: Error checking root area files for {item}: {e}")
            
            # Check areas/ subdirectory (new structure)
            areas_subdir = os.path.join(module_path, 'areas')
            if os.path.exists(areas_subdir) and os.path.isdir(areas_subdir):
                try:
                    subdir_area_files = [f for f in os.listdir(areas_subdir) 
                                       if os.path.isfile(os.path.join(areas_subdir, f)) 
                                       and f.endswith('.json') 
                                       and len(f.split('.')[0]) <= 7  # Area codes
                                       and not f.startswith('map_') 
                                       and not f.startswith('plot_')
                                       and not f.startswith('party_')
                                       and not f.startswith('module_')]
                    area_files.extend(subdir_area_files)
                except Exception as e:
                    print(f"DEBUG: Error checking areas subdirectory for {item}: {e}")
            
            if area_files:
                available_modules.append(item)
                print(f"DEBUG: Found valid module: {item} (has {len(area_files)} area files)")
    
    print(f"DEBUG: Found {len(available_modules)} valid modules: {available_modules}")
    
    # Check plot completion for each module
    for module_name in available_modules:
        module_path_manager = ModulePathManager(module_name)
        plot_file_path = module_path_manager.get_plot_path()
        
        print(f"DEBUG: Checking plot completion for module '{module_name}'")
        print(f"DEBUG: Plot file path: {plot_file_path}")
        
        try:
            plot_data = load_json_file(plot_file_path)
            
            if plot_data and "plotPoints" in plot_data:
                total_plots = len(plot_data["plotPoints"])
                completed_plots = 0
                
                for plot_point in plot_data["plotPoints"]:
                    status = plot_point.get("status", "unknown")
                    plot_id = plot_point.get("id", "unknown")
                    print(f"DEBUG: Module {module_name} - Plot point {plot_id}: status = '{status}'")
                    
                    if status == "completed":
                        completed_plots += 1
                
                module_complete = completed_plots == total_plots and total_plots > 0
                
                all_modules_data["completion_summary"][module_name] = {
                    "total_plots": total_plots,
                    "completed_plots": completed_plots,
                    "is_complete": module_complete,
                    "plot_file_exists": True
                }
                
                if not module_complete:
                    all_modules_data["all_complete"] = False
                
                print(f"DEBUG: Module {module_name} completion: {completed_plots}/{total_plots} ({module_complete})")
                
            else:
                print(f"DEBUG: Module {module_name} has no plot data or plotPoints")
                all_modules_data["completion_summary"][module_name] = {
                    "total_plots": 0,
                    "completed_plots": 0,
                    "is_complete": False,
                    "plot_file_exists": False
                }
                all_modules_data["all_complete"] = False
                
        except Exception as e:
            print(f"DEBUG: Error loading plot data for module {module_name}: {e}")
            all_modules_data["completion_summary"][module_name] = {
                "total_plots": 0,
                "completed_plots": 0,
                "is_complete": False,
                "plot_file_exists": False,
                "error": str(e)
            }
            all_modules_data["all_complete"] = False
    
    all_modules_data["modules_checked"] = available_modules
    
    print(f"DEBUG: All modules plot completion check complete")
    print(f"DEBUG: Total modules checked: {len(available_modules)}")
    print(f"DEBUG: All modules complete: {all_modules_data['all_complete']}")
    
    return all_modules_data

def main_game_loop():
    global needs_conversation_history_update

    validation_prompt_text = load_validation_prompt() 

    with open("system_prompt.txt", "r", encoding="utf-8") as file:
        main_system_prompt_text = file.read() 

    conversation_history = load_json_file(json_file) or []
    party_tracker_data = load_json_file("party_tracker.json")
    
    # Extract module name from party tracker data first
    module_name = party_tracker_data.get("module", "").replace(" ", "_")
    print(f"DEBUG: Initializing path_manager with module: '{module_name}'")
    
    # Initialize path manager with the correct module name
    path_manager = ModulePathManager(module_name)
    print(f"DEBUG: Path manager initialized - module_name: '{path_manager.module_name}', module_dir: '{path_manager.module_dir}'")
    
    current_area_id = party_tracker_data["worldConditions"]["currentAreaId"]
    location_data = location_manager.get_location_info( 
        party_tracker_data["worldConditions"]["currentLocation"],
        party_tracker_data["worldConditions"]["currentArea"],
        current_area_id
    )

    # Use current module from party tracker for plot data  
    current_module_name = party_tracker_data.get("module", "").replace(" ", "_")
    current_path_manager = ModulePathManager(current_module_name)
    plot_data = load_json_file(current_path_manager.get_plot_path())
    print(f"DEBUG: Plot file path: {current_path_manager.get_plot_path()}")
    
    module_data = load_json_file(current_path_manager.get_module_file_path())

    conversation_history = ensure_main_system_prompt(conversation_history, main_system_prompt_text)
    conversation_history = update_conversation_history(conversation_history, party_tracker_data, plot_data, module_data)
    conversation_history = update_character_data(conversation_history, party_tracker_data)
    
    # Use the new order_conversation_messages function
    conversation_history = order_conversation_messages(conversation_history, main_system_prompt_text)
    
    # Check for missing summaries at game startup
    print("DEBUG: Checking for missing location summaries at startup")
    conversation_history = cumulative_summary.check_and_compact_missing_summaries(
        conversation_history,
        party_tracker_data
    )
    
    save_conversation_history(conversation_history)

    initial_ai_response = get_ai_response(conversation_history)
    # Ensure location_data passed here is the one loaded for the initial state
    process_ai_response(initial_ai_response, party_tracker_data, location_data, conversation_history) 

    # Add safeguard against infinite loops in non-interactive environments
    empty_input_count = 0
    max_empty_inputs = 5
    
    while True:
        conversation_history = truncate_dm_notes(conversation_history)

        if needs_conversation_history_update:
            # Reload conversation history from disk to get any changes made during actions
            conversation_history = load_json_file("conversation_history.json") or []
            conversation_history = process_conversation_history(conversation_history)
            save_conversation_history(conversation_history)
            needs_conversation_history_update = False

        # Check for and process any location transitions
        conversation_history = check_and_process_location_transitions(conversation_history, party_tracker_data, path_manager)
        save_conversation_history(conversation_history)

        # Set status to ready before accepting input
        status_ready()

        # Check if stdin is available (prevent infinite loops in non-interactive environments)
        if not sys.stdin.isatty():
            print("WARNING: Running in non-interactive environment. Stdin is not a terminal.")
            print("Game loop stopped to prevent infinite empty input cycle.")
            print("To run interactively, ensure the program is run from a proper terminal.")
            break

        player_name_actual = party_tracker_data["partyMembers"][0]
        player_data_file = path_manager.get_character_path(player_name_actual)
        player_data_current = load_json_file(player_data_file)

        if player_data_current:
            current_hp = player_data_current.get("hitPoints", "N/A")
            max_hp = player_data_current.get("maxHitPoints", "N/A")
            current_xp = player_data_current.get("experience_points", "N/A")
            next_level_xp = player_data_current.get("exp_required_for_next_level", "N/A")
            current_time_str = party_tracker_data["worldConditions"]["time"]
            stats_display = f"{LIGHT_OFF_GREEN}[{current_time_str}][HP:{current_hp}/{max_hp}][XP:{current_xp}/{next_level_xp}]{RESET_COLOR}"
            player_name_display = f"{SOLID_GREEN}{player_name_actual}{RESET_COLOR}"
            user_input_text = input(f"{stats_display} {player_name_display}: ")
        else:
            user_input_text = input("User: ")

        # Skip processing if input is empty or only whitespace, but track consecutive empty inputs
        if not user_input_text or not user_input_text.strip():
            empty_input_count += 1
            if empty_input_count >= max_empty_inputs:
                print("WARNING: Detected multiple consecutive empty inputs. This may indicate a non-interactive environment.")
                print("Stopping game loop to prevent infinite cycle.")
                break
            continue
        else:
            # Reset counter on valid input
            empty_input_count = 0

        party_tracker_data = load_json_file("party_tracker.json") 

        party_members_stats = []
        for member_name_iter in party_tracker_data["partyMembers"]:
            member_file_path = path_manager.get_character_path(member_name_iter)
            member_data_iter = load_json_file(member_file_path)
            if member_data_iter:
                stats = {
                    "name": member_name_iter,  # Keep original case to match file names
                    "display_name": member_name_iter.capitalize(),  # For display purposes
                    "level": member_data_iter.get("level", "N/A"),
                    "xp": member_data_iter.get("experience_points", "N/A"),
                    "hp": member_data_iter.get("hitPoints", "N/A"),
                    "max_hp": member_data_iter.get("maxHitPoints", "N/A")
                }
                party_members_stats.append(stats)

        try:
            for npc_info_iter in party_tracker_data["partyNPCs"]:
                print(f"DEBUG: Processing NPC: {npc_info_iter['name']}")
                npc_name_iter = npc_info_iter["name"]
                npc_data_file = path_manager.get_character_path(npc_name_iter)
                print(f"DEBUG: NPC file path: {npc_data_file}")
                npc_data_iter = load_json_file(npc_data_file)
                print(f"DEBUG: NPC data loaded: {npc_data_iter is not None}")
                if npc_data_iter:
                    stats = {
                        "name": npc_info_iter["name"],
                        "display_name": npc_info_iter["name"].capitalize(),  # For display purposes
                        "level": npc_data_iter.get("level", npc_info_iter.get("level", "N/A")),
                        "xp": npc_data_iter.get("experience_points", "N/A"),
                        "hp": npc_data_iter.get("hitPoints", "N/A"),
                        "max_hp": npc_data_iter.get("maxHitPoints", "N/A")
                    }
                    party_members_stats.append(stats)
                    print(f"DEBUG: Added NPC stats: {stats}")
        except Exception as e:
            print(f"DEBUG: Error processing NPCs: {e}")
            import traceback
            traceback.print_exc()
        
        # Reload current location_data for the DM note based on party_tracker
        # This ensures location_data is fresh for each DM note construction
        current_area_id = party_tracker_data["worldConditions"]["currentAreaId"] 
        location_data = location_manager.get_location_info( 
            party_tracker_data["worldConditions"]["currentLocation"],
            party_tracker_data["worldConditions"]["currentArea"],
            current_area_id
        )

        if party_members_stats:
            world_conditions = party_tracker_data["worldConditions"]
            date_time_str = f"{world_conditions['year']} {world_conditions['month']} {world_conditions['day']} {world_conditions['time']}"
            party_stats_formatted = []
            for stats_item in party_members_stats:
                # Check if this is a player or an NPC
                if stats_item['name'] in party_tracker_data["partyMembers"]:
                    member_data_for_note = load_json_file(path_manager.get_character_path(stats_item['name']))
                else:
                    member_data_for_note = load_json_file(path_manager.get_character_path(stats_item['name']))
                if member_data_for_note:
                    abilities = member_data_for_note.get("abilities", {})
                    ability_str = f"STR:{abilities.get('strength', 'N/A')} DEX:{abilities.get('dexterity', 'N/A')} CON:{abilities.get('constitution', 'N/A')} INT:{abilities.get('intelligence', 'N/A')} WIS:{abilities.get('wisdom', 'N/A')} CHA:{abilities.get('charisma', 'N/A')}"
                    next_level_xp_note = member_data_for_note.get("exp_required_for_next_level", "N/A")
                    display_name = stats_item.get('display_name', stats_item['name'].capitalize())
                    
                    # Extract spell slot information if character has spellcasting
                    spell_slots_str = ""
                    spellcasting = member_data_for_note.get("spellcasting", {})
                    if spellcasting and "spellSlots" in spellcasting:
                        spell_slots = spellcasting["spellSlots"]
                        slot_parts = []
                        for level in range(1, 10):  # Spell levels 1-9
                            level_key = f"level{level}"
                            if level_key in spell_slots:
                                slot_data = spell_slots[level_key]
                                current = slot_data.get("current", 0)
                                maximum = slot_data.get("max", 0)
                                if maximum > 0:  # Only show levels with available slots
                                    slot_parts.append(f"L{level}:{current}/{maximum}")
                        if slot_parts:
                            spell_slots_str = f", Spell Slots: {' '.join(slot_parts)}"
                    
                    party_stats_formatted.append(f"{display_name}: Level {stats_item['level']}, XP {stats_item['xp']}/{next_level_xp_note}, HP {stats_item['hp']}/{stats_item['max_hp']}, {ability_str}{spell_slots_str}")

            party_stats_str = "; ".join(party_stats_formatted)
            current_location_name_note = world_conditions["currentLocation"]
            current_location_id_note = world_conditions["currentLocationId"]
            
            # --- CONNECTIVITY SECTION ---
            connected_locations_display_str = "None listed"
            connected_areas_display_str = "" # Initialize as empty

            if location_data: # Ensure location_data is not None
                # Get connections within the current area
                if "connectivity" in location_data and location_data["connectivity"]:
                    connected_ids_current_area = location_data["connectivity"]
                    connected_names_current_area = []
                    # Load the current area's full data to get names from IDs
                    current_area_full_data = load_json_file(path_manager.get_area_path(current_area_id))
                    if current_area_full_data and "locations" in current_area_full_data:
                        for loc_id in connected_ids_current_area:
                            found_loc = next((l["name"] for l in current_area_full_data["locations"] if l["locationId"] == loc_id), loc_id)
                            connected_names_current_area.append(found_loc)
                    if connected_names_current_area:
                         connected_locations_display_str = ", ".join(connected_names_current_area)
                
                # Get connections to other areas
                if "areaConnectivity" in location_data and location_data["areaConnectivity"]:
                    area_names = location_data.get("areaConnectivity", [])
                    area_ids = location_data.get("areaConnectivityId", [])
                    area_connections_formatted = []
                    for i, name in enumerate(area_names):
                        conn_id = area_ids[i] if i < len(area_ids) else "Unknown ID"
                        area_connections_formatted.append(f"{name}")
                    
                    if area_connections_formatted:
                        connected_areas_display_str = ". Connects to new areas: " + ", ".join(area_connections_formatted)
            
            # --- INTER-MODULE CONNECTIVITY SECTION ---
            available_modules_str = ""
            try:
                # Load world registry to get all available modules
                world_registry_path = "modules/world_registry.json"
                world_registry = safe_read_json(world_registry_path)
                
                if world_registry and 'modules' in world_registry:
                    current_module = party_tracker_data.get('module', '').replace(' ', '_')
                    all_modules = list(world_registry['modules'].keys())
                    other_modules = [m for m in all_modules if m != current_module]
                    
                    if other_modules:
                        # Get areas from other modules
                        other_module_areas = []
                        for module_name in other_modules:
                            module_info = world_registry['modules'][module_name]
                            # Get the areas for this module from the areas section
                            module_areas = []
                            for area_id, area_info in world_registry.get('areas', {}).items():
                                if area_info.get('module') == module_name:
                                    area_name = area_info.get('areaName', area_id)
                                    module_areas.append(f"{area_name} ({area_id})")
                            
                            if module_areas:
                                level_range = module_info.get('levelRange', {})
                                level_str = f"Level {level_range.get('min', '?')}-{level_range.get('max', '?')}"
                                
                                # Get starting location for this module
                                try:
                                    start_location_id, start_location_name, start_area_id, start_area_name = action_handler.get_module_starting_location(module_name)
                                    starting_info = f" (Starting location: {start_location_name} [{start_location_id}] in {start_area_name} [{start_area_id}])"
                                except Exception as e:
                                    print(f"Warning: Could not get starting location for {module_name}: {e}")
                                    starting_info = ""
                                
                                module_description = f"{module_name} [{level_str}]: {', '.join(module_areas[:3])}{starting_info}"
                                other_module_areas.append(module_description)
                        
                        if other_module_areas:
                            available_modules_str = ". Available modules for travel: " + "; ".join(other_module_areas)
            except Exception as e:
                print(f"DEBUG: Failed to load inter-module connectivity: {e}")
            # --- END OF INTER-MODULE CONNECTIVITY SECTION ---
            # --- END OF CONNECTIVITY SECTION ---
            
            # Use current module from party tracker for plot data
            current_module_for_plot = party_tracker_data.get("module", "").replace(" ", "_")
            current_plot_manager = ModulePathManager(current_module_for_plot)
            plot_data_for_note = load_json_file(current_plot_manager.get_plot_path())
            print(f"DEBUG: Plot file path: {current_plot_manager.get_plot_path()}")
            print(f"DEBUG: Plot data loaded: {plot_data_for_note is not None}")
            if plot_data_for_note:
                print(f"DEBUG: Plot data keys: {list(plot_data_for_note.keys())}")
            else:
                print("DEBUG: No plot data loaded - plot_data_for_note is None") 
            current_plot_points = []
            if plot_data_for_note and "plotPoints" in plot_data_for_note:
                 current_plot_points = [
                    point for point in plot_data_for_note["plotPoints"]
                    if point.get("location") == current_area_id and point["status"] != "completed"
                ]
            plot_points_str = "\n".join([f"- {point['title']}: {point['description']}" for point in current_plot_points])
            
            side_quests = []
            for point in current_plot_points:
                for quest in point.get("sideQuests", []):
                    if quest["status"] != "completed":
                        side_quests.append(f"- {quest['title']} (Status: {quest['status']}): {quest['description']}")
            side_quests_str = "\n".join(side_quests)

            traps_str = "None listed"
            if location_data and "traps" in location_data: 
                traps = location_data.get("traps", [])
                if traps:
                    traps_str = "\n".join([
                        f"- {trap.get('name', 'Unknown Trap')}: {trap.get('description', 'No description')} (Detect DC: {trap.get('detectDC', 'N/A')}, Disable DC: {trap.get('disableDC', 'N/A')}, Trigger DC: {trap.get('triggerDC', 'N/A')}, Damage: {trap.get('damage', 'N/A')})"
                        for trap in traps
                    ])

            monsters_str = "None listed"
            if location_data and "monsters" in location_data:
                monsters = location_data.get("monsters", [])
                if monsters:
                    monster_list = []
                    for monster in monsters:
                        name = monster.get('name', 'Unknown')
                        qty = monster.get('quantity', {})
                        if isinstance(qty, dict):
                            qty_str = f"{qty.get('min', 1)}-{qty.get('max', 1)}"
                        else:
                            qty_str = str(qty)
                        monster_list.append(f"- {name} ({qty_str})")
                    monsters_str = "\n".join(monster_list)

            # Check ALL modules for plot completion before suggesting module creation
            module_creation_prompt = ""
            try:
                # Debug current module detection
                current_module = party_tracker_data.get('module', '').replace(' ', '_')
                print(f"DEBUG: Current module from party tracker: '{current_module}'")
                
                # Use new comprehensive module completion checker
                all_modules_completion = check_all_modules_plot_completion()
                
                # Extract results
                all_modules_complete = all_modules_completion["all_complete"]
                modules_checked = all_modules_completion["modules_checked"]
                completion_summary = all_modules_completion["completion_summary"]
                
                # Print summary of all modules
                print(f"DEBUG: === ALL MODULES COMPLETION SUMMARY ===")
                for module_name, summary in completion_summary.items():
                    status = "COMPLETE" if summary["is_complete"] else "INCOMPLETE"
                    print(f"DEBUG: {module_name}: {summary['completed_plots']}/{summary['total_plots']} plots - {status}")
                print(f"DEBUG: === END SUMMARY ===")
                
                # Determine if we should inject module creation prompt
                # Only suggest module creation if ALL modules are complete
                should_inject_creation_prompt = all_modules_complete and len(modules_checked) > 0
                
                print(f"DEBUG: All modules complete: {all_modules_complete}")
                print(f"DEBUG: Should inject module creation prompt: {should_inject_creation_prompt}")
                
                # If ALL modules are complete, inject creation prompt
                if should_inject_creation_prompt:
                    print("DEBUG: *** MODULE CREATION PROMPT INJECTION TRIGGERED ***")
                    print("DEBUG: All available modules have completed plots - suggesting new module creation")
                    # Load the module creation prompt
                    import os
                    if os.path.exists("module_creation_prompt.txt"):
                        with open("module_creation_prompt.txt", "r", encoding="utf-8") as f:
                            module_creation_prompt = "\n\n" + f.read()
                        print(f"DEBUG: Module creation prompt loaded ({len(module_creation_prompt)} characters)")
                    else:
                        print("DEBUG: module_creation_prompt.txt not found!")
                else:
                    incomplete_modules = [name for name, summary in completion_summary.items() if not summary["is_complete"]]
                    if incomplete_modules:
                        print(f"DEBUG: Module creation prompt NOT injected - incomplete modules: {incomplete_modules}")
                    else:
                        print(f"DEBUG: Module creation prompt NOT injected - no modules found to check")
                    
            except Exception as e:
                print(f"DEBUG: Module completion check failed: {e}")
                import traceback
                traceback.print_exc()
            
            # Sanitize location name before using in DM note
            current_location_name_note = sanitize_text(current_location_name_note)
            dm_note = (f"Dungeon Master Note: Current date and time: {date_time_str}. "
                f"Party stats: {party_stats_str}. "
                f"Current location: {current_location_name_note} ({current_location_id_note}). "
                # --- MODIFIED LINE TO INCLUDE CONNECTIVITY ---
                f"Adjacent locations in this area: {connected_locations_display_str}{connected_areas_display_str}{available_modules_str}.\n"
                # --- END OF MODIFIED LINE ---
                f"Active plot points for this location:\n{plot_points_str}\n"
                f"Active side quests for this location:\n{side_quests_str}\n"
                f"Monsters in this location:\n{monsters_str}\n"
                f"Traps in this location:\n{traps_str}\n"
                "Monsters should be active threats per engagement rules. "
                "updateCharacterInfo for player and NPC character changes (inventory, stats, abilities), "
                "updateTime for time passage, "
                "updatePlot for story progression, discovers, and new information, "
                "updatePartyNPCs for party composition changes to the party tracker, "
                "levelUp for advancement, "
                "establishHub when the party gains ownership or control of a location that could serve as a base of operations (stronghold, tavern, keep, etc.) - example: establishHub('The Silver Swan Inn', {hubType: 'tavern', description: 'Our permanent base of operations', services: ['rest', 'information'], ownership: 'party'}), "
                "exitGame for ending sessions, and "
                "transitionLocation should always be used when the player expresses a desire to move to an adjacent location to their current location, "
                "Always roleplay the NPC and NPC party rolls without asking the player. "
                "Always ask the player character to roll for skill checks and other actions. "
                "Proactively narrate location NPCs, start conversations, and weave plot elements into the adventure. "
                "Use party NPCs to narrate if possible instead of always narrating from the DM's perspective, but don't overdo it. "
                "Maintain immersive and engaging storytelling similar to an adventure novel while accurately managing game mechanics. "
                "Update all relevant information immediately and confirm with the player before major actions. "
                "Consider whether the party's action trigger traps in this location. "
                "Consider updating the plot elements on every action the player and NPCs take."
                f"{module_creation_prompt}")
        else:
            dm_note = "Dungeon Master Note: Remember to take actions if necessary such as updating the plot, time, character sheets, and location if changes occur."

        user_input_with_note = f"{dm_note} Player: {user_input_text}"
        conversation_history.append({"role": "user", "content": user_input_with_note})
        save_conversation_history(conversation_history)

        retry_count = 0
        valid_response_received = False 
        ai_response_content = None 

        while retry_count < 5 and not valid_response_received:
            ai_response_content = get_ai_response(conversation_history)
            validation_result = validate_ai_response(ai_response_content, user_input_text, validation_prompt_text, conversation_history, party_tracker_data)
            if validation_result is True:
                valid_response_received = True
                print(f"DEBUG: Valid response generated on attempt {retry_count + 1}")
                # Pass the same location_data that was used for the DM note construction
                result = process_ai_response(ai_response_content, party_tracker_data, location_data, conversation_history) 
                if result == "exit":
                    return
            elif isinstance(validation_result, str):
                print(f"DEBUG: Validation failed. Reason: {validation_result}")
                print(f"Retrying... (Attempt {retry_count + 1}/5)")
                status_retrying(retry_count + 1, 5)
                conversation_history.append({
                    "role": "user",
                    "content": f"Error Note: Your previous response failed validation. Reason: {validation_result}. Please adjust your response accordingly."
                })
                retry_count += 1
            else: 
                print(f"DEBUG: Unexpected validation result: {validation_result}. Assuming invalid and retrying.")
                retry_count += 1


        if not valid_response_received:
            print("Failed to generate a valid response after 5 attempts. Proceeding with the last generated response.")
            if ai_response_content: 
                result = process_ai_response(ai_response_content, party_tracker_data, location_data, conversation_history) 
                if result == "exit":
                    return
            else:
                print("ERROR: No AI response was generated after retries.")
                conversation_history.append({"role": "assistant", "content": "I seem to be having trouble formulating a response. Could you try rephrasing your action or query?"})
                save_conversation_history(conversation_history)
        
        # Always ensure status is reset to ready at end of main game loop
        try:
            status_ready()
            print("DEBUG: Status reset to ready at end of main game loop")
        except Exception as e:
            print(f"DEBUG: Error resetting status at end of main game loop: {e}")


        current_area_id = party_tracker_data["worldConditions"]["currentAreaId"] 
        # Use current module from party tracker for plot data  
        module_name_updated = party_tracker_data.get("module", "").replace(" ", "_")
        updated_path_manager = ModulePathManager(module_name_updated)
        plot_data = load_json_file(updated_path_manager.get_plot_path())
        module_data = load_json_file(updated_path_manager.get_module_file_path())
        print(f"DEBUG: Updated plot file path: {updated_path_manager.get_plot_path()}")

        conversation_history = update_conversation_history(conversation_history, party_tracker_data, plot_data, module_data)
        conversation_history = update_character_data(conversation_history, party_tracker_data)
        conversation_history = ensure_main_system_prompt(conversation_history, main_system_prompt_text)
        
        # Use the new order_conversation_messages function
        conversation_history = order_conversation_messages(conversation_history, main_system_prompt_text)
        
        save_conversation_history(conversation_history)

def main():
    """Main entry point with startup wizard integration"""
    setup_utf8_console()
    
    # Check if first-time setup is needed
    try:
        from startup_wizard import startup_required, run_startup_sequence
        
        if startup_required():
            print("[D20] Welcome to your 5th Edition Adventure! [D20]")
            print("It looks like this is your first time, or you need to set up a character.")
            print("Let's get you ready for adventure!\n")
            
            success = run_startup_sequence()
            if not success:
                print("[ERROR] Setup was cancelled or failed. Exiting...")
                return
            
            print("Setup complete! Your adventure begins now...\n")
    
    except Exception as e:
        print(f"[WARNING] Startup wizard had an issue: {e}")
        print("Continuing with main game (assuming setup is complete)...\n")
    
    # Continue with normal game loop
    main_game_loop()

if __name__ == "__main__":
    main()