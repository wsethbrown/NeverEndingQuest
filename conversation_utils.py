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
# - SYSTEM MESSAGES: Static character reference data (stats, abilities, spells)
# - DM NOTES: Dynamic, frequently-changing data (HP, spell slots, status)
# - SEPARATION PRINCIPLE: Prevents AI confusion from conflicting data versions
# - SINGLE SOURCE OF TRUTH: DM Note is authoritative for current character state
# 
# DATA SEPARATION STRATEGY:
# System Messages (Static Reference):
#   - Ability scores, skills, proficiencies
#   - Class features, racial traits, equipment lists
#   - Spellcasting ability/DC/bonus, known spells
#   - Personality traits, background information
# 
# DM Notes (Dynamic Current State):
#   - Current/max hit points
#   - Current/max spell slots
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
from module_path_manager import ModulePathManager
from encoding_utils import safe_json_load

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
    with open("system_prompt.txt", "r", encoding="utf-8") as file:
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

    # Remove any existing system messages for location, party tracker, plot, map, module data, and world state
    updated_history = [
        msg for msg in conversation_history 
        if not (msg["role"] == "system" and 
                any(key in msg["content"] for key in [
                    "Current Location:", 
                    "No active location data available",
                    "Here's the updated party tracker data:",
                    "Here's the current plot data:",
                    "Here's the current map data:",
                    "Here's the module data:",
                    "WORLD STATE CONTEXT:"
                ]))
    ]

    # Create a new list starting with the primary system prompt
    new_history = [primary_system_prompt] if primary_system_prompt else []

    # Insert world state information
    try:
        from campaign_manager import CampaignManager
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

    # Insert plot data
    if plot_data:
        plot_message = "Here's the current plot data:\n"
        plot_message += f"{plot_data}\n"  # plot_data is already compressed
        new_history.append({"role": "system", "content": plot_message})

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

    # Add party tracker data
    if party_tracker_data:
        party_tracker_message = "Here's the updated party tracker data:\n"
        party_tracker_message += f"Party Tracker Data: {compress_json_data(party_tracker_data)}\n"
        new_history.append({"role": "system", "content": party_tracker_message})

    # Add the rest of the conversation history
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
        path_manager = ModulePathManager()
        
        # Process player characters
        for member in party_tracker_data["partyMembers"]:
            name = member.lower()
            member_file = path_manager.get_character_path(member)
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
                    formatted_data = f"""
CHAR: {member_data['name']}
TYPE: {member_data['character_type'].capitalize()} | LVL: {member_data['level']} | RACE: {member_data['race']} | CLASS: {member_data['class']} | ALIGN: {member_data['alignment'][:2].upper()} | BG: {member_data['background']}
AC: {member_data['armorClass']} | SPD: {member_data['speed']}
STATUS: {member_data['status']} | CONDITION: {member_data['condition']} | AFFECTED: {', '.join(member_data['condition_affected'])}
STATS: STR {member_data['abilities']['strength']}, DEX {member_data['abilities']['dexterity']}, CON {member_data['abilities']['constitution']}, INT {member_data['abilities']['intelligence']}, WIS {member_data['abilities']['wisdom']}, CHA {member_data['abilities']['charisma']}
SAVES: {', '.join(member_data['savingThrows'])}
SKILLS: {', '.join(f"{skill} +{bonus}" for skill, bonus in member_data['skills'].items())}
PROF BONUS: +{member_data['proficiencyBonus']}
SENSES: {', '.join(f"{sense} {value}" for sense, value in member_data['senses'].items())}
LANGUAGES: {', '.join(member_data['languages'])}
PROF: {', '.join([f"{cat}: {', '.join(items)}" for cat, items in member_data['proficiencies'].items()])}
VULN: {', '.join(member_data['damageVulnerabilities'])}
RES: {', '.join(member_data['damageResistances'])}
IMM: {', '.join(member_data['damageImmunities'])}
COND IMM: {', '.join(member_data['conditionImmunities'])}
CLASS FEAT: {', '.join([f"{feature['name']}" for feature in member_data['classFeatures']])}
RACIAL: {', '.join([f"{trait['name']}" for trait in member_data['racialTraits']])}
BG FEAT: {bg_feature_name}
FEATS: {', '.join([f"{feat['name']}" for feat in member_data.get('feats', [])])}
TEMP FX: {', '.join([f"{effect['name']}" for effect in member_data.get('temporaryEffects', [])])}
EQUIP: {equipment_str}
AMMO: {', '.join([f"{ammo['name']} x{ammo['quantity']}" for ammo in member_data['ammunition']])}
ATK: {', '.join([f"{atk['name']} ({atk['type']}, {atk['damageDice']} {atk['damageType']})" for atk in member_data['attacksAndSpellcasting']])}
SPELLCASTING: {member_data.get('spellcasting', {}).get('ability', 'N/A')} | DC: {member_data.get('spellcasting', {}).get('spellSaveDC', 'N/A')} | ATK: +{member_data.get('spellcasting', {}).get('spellAttackBonus', 'N/A')}
SPELLS: {', '.join([f"{level}: {', '.join(spells)}" for level, spells in member_data.get('spellcasting', {}).get('spells', {}).items() if spells])}
CURRENCY: {member_data['currency']['gold']}G, {member_data['currency']['silver']}S, {member_data['currency']['copper']}C
XP: {member_data['experience_points']}/{member_data.get('exp_required_for_next_level', 'N/A')}
TRAITS: {member_data['personality_traits']}
IDEALS: {member_data['ideals']}
BONDS: {member_data['bonds']}
FLAWS: {member_data['flaws']}
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
                    formatted_data = f"""
NPC: {npc_data['name']}
ROLE: {npc['role']} | TYPE: {npc_data['character_type'].capitalize()} | LVL: {npc_data['level']} | RACE: {npc_data['race']} | CLASS: {npc_data['class']} | ALIGN: {npc_data['alignment'][:2].upper()} | BG: {npc_data['background']}
AC: {npc_data['armorClass']} | SPD: {npc_data['speed']}
STATUS: {npc_data['status']} | CONDITION: {npc_data['condition']} | AFFECTED: {', '.join(npc_data['condition_affected'])}
STATS: STR {npc_data['abilities']['strength']}, DEX {npc_data['abilities']['dexterity']}, CON {npc_data['abilities']['constitution']}, INT {npc_data['abilities']['intelligence']}, WIS {npc_data['abilities']['wisdom']}, CHA {npc_data['abilities']['charisma']}
SAVES: {', '.join(npc_data['savingThrows'])}
SKILLS: {', '.join(f"{skill} +{bonus}" for skill, bonus in npc_data['skills'].items())}
PROF BONUS: +{npc_data['proficiencyBonus']}
SENSES: {', '.join(f"{sense} {value}" for sense, value in npc_data['senses'].items())}
LANGUAGES: {', '.join(npc_data['languages'])}
PROF: {', '.join([f"{cat}: {', '.join(items)}" for cat, items in npc_data['proficiencies'].items()])}
VULN: {', '.join(npc_data['damageVulnerabilities'])}
RES: {', '.join(npc_data['damageResistances'])}
IMM: {', '.join(npc_data['damageImmunities'])}
COND IMM: {', '.join(npc_data['conditionImmunities'])}
CLASS FEAT: {', '.join([f"{feature['name']}" for feature in npc_data['classFeatures']])}
RACIAL: {', '.join([f"{trait['name']}" for trait in npc_data['racialTraits']])}
BG FEAT: {bg_feature_name}
FEATS: {', '.join([f"{feat['name']}" for feat in npc_data.get('feats', [])])}
TEMP FX: {', '.join([f"{effect['name']}" for effect in npc_data.get('temporaryEffects', [])])}
EQUIP: {equipment_str}
AMMO: {', '.join([f"{ammo['name']} x{ammo['quantity']}" for ammo in npc_data['ammunition']])}
ATK: {', '.join([f"{atk['name']} ({atk['type']}, {atk['damageDice']} {atk['damageType']})" for atk in npc_data['attacksAndSpellcasting']])}
SPELLCASTING: {npc_data.get('spellcasting', {}).get('ability', 'N/A')} | DC: {npc_data.get('spellcasting', {}).get('spellSaveDC', 'N/A')} | ATK: +{npc_data.get('spellcasting', {}).get('spellAttackBonus', 'N/A')}
SPELLS: {', '.join([f"{level}: {', '.join(spells)}" for level, spells in npc_data.get('spellcasting', {}).get('spells', {}).items() if spells])}
CURRENCY: {npc_data['currency']['gold']}G, {npc_data['currency']['silver']}S, {npc_data['currency']['copper']}C
XP: {npc_data['experience_points']}/{npc_data.get('exp_required_for_next_level', 'N/A')}
TRAITS: {npc_data['personality_traits']}
IDEALS: {npc_data['ideals']}
BONDS: {npc_data['bonds']}
FLAWS: {npc_data['flaws']}
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
    output_file = "chat_history.json"
    
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
        
        print(f"Lightweight chat history updated!")
        print(f"System messages removed: {system_count}")
        print(f"User messages: {user_count}")
        print(f"Assistant messages: {assistant_count}")
        
    except Exception as e:
        print(f"Error generating chat history: {str(e)}")