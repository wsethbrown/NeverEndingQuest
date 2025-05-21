import json
from campaign_path_manager import CampaignPathManager

def compress_json_data(data):
    """Compress JSON data by removing unnecessary whitespace."""
    return json.dumps(data, separators=(',', ':'))

def load_json_data(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return compress_json_data(data)
    except FileNotFoundError:
        print(f"{file_path} not found. Returning None.")
        return None
    except json.JSONDecodeError:
        print(f"{file_path} has an invalid JSON format. Returning None.")
        return None

def update_conversation_history(conversation_history, party_tracker_data, plot_data, campaign_data):
    # Read the actual system prompt to get the proper identifier
    with open("system_prompt.txt", "r") as file:
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

    # Remove any existing system messages for location, party tracker, plot, map, and campaign data
    updated_history = [
        msg for msg in conversation_history 
        if not (msg["role"] == "system" and 
                any(key in msg["content"] for key in [
                    "Current Location:", 
                    "No active location data available",
                    "Here's the updated party tracker data:",
                    "Here's the current plot data:",
                    "Here's the current map data:",
                    "Here's the campaign data:"
                ]))
    ]

    # Create a new list starting with the primary system prompt
    new_history = [primary_system_prompt] if primary_system_prompt else []

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
        path_manager = CampaignPathManager()
        map_file = path_manager.get_map_path(current_area_id)
        map_data = load_json_data(map_file)
        if map_data:
            map_message = "Here's the current map data:\n"
            map_message += f"{map_data}\n"
            new_history.append({"role": "system", "content": map_message})

    # Load the area-specific JSON file
    if current_area_id:
        path_manager = CampaignPathManager()
        area_file = path_manager.get_area_path(current_area_id)
        try:
            with open(area_file, 'r') as file:
                location_data = json.load(file)
        except FileNotFoundError:
            print(f"{area_file} not found. Skipping location data.")
            location_data = None
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
        path_manager = CampaignPathManager()
        
        # Process player characters
        for member in party_tracker_data["partyMembers"]:
            name = member.lower()
            member_file = path_manager.get_player_path(member)
            try:
                with open(member_file, "r") as file:
                    member_data = json.load(file)
                    
                    # Format equipment list with quantities
                    equipment_list = []
                    for item in member_data['equipment']:
                        item_description = f"{item['item_name']} ({item['item_type']})"
                        if item['quantity'] > 1:
                            item_description = f"{item_description} x{item['quantity']}"
                        equipment_list.append(item_description)
                    
                    equipment_str = ", ".join(equipment_list)

                    # Format character data
                    formatted_data = f"""
CHAR: {member_data['name']}
TYPE: {member_data['character_type'].capitalize()} | LVL: {member_data['level']} | RACE: {member_data['race']} | CLASS: {member_data['class']} | ALIGN: {member_data['alignment'][:2].upper()} | BG: {member_data['background']}
HP: {member_data['hitPoints']}/{member_data['maxHitPoints']} | AC: {member_data['armorClass']} | INIT: {member_data['initiative']} | SPD: {member_data['speed']}
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
FEAT: {', '.join(member_data['features'])}
SPECIAL: {', '.join([f"{ability['name']}" for ability in member_data['specialAbilities']])}
CLASS FEAT: {', '.join([f"{feature['name']}" for feature in member_data['classFeatures']])}
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
            npc_file = path_manager.get_npc_path(npc_name)
            try:
                with open(npc_file, "r") as file:
                    npc_data = json.load(file)
                    
                    # Format equipment list with quantities
                    equipment_list = []
                    for item in npc_data['equipment']:
                        item_description = f"{item['item_name']} ({item['item_type']})"
                        if item['quantity'] > 1:
                            item_description = f"{item_description} x{item['quantity']}"
                        equipment_list.append(item_description)
                    
                    equipment_str = ", ".join(equipment_list)

                    # Format NPC data
                    formatted_data = f"""
NPC: {npc_data['name']}
ROLE: {npc['role']} | SIZE: {npc_data['size']} | TYPE: {npc_data['type']} | RACE: {npc_data['race']} | CLASS: {npc_data['class']} | LVL: {npc_data['level']} | ALIGN: {npc_data['alignment']}
HP: {npc_data['hitPoints']}/{npc_data['maxHitPoints']} | AC: {npc_data['armorClass']} | SPD: {npc_data['speed']} | INIT: {npc_data['initiative']}
STATUS: {npc_data['status']} | CONDITION: {npc_data['condition']} | AFFECTED: {', '.join(npc_data['condition_affected'])}
STATS: STR {npc_data['abilities']['strength']}, DEX {npc_data['abilities']['dexterity']}, CON {npc_data['abilities']['constitution']}, INT {npc_data['abilities']['intelligence']}, WIS {npc_data['abilities']['wisdom']}, CHA {npc_data['abilities']['charisma']}
SAVES: {', '.join(npc_data['savingThrows'])}
SKILLS: {', '.join(f"{skill} +{bonus}" for skill, bonus in npc_data['skills'].items())}
PROF: {', '.join([f"{cat}: {', '.join(items)}" for cat, items in npc_data['proficiencies'].items()])}
VULN: {', '.join(npc_data['damageVulnerabilities'])}
RES: {', '.join(npc_data['damageResistances'])}
IMM: {', '.join(npc_data['damageImmunities'])}
COND IMM: {', '.join(npc_data['conditionImmunities'])}
SENSES: {', '.join(f"{sense} {value}" for sense, value in npc_data['senses'].items())}
LANGUAGES: {npc_data['languages']}
CR: {npc_data['challengeRating']} | PROF BONUS: +{npc_data['proficiencyBonus']}
ABILITIES: {', '.join(ability['name'] for ability in npc_data['specialAbilities'])}
ACTIONS: {', '.join(action['name'] for action in npc_data['actions'])}
EQUIP: {equipment_str}
AMMO: {', '.join([f"{ammo['name']} x{ammo['quantity']}" for ammo in npc_data['ammunition']])}
ATK: {', '.join([f"{atk['name']} ({atk['type']}, {atk['damage']})" for atk in npc_data.get('attacksAndSpellcasting', [])])}
SPELLCASTING: {npc_data.get('spellcasting', {}).get('ability', 'N/A')} | DC: {npc_data.get('spellcasting', {}).get('spellSaveDC', 'N/A')} | ATK: +{npc_data.get('spellcasting', {}).get('spellAttackBonus', 'N/A')}
SPELLS: {', '.join([f"{level}: {', '.join(spells)}" for level, spells in npc_data.get('spellcasting', {}).get('spells', {}).items() if spells])}
FEATURES: {', '.join([feature['name'] for feature in npc_data.get('classFeatures', [])])}
BG: {npc_data['background']}
PERSONALITY: {npc_data['personality']}
IDEALS: {npc_data['ideals']}
BONDS: {npc_data['bonds']}
FLAWS: {npc_data['flaws']}
XP: {npc_data.get('experience_points', 'N/A')}/{npc_data.get('exp_required_for_next_level', 'N/A')}
CURRENCY: {npc_data['currency']['gold']}G, {npc_data['currency']['silver']}S, {npc_data['currency']['copper']}C
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