# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

# ============================================================================
# CONVERSATION_UTILS.PY - AI CONTEXT MANAGEMENT LAYER
# ============================================================================
# 
# ARCHITECTURE ROLE: AI Integration Layer - Context and History Management
# 
# This module manages AI conversation context, history compression, and
# memory optimization to maintain coherent long-term game sessions while
# respecting AI model token limitations.
# 
# KEY RESPONSIBILITIES:
# - Conversation history management and persistence
# - Intelligent context trimming and compression
# - Game state synchronization with AI context
# - Memory optimization for long-running sessions
# - Context rebuilding after session interruptions
# - Character data formatting for AI consumption
# 
# CONTEXT MANAGEMENT STRATEGY:
# - Rolling conversation window with intelligent pruning
# - Key game state preservation across context reductions
# - Selective history compression based on importance
# - Real-time context size monitoring and optimization
# 
# INFORMATION ARCHITECTURE DESIGN:
# - SYSTEM MESSAGES: Static character reference data (Virtues, Knight type, abilities)
# - DM NOTES: Dynamic, frequently-changing data (Guard, Glory, status)
# - SEPARATION PRINCIPLE: Prevents AI confusion from conflicting data versions
# - SINGLE SOURCE OF TRUTH: DM Note is authoritative for current character state
# 
# DATA SEPARATION STRATEGY:
# System Messages (Static Reference):
#   - Knight Virtues (VIG, CLA, SPI base values)
#   - Knight type, Property, Ability, Passion
#   - Equipment, trade goods
#   - Knighted by (Seer information)
# 
# DM Notes (Dynamic Current State):
#   - Current Guard and Virtue damage
#   - Current Glory and Rank
#   - Active conditions and temporary effects
#   - Real-time combat status
# 
# COMPRESSION TECHNIQUES:
# - Adventure summary generation for long-term memory
# - Character state snapshots for quick context rebuilding
# - Important event highlighting and preservation
# - Redundant information removal while preserving continuity
# 
# ARCHITECTURAL INTEGRATION:
# - Core dependency for dm_wrapper.py AI interactions
# - Integrates with main.py for session management
# - Uses file_operations.py for conversation persistence
# - Supports cumulative_summary.py for long-term memory
# 
# AI CONTEXT OPTIMIZATION:
# - Token-aware context management
# - Model-specific optimization strategies
# - Intelligent prompt construction with relevant history
# - Context freshness tracking and stale data removal
# - Conflict prevention through data source separation
# 
# DESIGN PATTERNS:
# - Memento Pattern: Conversation state snapshots
# - Strategy Pattern: Different compression strategies
# - Observer Pattern: Context size change notifications
# - Single Source of Truth: Dynamic data authority separation
# 
# This module ensures AI maintains coherent understanding of ongoing
# adventures while optimizing performance and token usage, and prevents
# confusion through clear separation of static vs dynamic character data.
# ============================================================================

import json
import os
from utils.module_path_manager import ModulePathManager
from utils.encoding_utils import safe_json_load
from utils.plot_formatting import format_plot_for_ai
from utils.enhanced_logger import debug, info, warning, error, set_script_name

# Set script name for logging
set_script_name("conversation_utils")

# ============================================================================
# CAMPAIGN SUMMARY INJECTION
# ============================================================================

def inject_campaign_summaries(new_history):
    """Inject campaign summaries as system messages into conversation history"""
    try:
        summaries_dir = "modules/campaign_summaries"
        if os.path.exists(summaries_dir):
            summary_files = [f for f in os.listdir(summaries_dir) if '_summary_' in f and f.endswith('.json')]
            
            # Load all summaries with their completion dates for proper chronological sorting
            summaries_with_dates = []
            for summary_file in summary_files:
                try:
                    summary_path = os.path.join(summaries_dir, summary_file)
                    summary_data = safe_json_load(summary_path)
                    if summary_data and "completionDate" in summary_data:
                        summaries_with_dates.append((summary_data["completionDate"], summary_file, summary_data))
                except Exception as e:
                    debug(f"WARNING: Could not load completion date from {summary_file}", exception=e, category="campaign_context")
            
            # Sort by completion date (chronological order)
            summaries_with_dates.sort(key=lambda x: x[0])
            
            if summaries_with_dates:
                for completion_date, summary_file, summary_data in summaries_with_dates:
                    try:
                        if summary_data and "summary" in summary_data:
                            module_name = summary_data.get("moduleName", "Unknown Module")
                            sequence = summary_data.get("sequenceNumber", 1)
                            
                            # Create the full content for this single chronicle
                            chronicle_content = (
                                f"=== CAMPAIGN CONTEXT ===\n\n"
                                f"--- {module_name} (Chronicle {sequence:03d}) ---\n"
                                f"{summary_data['summary']}"
                            )
                            
                            # Append it as a new, separate system message
                            new_history.append({"role": "system", "content": chronicle_content})
                            
                            debug(f"SUCCESS: Injected chronicle for {module_name} (completed {completion_date}) as a separate system message", category="campaign_context")
                    except Exception as e:
                        debug(f"FAILURE: Could not inject summary {summary_file}", exception=e, category="campaign_context")
            else:
                debug(f"INFO: No campaign summary files found in {summaries_dir}", category="campaign_context")
    except Exception as e:
        debug(f"FAILURE: Error injecting campaign summaries", exception=e, category="campaign_context")

# ============================================================================
# MODULE TRANSITION DETECTION AND HANDLING
# ============================================================================

def find_last_module_transition_index(conversation_history):
    """Find the index of the last module transition marker"""
    for i in range(len(conversation_history) - 1, -1, -1):
        message = conversation_history[i]
        if (message.get("role") == "user" and 
            message.get("content", "").startswith("Module transition:")):
            return i
    return -1  # No previous module transition found

def find_last_system_message_index(conversation_history):
    """Find the index of the last system message to use as boundary marker"""
    for i in range(len(conversation_history) - 1, -1, -1):
        if conversation_history[i].get("role") == "system":
            return i
    return 0  # If no system message found, start from beginning

def extract_conversation_segment(conversation_history, start_index):
    """Extract conversation segment from start_index to end"""
    if start_index >= len(conversation_history):
        return []
    return conversation_history[start_index:]

def generate_conversation_summary(conversation_segment, module_name):
    """Generate a concise summary of the conversation segment for a module"""
    if not conversation_segment:
        return f"Brief activities in {module_name}."
    
    # Count meaningful interactions (exclude system messages and transitions)
    meaningful_messages = [
        msg for msg in conversation_segment 
        if msg.get("role") in ["user", "assistant"] and 
        not msg.get("content", "").startswith(("Location transition:", "Module transition:"))
    ]
    
    if len(meaningful_messages) <= 2:
        return f"Brief activities in {module_name}."
    elif len(meaningful_messages) <= 5:
        return f"Short adventure in {module_name} with several interactions."
    else:
        return f"Extended adventure in {module_name} with multiple significant events and discoveries."

def insert_module_summary_and_transition(conversation_history, summary_text, transition_text, insertion_index):
    """Insert module summary and transition marker at specified index"""
    # Create summary message
    summary_message = {
        "role": "user",
        "content": f"Module summary: {summary_text}"
    }
    
    # Create transition message  
    transition_message = {
        "role": "user",
        "content": transition_text
    }
    
    # Insert both messages at the specified index
    conversation_history.insert(insertion_index, summary_message)
    conversation_history.insert(insertion_index + 1, transition_message)
    
    debug(f"STATE_CHANGE: Inserted module summary and transition at index {insertion_index}", category="module_management")
    debug(f"STATE_CHANGE: Module transition message: '{transition_text}'", category="module_management")
    
    return conversation_history

def handle_module_conversation_segmentation(conversation_history, from_module, to_module):
    """Insert module transition marker - compression handled later by check_and_process_module_transitions()
    
    This function now only inserts the transition marker. The actual conversation
    compression is handled separately by check_and_process_module_transitions() 
    which mirrors the location transition processing logic.
    """
    debug(f"STATE_CHANGE: Inserting module transition marker for {from_module} -> {to_module}", category="module_management")
    
    # Simply insert the module transition marker at the end (matching location transition format)
    transition_text = f"Module transition: {from_module} to {to_module}"
    transition_message = {
        "role": "user",
        "content": transition_text
    }
    
    # Add transition marker to conversation history
    conversation_history.append(transition_message)
    
    debug(f"STATE_CHANGE: Module transition marker inserted: '{transition_text}'", category="module_management")
    debug(f"STATE_CHANGE: Conversation history now has {len(conversation_history)} messages", category="conversation_management")
    
    return conversation_history

def get_previous_module_from_history(conversation_history):
    """Extract the previous module from conversation history"""
    # Look for the most recent module transition marker
    last_transition_index = find_last_module_transition_index(conversation_history)
    if last_transition_index != -1:
        # Parse the transition message to get the "to" module
        transition_msg = conversation_history[last_transition_index].get("content", "")
        # Format: "Module transition: from_module to to_module"
        parts = transition_msg.split(" to ")
        if len(parts) == 2:
            return parts[1].strip()
    
    # If no transition found, look for module info in system messages
    for msg in reversed(conversation_history):
        if msg.get("role") == "system":
            content = msg.get("content", "")
            if "Current module:" in content:
                # Extract module name from world state context
                import re
                match = re.search(r"Current module: ([^\n(]+)", content)
                if match:
                    return match.group(1).strip()
    
    return None

def compress_json_data(data):
    """Compress JSON data by removing unnecessary whitespace."""
    return json.dumps(data, separators=(',', ':'))

def load_json_data(file_path):
    try:
        data = safe_json_load(file_path)
        if data is not None:
            return compress_json_data(data)
        else:
            print(f"{file_path} not found. Returning None.")
            return None
    except json.JSONDecodeError:
        print(f"{file_path} has an invalid JSON format. Returning None.")
        return None

def update_conversation_history(conversation_history, party_tracker_data, plot_data, module_data):
    # Read the actual system prompt to get the proper identifier
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "prompts", "mythic_system_prompt.txt"), "r", encoding="utf-8") as file:
        main_system_prompt_text = file.read().strip()
    
    # Use the first part of the actual system prompt as identifier
    main_prompt_start = main_system_prompt_text[:50]  # First 50 characters as identifier
    
    # Find and remove the primary system prompt (the one that starts with our identifier)
    primary_system_prompt = None
    for msg in conversation_history:
        if msg["role"] == "system" and msg["content"].startswith(main_prompt_start):
            primary_system_prompt = msg
            break
    
    if primary_system_prompt:
        conversation_history.remove(primary_system_prompt)

    # ============================================================================
    # MODULE TRANSITION DETECTION (BEFORE SYSTEM MESSAGE REMOVAL)
    # ============================================================================
    # Check if there has been a module transition by comparing current module
    # with the module from previous conversation state BEFORE removing system messages
    current_module = party_tracker_data.get('module', 'Unknown') if party_tracker_data else 'Unknown'
    previous_module = get_previous_module_from_history(conversation_history)

    # Remove any existing system messages for location, party tracker, plot, map, module data, world state, and campaign context
    updated_history = [
        msg for msg in conversation_history 
        if not (msg["role"] == "system" and 
                any(key in msg["content"] for key in [
                    "Current Location:", 
                    "No active location data available",
                    "Here's the updated party tracker data:",
                    "Here's the current plot data:",
                    "=== ADVENTURE PLOT STATUS ===",
                    "Here's the current map data:",
                    "Here's the module data:",
                    "WORLD STATE CONTEXT:",
                    "=== CAMPAIGN CONTEXT ==="
                ]))
    ]

    # Create a new list starting with the primary system prompt
    new_history = [primary_system_prompt] if primary_system_prompt else []
    
    debug(f"VALIDATION: Module transition check - previous: '{previous_module}', current: '{current_module}'", category="module_management")
    
    # Module transition detection and marker insertion now happens in action_handler.py
    # This section is preserved for any future module transition logic

    # Insert world state information
    try:
        from core.managers.campaign_manager import CampaignManager
        campaign_manager = CampaignManager()
        available_modules = campaign_manager.campaign_data.get('availableModules', [])
        
        # Get current module from actual party_tracker.json file
        current_module = 'Unknown'
        party_tracker_file = "party_tracker.json"
        try:
            if os.path.exists(party_tracker_file):
                party_data = safe_json_load(party_tracker_file)
                if party_data:
                    current_module = party_data.get('module', 'Unknown')
        except:
            # Fallback to parameter if file reading fails
            current_module = party_tracker_data.get('module', 'Unknown') if party_tracker_data else 'Unknown'
        
        world_state_parts = []
        if available_modules:
            other_modules = [m for m in available_modules if m != current_module]
            if other_modules:
                world_state_parts.append(f"Available modules for travel: {', '.join(other_modules)}")
                world_state_parts.append(f"To travel to another module, use: 'I travel to [module name]' or similar explicit phrasing")
            world_state_parts.append(f"Current module: {current_module}")
        else:
            world_state_parts.append(f"Current module: {current_module} (no other modules detected)")
            
        # Add hub information if available
        hubs = campaign_manager.campaign_data.get('hubs', {})
        if hubs:
            hub_names = list(hubs.keys())
            world_state_parts.append(f"Established hubs: {', '.join(hub_names)}")
            
        if world_state_parts:
            world_state_message = "WORLD STATE CONTEXT:\n" + "\n".join(world_state_parts)
            new_history.append({"role": "system", "content": world_state_message})
            
    except Exception as e:
        # Don't let world state errors break the conversation system
        pass
    
    # CAMPAIGN SUMMARY INJECTION: Add previous adventure context
    try:
        inject_campaign_summaries(new_history)
    except Exception as e:
        debug(f"FAILURE: Error injecting campaign summaries", exception=e, category="campaign_context")
    
# Module transition detection now happens before system message removal above

    # Insert plot data with new formatting
    if plot_data:
        formatted_plot = format_plot_for_ai(plot_data)
        new_history.append({"role": "system", "content": formatted_plot})

    # Get the current area and location ID from the party tracker data
    current_area = party_tracker_data["worldConditions"]["currentArea"] if party_tracker_data else None
    current_area_id = party_tracker_data["worldConditions"]["currentAreaId"] if party_tracker_data else None
    current_location_id = party_tracker_data["worldConditions"]["currentLocationId"] if party_tracker_data else None

    # Insert map data
    if current_area_id:
        # Use current module from party tracker for consistent path resolution
        current_module_name = party_tracker_data.get("module", "").replace(" ", "_") if party_tracker_data else None
        path_manager = ModulePathManager(current_module_name)
        map_file = path_manager.get_map_path(current_area_id)
        map_data = load_json_data(map_file)
        if map_data:
            map_message = "Here's the current map data:\n"
            map_message += f"{map_data}\n"
            new_history.append({"role": "system", "content": map_message})

    # Load the area-specific JSON file
    if current_area_id:
        # Use current module from party tracker for consistent path resolution
        current_module_name = party_tracker_data.get("module", "").replace(" ", "_") if party_tracker_data else None
        path_manager = ModulePathManager(current_module_name)
        area_file = path_manager.get_area_path(current_area_id)
        try:
            location_data = safe_json_load(area_file)
            if location_data is None:
                print(f"{area_file} not found. Skipping location data.")
        except json.JSONDecodeError:
            print(f"{area_file} has an invalid JSON format. Skipping location data.")
            location_data = None

    # Find the relevant location data based on the current location ID
    current_location = None
    if location_data and current_location_id:
        for location in location_data["locations"]:
            if location["locationId"] == current_location_id:
                current_location = location
                break

    # Insert the most recent location information
    if current_location:
        new_history.append({
            "role": "system",
            "content": f"Current Location:\n{compress_json_data(current_location)}\n"
        })

    # Add party tracker data with calendar system information
    if party_tracker_data:
        # Load calendar system prompt
        calendar_info = ""
        try:
            with open("prompts/calendar.txt", "r", encoding="utf-8") as f:
                calendar_info = f.read()
        except:
            debug("WARNING: Could not load calendar.txt prompt", category="conversation_management")
        
        party_tracker_message = "Here's the updated party tracker data:\n"
        party_tracker_message += f"Party Tracker Data: {compress_json_data(party_tracker_data)}\n"
        
        # Add calendar information if available
        if calendar_info:
            party_tracker_message += f"\n{calendar_info}\n"
        
        new_history.append({"role": "system", "content": party_tracker_message})

    # Add the rest of the conversation history
    debug(f"STATE_CHANGE: update_conversation_history preserving {len(updated_history)} messages", category="conversation_management")
    # Check for module transition messages
    module_transitions = [msg for msg in updated_history if msg.get("role") == "user" and "Module transition:" in msg.get("content", "")]
    if module_transitions:
        debug(f"VALIDATION: Found {len(module_transitions)} module transition messages in preserved history", category="module_management")
    else:
        debug("VALIDATION: No module transition messages found in preserved history", category="module_management")
    new_history.extend(updated_history)

    # Generate lightweight chat history for debugging
    generate_chat_history(new_history)

    return new_history

def update_character_data(conversation_history, party_tracker_data):
    updated_history = conversation_history.copy()

    # Remove old character data
    updated_history = [
        entry
        for entry in updated_history
        if not (
            entry["role"] == "system"
            and ("Here's the updated character data for" in entry["content"]
                 or "Here's the NPC data for" in entry["content"])
        )
    ]

    if party_tracker_data:
        character_data = []
        # Get current module from party tracker for consistent path resolution
        current_module = party_tracker_data.get("module", "").replace(" ", "_")
        path_manager = ModulePathManager(current_module)
        
        # Process player characters
        for member in party_tracker_data["partyMembers"]:
            # Normalize name for file access
            from updates.update_character_info import normalize_character_name
            normalized_member = normalize_character_name(member)
            name = member.lower()
            member_file = path_manager.get_character_path(normalized_member)
            try:
                with open(member_file, "r", encoding="utf-8") as file:
                    member_data = json.load(file)
                    
                    # Validate that member_data is a dictionary
                    if not isinstance(member_data, dict):
                        print(f"Warning: {member_file} contains corrupted data (not a dictionary). Skipping.")
                        continue
                    
                    # Format equipment list with quantities
                    equipment_list = []
                    for item in member_data['equipment']:
                        item_description = f"{item['item_name']} ({item['item_type']})"
                        if item['quantity'] > 1:
                            item_description = f"{item_description} x{item['quantity']}"
                        equipment_list.append(item_description)
                    
                    equipment_str = ", ".join(equipment_list)

                    # Handle backgroundFeature which might be None or bool
                    bg_feature = member_data.get('backgroundFeature')
                    bg_feature_name = 'None'
                    if isinstance(bg_feature, dict) and 'name' in bg_feature:
                        bg_feature_name = bg_feature['name']
                    
                    
                    # Format character data
                    # Format Mythic Bastionland character data
                    virtues = member_data.get('virtues', {})
                    knight_data = member_data.get('knight_data', {})
                    
                    formatted_data = f"""
KNIGHT: {member_data['name']}
TYPE: {knight_data.get('type', 'Unknown Knight')} | GLORY: {member_data.get('glory', 0)} | RANK: {member_data.get('rank', 'Knight-Errant')}
VIRTUES: VIG {virtues.get('vigour', 10)} | CLA {virtues.get('clarity', 10)} | SPI {virtues.get('spirit', 10)}
GUARD: {member_data.get('guard', 1)} | STATUS: {member_data.get('status', 'Active')} | CONDITION: {member_data.get('condition', 'Normal')}
PROPERTY: {knight_data.get('property', 'None listed')}
ABILITY: {knight_data.get('ability', 'None listed')}
PASSION: {knight_data.get('passion', 'None listed')}
KNIGHTED BY: {knight_data.get('seer', {}).get('name', 'Unknown Seer')}
EQUIPMENT: {equipment_str}
TRADE GOODS: {', '.join(member_data.get('trade_goods', ['None']))}
NOTES: {member_data.get('notes', 'None')}
"""
                    character_message = f"Here's the updated character data for {name}:\n{formatted_data}\n"
                    character_data.append({"role": "system", "content": character_message})
            except FileNotFoundError:
                print(f"{member_file} not found. Skipping JSON data for {name}.")
            except json.JSONDecodeError:
                print(f"{member_file} has an invalid JSON format. Skipping JSON data for {name}.")
        
        # Process NPCs
        for npc in party_tracker_data.get("partyNPCs", []):
            npc_name = npc['name']
            npc_file = path_manager.get_character_path(npc_name)
            try:
                with open(npc_file, "r", encoding="utf-8") as file:
                    npc_data = json.load(file)
                    
                    # Validate that npc_data is a dictionary
                    if not isinstance(npc_data, dict):
                        print(f"Warning: {npc_file} contains corrupted data (not a dictionary). Skipping.")
                        continue
                    
                    # Format equipment list with quantities
                    equipment_list = []
                    for item in npc_data['equipment']:
                        item_description = f"{item['item_name']} ({item['item_type']})"
                        if item['quantity'] > 1:
                            item_description = f"{item_description} x{item['quantity']}"
                        equipment_list.append(item_description)
                    
                    equipment_str = ", ".join(equipment_list)
                    
                    # Handle backgroundFeature which might be None or bool
                    bg_feature = npc_data.get('backgroundFeature')
                    bg_feature_name = 'None'
                    if isinstance(bg_feature, dict) and 'name' in bg_feature:
                        bg_feature_name = bg_feature['name']


                    # Format NPC data (using same schema as players)
                    # Format Mythic Bastionland NPC data
                    virtues = npc_data.get('virtues', {})
                    knight_data = npc_data.get('knight_data', {})
                    
                    formatted_data = f"""
KNIGHT NPC: {npc_data['name']}
ROLE: {npc['role']} | TYPE: {knight_data.get('type', 'Unknown Knight')} | GLORY: {npc_data.get('glory', 0)} | RANK: {npc_data.get('rank', 'Knight-Errant')}
VIRTUES: VIG {virtues.get('vigour', 10)} | CLA {virtues.get('clarity', 10)} | SPI {virtues.get('spirit', 10)}
GUARD: {npc_data.get('guard', 1)} | STATUS: {npc_data.get('status', 'Active')} | CONDITION: {npc_data.get('condition', 'Normal')}
PROPERTY: {knight_data.get('property', 'None listed')}
ABILITY: {knight_data.get('ability', 'None listed')}
PASSION: {knight_data.get('passion', 'None listed')}
KNIGHTED BY: {knight_data.get('seer', {}).get('name', 'Unknown Seer')}
EQUIPMENT: {equipment_str}
TRADE GOODS: {', '.join(npc_data.get('trade_goods', ['None']))}
NOTES: {npc_data.get('notes', 'None')}
"""
                    npc_message = f"Here's the NPC data for {npc_data['name']}:\n{formatted_data}\n"
                    character_data.append({"role": "system", "content": npc_message})
            except FileNotFoundError:
                print(f"{npc_file} not found. Skipping JSON data for NPC {npc['name']}.")
            except json.JSONDecodeError:
                print(f"{npc_file} has an invalid JSON format. Skipping JSON data for NPC {npc['name']}.")
        
        # Insert character and NPC data after party tracker data
        party_tracker_index = next((i for i, msg in enumerate(updated_history) if msg["role"] == "system" and "Here's the updated party tracker data:" in msg["content"]), -1)
        if party_tracker_index != -1:
            for i, char_data in enumerate(character_data):
                updated_history.insert(party_tracker_index + 1 + i, char_data)
        else:
            updated_history.extend(character_data)

    return updated_history

def generate_chat_history(conversation_history):
    """Generate a lightweight chat history without system messages"""
    output_file = "modules/conversation_history/chat_history.json"
    
    try:
        # Filter out system messages and keep only user and assistant messages
        chat_history = [msg for msg in conversation_history if msg["role"] != "system"]
        
        # Write the filtered chat history to the output file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(chat_history, f, indent=2)
        
        # Print statistics
        system_count = len(conversation_history) - len(chat_history)
        total_count = len(conversation_history)
        user_count = sum(1 for msg in chat_history if msg["role"] == "user")
        assistant_count = sum(1 for msg in chat_history if msg["role"] == "assistant")
        
        info(f"SUCCESS: Lightweight chat history updated!", category="conversation_history")
        debug(f"System messages removed: {system_count}", category="conversation_history")
        debug(f"User messages: {user_count}", category="conversation_history")
        debug(f"Assistant messages: {assistant_count}", category="conversation_history")
        
    except Exception as e:
        error(f"FAILURE: Error generating chat history: {str(e)}", exception=e, category="conversation_history")