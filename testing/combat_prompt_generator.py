"""
Combat Prompt Generator for DungeonMasterAI

This module handles the generation of system prompts for combat simulations,
keeping the prompt generation logic separate from the test script.
"""

def generate_prompt_schema(player_stats, npc_stats_list, monster_stats_list, location_info, encounter_data):
    """Generate the combat prompt schema with all character and environment details"""
    try:
        # Add Player Character section
        player_section = f"""
Player Character:
Name: {player_stats['name']}
Class: {player_stats['class']}
Level: {player_stats['level']}
HP: {player_stats['hitPoints']}/{player_stats['maxHitPoints']}
AC: {player_stats['armorClass']}
STR: {player_stats['abilities']['strength']} ({(player_stats['abilities']['strength']-10)//2})
DEX: {player_stats['abilities']['dexterity']} ({(player_stats['abilities']['dexterity']-10)//2})
CON: {player_stats['abilities']['constitution']} ({(player_stats['abilities']['constitution']-10)//2})
INT: {player_stats['abilities']['intelligence']} ({(player_stats['abilities']['intelligence']-10)//2})
WIS: {player_stats['abilities']['wisdom']} ({(player_stats['abilities']['wisdom']-10)//2})
CHA: {player_stats['abilities']['charisma']} ({(player_stats['abilities']['charisma']-10)//2})
Skills: {', '.join([f"{skill} +{bonus}" for skill, bonus in player_stats['skills'].items()])} 
Attacks: {', '.join([f"{attack['name']} +{attack['attackBonus']} to hit, {attack['damageDice']}+{attack['damageBonus']} {attack['damageType']} damage" for attack in player_stats['attacksAndSpellcasting'] if all(k in attack for k in ['attackBonus', 'damageDice', 'damageBonus', 'damageType'])])}
Features: {', '.join(player_stats['features'])}
"""
        
        # Add NPCs section
        npc_section = "NPC TEMPLATES:\n"
        for npc in npc_stats_list:
            npc_section += f"Name: {npc['name']}\n"
            npc_section += f"Race: {npc['race']}\n"
            npc_section += f"Class: {npc['class']}\n"
            npc_section += f"Level: {npc['level']}\n"
            npc_section += f"HP: {npc['hitPoints']}/{npc['maxHitPoints']}\n"
            npc_section += f"AC: {npc['armorClass']}\n"
            npc_section += f"STR: {npc['abilities']['strength']} ({(npc['abilities']['strength']-10)//2})\n"
            npc_section += f"DEX: {npc['abilities']['dexterity']} ({(npc['abilities']['dexterity']-10)//2})\n"
            npc_section += f"CON: {npc['abilities']['constitution']} ({(npc['abilities']['constitution']-10)//2})\n"
            npc_section += f"INT: {npc['abilities']['intelligence']} ({(npc['abilities']['intelligence']-10)//2})\n"
            npc_section += f"WIS: {npc['abilities']['wisdom']} ({(npc['abilities']['wisdom']-10)//2})\n"
            npc_section += f"CHA: {npc['abilities']['charisma']} ({(npc['abilities']['charisma']-10)//2})\n"
            
            # Add skills if present
            if "skills" in npc:
                skills_str = ", ".join([f"{skill} +{bonus}" for skill, bonus in npc['skills'].items()])
                npc_section += f"Skills: {skills_str}\n"
            
            # Add attacks if present
            if "actions" in npc:
                valid_actions = []
                for action in npc['actions']:
                    if all(key in action for key in ['attackBonus', 'damageDice', 'damageBonus', 'damageType']):
                        valid_actions.append(f"{action['name']} +{action['attackBonus']} to hit, {action['damageDice']}+{action['damageBonus']} {action['damageType']} damage")
                
                if valid_actions:
                    attacks_str = ", ".join(valid_actions)
                    npc_section += f"Attacks: {attacks_str}\n"
            
            # Add special abilities if present
            if "specialAbilities" in npc:
                abilities_str = ", ".join([ability['name'] for ability in npc['specialAbilities']])
                npc_section += f"Special Abilities: {abilities_str}\n"
            
            # Add spells if present
            if "spellcasting" in npc and npc["spellcasting"].get("ability", ""):
                spells = npc["spellcasting"].get("spells", {})
                spell_list = []
                for level, level_spells in spells.items():
                    if level_spells:
                        spell_list.extend(level_spells)
                if spell_list:
                    npc_section += f"Spells: {', '.join(spell_list)}\n"
            
            npc_section += "\n"
        
        # Add monsters section
        monster_section = "MONSTER TEMPLATES:\n"
        for monster in monster_stats_list:
            monster_section += f"Name: {monster['name']}\n"
            monster_section += f"Type: {monster['type']}\n"
            monster_section += f"Size: {monster['size']}\n"
            monster_section += f"HP: {monster['hitPoints']}/{monster['maxHitPoints']}\n"
            monster_section += f"AC: {monster['armorClass']}\n"
            monster_section += f"STR: {monster['abilities']['strength']} ({(monster['abilities']['strength']-10)//2})\n"
            monster_section += f"DEX: {monster['abilities']['dexterity']} ({(monster['abilities']['dexterity']-10)//2})\n"
            monster_section += f"CON: {monster['abilities']['constitution']} ({(monster['abilities']['constitution']-10)//2})\n"
            monster_section += f"INT: {monster['abilities']['intelligence']} ({(monster['abilities']['intelligence']-10)//2})\n"
            monster_section += f"WIS: {monster['abilities']['wisdom']} ({(monster['abilities']['wisdom']-10)//2})\n"
            monster_section += f"CHA: {monster['abilities']['charisma']} ({(monster['abilities']['charisma']-10)//2})\n"
            
            # Add special abilities if present
            if "specialAbilities" in monster:
                abilities_str = ", ".join([ability['name'] for ability in monster['specialAbilities']])
                monster_section += f"Special Abilities: {abilities_str}\n"
            
            # Add actions if present
            if "actions" in monster:
                valid_actions = []
                for action in monster['actions']:
                    if all(key in action for key in ['attackBonus', 'damageDice', 'damageBonus', 'damageType']):
                        valid_actions.append(f"{action['name']} +{action['attackBonus']} to hit, {action['damageDice']}+{action['damageBonus']} {action['damageType']} damage")
                
                if valid_actions:
                    actions_str = ", ".join(valid_actions)
                    monster_section += f"Actions: {actions_str}\n"
            
            monster_section += "\n"
        
        # Add location section
        location_section = f"""
LOCATION:
Name: {location_info.get('name', 'Unknown Location')}
Description: {location_info.get('description', 'No description available')}
"""
        
        if "details" in location_info:
            location_section += "Details:\n"
            for key, value in location_info["details"].items():
                if isinstance(value, list):
                    value_str = ", ".join(value)
                    location_section += f"- {key.capitalize()}: {value_str}\n"
                else:
                    location_section += f"- {key.capitalize()}: {value}\n"
        
        # Add encounter section
        encounter_section = f"""
ENCOUNTER DETAILS:
Encounter ID: {encounter_data.get('encounterId', 'Unknown')}
Name: {encounter_data.get('name', 'Unknown Encounter')}
Description: {encounter_data.get('description', 'No description available')}
Difficulty: {encounter_data.get('difficultyLevel', 'Unknown')}
"""
        
        if "environment" in encounter_data:
            encounter_section += "Environment:\n"
            for key, value in encounter_data["environment"].items():
                if isinstance(value, list):
                    encounter_section += f"- {key.capitalize()}:\n"
                    for item in value:
                        if isinstance(item, dict):
                            encounter_section += f"  * {item.get('description', 'Unknown')}\n"
                        else:
                            encounter_section += f"  * {item}\n"
                else:
                    encounter_section += f"- {key.capitalize()}: {value}\n"
        
        if "objectives" in encounter_data:
            encounter_section += "Objectives:\n"
            for key, value in encounter_data["objectives"].items():
                encounter_section += f"- {key.capitalize()}: {value}\n"
        
        if "notes" in encounter_data:
            encounter_section += f"Notes: {encounter_data['notes']}\n"
        
        return player_section, npc_section, monster_section, location_section, encounter_section
        
    except Exception as e:
        print(f"Error generating prompt sections: {str(e)}")
        return None

def generate_fallback_prompt(player_stats, npc_stats_list, monster_stats_list, location_info, encounter_data):
    """Generate a simplified fallback prompt if the main prompt generation fails"""
    return f"""You are a Dungeon Master controlling combat in a role-playing game.

The combat is taking place in: {location_info.get('name', 'Unknown Location')}

Player Character:
Name: {player_stats['name']}
Class: {player_stats['class']}
Level: {player_stats['level']}
HP: {player_stats['hitPoints']}/{player_stats['maxHitPoints']}
AC: {player_stats['armorClass']}

Monster:
Name: {monster_stats_list[0]['name'] if monster_stats_list else 'Unknown Monster'}
HP: {monster_stats_list[0]['hitPoints'] if monster_stats_list else 'Unknown'}/{monster_stats_list[0]['maxHitPoints'] if monster_stats_list else 'Unknown'}
AC: {monster_stats_list[0]['armorClass'] if monster_stats_list else 'Unknown'}

NPC:
Name: {npc_stats_list[0]['name'] if npc_stats_list else 'Unknown NPC'}
Class: {npc_stats_list[0]['class'] if npc_stats_list else 'Unknown'}
HP: {npc_stats_list[0]['hitPoints'] if npc_stats_list else 'Unknown'}/{npc_stats_list[0]['maxHitPoints'] if npc_stats_list else 'Unknown'}

Encounter ID: {encounter_data.get('encounterId', 'Unknown')}

Output Format: Use JSON for all responses. Include narration and actions fields.
"""

def create_full_prompt(prompt_template_path, player_stats, npc_stats_list, monster_stats_list, location_info, encounter_data):
    """Create the full system prompt by combining template with generated sections"""
    try:
        # Read the system prompt template from file
        with open(prompt_template_path, "r") as f:
            prompt_template = f.read()
        
        # Generate all prompt sections
        sections = generate_prompt_schema(player_stats, npc_stats_list, monster_stats_list, location_info, encounter_data)
        
        if sections:
            player_section, npc_section, monster_section, location_section, encounter_section = sections
            # Combine the template with our sections
            return prompt_template + "\n\n" + player_section + "\n\n" + npc_section + "\n\n" + monster_section + "\n\n" + location_section + "\n\n" + encounter_section
        else:
            # Use fallback prompt if section generation failed
            return generate_fallback_prompt(player_stats, npc_stats_list, monster_stats_list, location_info, encounter_data)
        
    except Exception as e:
        print(f"Error creating full prompt: {str(e)}")
        return generate_fallback_prompt(player_stats, npc_stats_list, monster_stats_list, location_info, encounter_data)