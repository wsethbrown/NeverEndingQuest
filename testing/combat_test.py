#!/usr/bin/env python3
"""
Combat Test Manager for DungeonMasterAI

A streamlined version specifically designed for testing prompt adherence
using an external prompt file that can be modified separately.
"""

import json
import os
import time
import shutil
import sys
from datetime import datetime
from openai import OpenAI

# Import configuration from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import OPENAI_API_KEY

# Constants
COMBAT_MAIN_MODEL = "gpt-4.1-2025-04-14"  # Full GPT-4.1 model for combat
PLAYER_SIMULATOR_MODEL = "gpt-4.1-mini-2025-04-14"  # Model to simulate player actions
EVALUATION_MODEL = "gpt-4.1-2025-04-14"  # Full GPT-4.1 model for evaluation
TEST_TURNS = 2  # Number of combat turns to simulate

# File paths
DUMMY_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_FILES = {
    "player": os.path.join(DUMMY_DIR, "dummy_player.json"),
    "npc": os.path.join(DUMMY_DIR, "dummy_npc.json"),
    "monster": os.path.join(DUMMY_DIR, "dummy_monster.json"),
    "location": os.path.join(DUMMY_DIR, "dummy_location.json"),
    "encounter": os.path.join(DUMMY_DIR, "dummy_encounter.json"),
    "prompt": os.path.join(DUMMY_DIR, "combat_sim_prompt.txt")
}

# Log directories
LOGS_DIR = os.path.join(DUMMY_DIR, "combat_logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Create combat_logs directory if it doesn't exist
os.makedirs("combat_logs", exist_ok=True)

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Colors for terminal output
SOLID_GREEN = "\033[38;2;0;180;0m"
LIGHT_OFF_GREEN = "\033[38;2;100;180;100m"
SOFT_REDDISH_ORANGE = "\033[38;2;204;102;0m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RESET_COLOR = "\033[0m"

def load_json_file(file_path):
    """Load a JSON file"""
    with open(file_path, "r") as file:
        return json.load(file)

def save_json_file(file_path, data):
    """Save data to a JSON file"""
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)

def generate_prompt_schema(player_stats, npc_stats_list, monster_stats_list, location_info, encounter_data):
    """Generate the combat prompt schema with all character and environment details"""
    try:
        # Read the system prompt template from file
        with open(TEST_FILES["prompt"], "r") as f:
            prompt_template = f.read()
        
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
            
            # Add spells if present (matching your combat_manager.py)
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
        
        # Combine the template with our sections
        # We'll append the sections after the template rather than trying to format them in
        # This is safer and more in line with how you might be doing it in the real system
        return prompt_template + "\n\n" + player_section + "\n\n" + npc_section + "\n\n" + monster_section + "\n\n" + location_section + "\n\n" + encounter_section
        
    except Exception as e:
        print(f"{SOFT_REDDISH_ORANGE}Error generating prompt: {str(e)}{RESET_COLOR}")
        
        # Fallback to a simplified prompt if we can't use the template
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

def format_system_prompt(player_stats, npc_stats_list, monster_stats_list, location_info):
    """Format the system prompt with actual values"""
    
    try:
        # Read the system prompt template from file
        with open(TEST_FILES["prompt"], "r") as f:
            template = f.read()
        
        # Create NPC section
        npc_section = ""
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
                attacks = []
                for action in npc['actions']:
                    if all(k in action for k in ['attackBonus', 'damageDice', 'damageBonus', 'damageType']):
                        attacks.append(f"{action['name']} +{action['attackBonus']} to hit, {action['damageDice']}+{action['damageBonus']} {action['damageType']} damage")
                attacks_str = ", ".join(attacks)
                npc_section += f"Attacks: {attacks_str}\n"
            
            # Add special abilities if present
            if "specialAbilities" in npc:
                abilities_str = ", ".join([ability['name'] for ability in npc['specialAbilities']])
                npc_section += f"Special Abilities: {abilities_str}\n"
            
            npc_section += "\n"
        
        # Create monster section
        monster_section = ""
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
                actions = []
                for action in monster['actions']:
                    if all(k in action for k in ['attackBonus', 'damageDice', 'damageBonus', 'damageType']):
                        actions.append(f"{action['name']} +{action['attackBonus']} to hit, {action['damageDice']}+{action['damageBonus']} {action['damageType']} damage")
                actions_str = ", ".join(actions)
                monster_section += f"Actions: {actions_str}\n"
            
            monster_section += "\n"
        
        # Format player skills
        skills_str = ', '.join([f"{skill} +{bonus}" for skill, bonus in player_stats['skills'].items()])
        
        # Format player attacks
        attacks = []
        for attack in player_stats['attacksAndSpellcasting']:
            if all(k in attack for k in ['attackBonus', 'damageDice', 'damageBonus', 'damageType']):
                attacks.append(f"{attack['name']} +{attack['attackBonus']} to hit, {attack['damageDice']}+{attack['damageBonus']} {attack['damageType']} damage")
        attacks_str = ', '.join(attacks)
        
        # Format player features
        features_str = ', '.join(player_stats['features'])
        
        # Customization dictionary for format string
        custom_values = {
            "location_info.get('name', 'Unknown Location')": location_info.get('name', 'Unknown Location'),
            "location_info.get('description', 'No description available')": location_info.get('description', 'No description available'),
            "player_stats['name']": player_stats['name'],
            "player_stats['class']": player_stats['class'],
            "player_stats['level']": str(player_stats['level']),
            "player_stats['hitPoints']": str(player_stats['hitPoints']),
            "player_stats['maxHitPoints']": str(player_stats['maxHitPoints']),
            "player_stats['armorClass']": str(player_stats['armorClass']),
            "player_stats['abilities']['strength']": str(player_stats['abilities']['strength']),
            "(player_stats['abilities']['strength']-10)//2": str((player_stats['abilities']['strength']-10)//2),
            "player_stats['abilities']['dexterity']": str(player_stats['abilities']['dexterity']),
            "(player_stats['abilities']['dexterity']-10)//2": str((player_stats['abilities']['dexterity']-10)//2),
            "player_stats['abilities']['constitution']": str(player_stats['abilities']['constitution']),
            "(player_stats['abilities']['constitution']-10)//2": str((player_stats['abilities']['constitution']-10)//2),
            "player_stats['abilities']['intelligence']": str(player_stats['abilities']['intelligence']),
            "(player_stats['abilities']['intelligence']-10)//2": str((player_stats['abilities']['intelligence']-10)//2),
            "player_stats['abilities']['wisdom']": str(player_stats['abilities']['wisdom']),
            "(player_stats['abilities']['wisdom']-10)//2": str((player_stats['abilities']['wisdom']-10)//2),
            "player_stats['abilities']['charisma']": str(player_stats['abilities']['charisma']),
            "(player_stats['abilities']['charisma']-10)//2": str((player_stats['abilities']['charisma']-10)//2),
            "', '.join([f\"{skill} +{bonus}\" for skill, bonus in player_stats['skills'].items()])": skills_str,
            "', '.join([f\"{attack['name']} +{attack['attackBonus']} to hit, {attack['damageDice']}+{attack['damageBonus']} {attack['damageType']} damage\" for attack in player_stats['attacksAndSpellcasting'] if 'attackBonus' in attack])": attacks_str,
            "', '.join(player_stats['features'])": features_str,
            "npc_section": npc_section,
            "monster_section": monster_section
        }
        
        # Replace all placeholders in the template
        formatted_prompt = template
        for placeholder, value in custom_values.items():
            formatted_prompt = formatted_prompt.replace(f"{{{placeholder}}}", str(value))
        
        return formatted_prompt
        
    except Exception as e:
        print(f"{SOFT_REDDISH_ORANGE}Error formatting system prompt: {str(e)}{RESET_COLOR}")
        return "Error formatting prompt"

def generate_player_prompt(player_stats, location_info, current_message=None):
    """Generate prompt for the LLM simulating player actions"""
    prompt = f"""You are roleplaying as a player character in a 5e-style combat scenario. 
Your character is named {player_stats['name']}, a level {player_stats['level']} {player_stats['race']} {player_stats['class']}.

You should respond in-character to the Dungeon Master's description of combat and take appropriate actions.
Make tactical decisions based on the situation and your character's abilities.
Keep your responses brief and focused on your combat actions.
Feel free to use creative combat descriptions, but avoid using out-of-character explanations.

Your character has the following abilities:
- HP: {player_stats['hitPoints']}/{player_stats['maxHitPoints']}
- AC: {player_stats['armorClass']}
- Strength: {player_stats['abilities']['strength']} ({(player_stats['abilities']['strength']-10)//2})
- Dexterity: {player_stats['abilities']['dexterity']} ({(player_stats['abilities']['dexterity']-10)//2})
- Constitution: {player_stats['abilities']['constitution']} ({(player_stats['abilities']['constitution']-10)//2})
- Intelligence: {player_stats['abilities']['intelligence']} ({(player_stats['abilities']['intelligence']-10)//2})
- Wisdom: {player_stats['abilities']['wisdom']} ({(player_stats['abilities']['wisdom']-10)//2})
- Charisma: {player_stats['abilities']['charisma']} ({(player_stats['abilities']['charisma']-10)//2})

Your weapons and abilities:
"""
    
    # Add weapons and abilities
    for attack in player_stats['attacksAndSpellcasting']:
        if 'attackBonus' in attack:
            prompt += f"- {attack['name']}: +{attack['attackBonus']} to hit, {attack['damageDice']}+{attack['damageBonus']} {attack['damageType']} damage\n"
        else:
            prompt += f"- {attack['name']}: {attack.get('description', 'No description')}\n"
    
    prompt += "\nYour special features and abilities:\n"
    for feature in player_stats['features']:
        prompt += f"- {feature}\n"
    
    prompt += f"\nYou are currently in: {location_info['name']}\n"
    prompt += f"{location_info['description']}\n\n"
    
    if current_message:
        prompt += f"The DM has just described: {current_message}\n\n"
    
    prompt += """Respond to the DM's description with your character's action. Be creative but practical.
Don't waste time with lengthy explanations - focus on what you want to do.

Example responses:
"I charge at the goblin and attack with my longsword!"
"I'll use my Action Surge to attack twice with my bow, targeting the troll."
"I move behind the boulder for cover and ready my weapon."
"""
    
    return prompt

def generate_evaluation_prompt(conversation_history, player_stats, npc_stats, monster_stats, location_info, test_id):
    """Generate a prompt for the evaluation model to assess prompt adherence"""
    # Get original system prompt
    original_prompt = ""
    for message in conversation_history:
        if message["role"] == "system":
            original_prompt = message["content"]
            break
            
    prompt = f"""You are an expert 5th edition Dungeon Master evaluating an AI-driven combat system's performance.
You will analyze a 2-turn combat transcript between a combat AI (acting as DM) and a player character AI to determine if the combat AI adhered to its requirements.

Test ID: {test_id}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

EVALUATION CRITERIA:
1. Schema Adherence: Did the combat AI use the correct JSON format for its responses?
2. Combat Rules: Did the AI follow the 5e-style combat rules (initiative, attack rolls, damage, etc.)?
3. Narration Quality: Did the AI provide vivid, engaging descriptions of the combat?
4. Tactical Intelligence: Did the AI make logical decisions for NPCs and monsters?
5. Player Interaction: Did the AI give the player clear options and respond appropriately to their actions?
6. Tracking: Did the AI properly track hit points, positions, and combat conditions?
7. Turn Management: Did the AI ONLY ask for player input when it was their character's turn?
8. Inventory & State Updates: Did the AI track inventory changes and provide appropriate commands for updating character states?
9. Dice Roll Handling: Did the AI appropriately handle dice rolls itself rather than asking players to roll?
10. Action Implementation: Did the AI use the correct "action" commands (updatePlayerInfo, updateNPCInfo, etc.) when updating game state?
11. Immersion: Did the AI maintain the fantasy world's atmosphere and immersion?

THE COMBAT SETTING:
Location: {location_info['name']}
{location_info['description']}

COMBATANTS:
Player: {player_stats['name']}, Level {player_stats['level']} {player_stats['race']} {player_stats['class']}
NPC Ally: {npc_stats['name']}, Level {npc_stats['level']} {npc_stats['race']} {npc_stats['class']}
Monster: {monster_stats['name']}, {monster_stats['size']} {monster_stats['type']}

ORIGINAL SYSTEM PROMPT (What the AI was instructed to do):
```
{original_prompt[:1000]}...
[System prompt truncated for brevity]
```

KEY EXPECTATIONS FOR THE COMBAT AI:
1. The AI should act as Dungeon Master, managing all game state and dice rolls
2. The AI should ONLY ask for player input when it's their character's turn
3. The AI should properly track and display HP, conditions, and resources for all combatants
4. The AI should use realistic monster tactics based on their abilities and intelligence
5. The AI should use the correct JSON schema for all responses and game actions
6. The AI should calculate and apply damage, handle initiative order, and manage combat rules
7. For state changes, the AI should use the proper "action" commands in its JSON output

COMBAT TRANSCRIPT:
"""

    # Add the conversation history
    for message in conversation_history:
        role = message["role"]
        content = message["content"]
        
        # Skip system messages for brevity
        if role == "system":
            continue
            
        prompt += f"{role.upper()}: {content}\n\n"

    # Add evaluation instructions
    prompt += """
EVALUATION FORMAT:
Provide your evaluation in the following JSON format:

```json
{
  "schemaAdherence": {
    "score": 1-10,
    "comments": "Detailed observations about the AI's format adherence"
  },
  "combatRules": {
    "score": 1-10,
    "comments": "Observations about rules implementation"
  },
  "narrationQuality": {
    "score": 1-10,
    "comments": "Assessment of the descriptive quality"
  },
  "tacticalIntelligence": {
    "score": 1-10,
    "comments": "Evaluation of NPC/monster decision-making"
  },
  "playerInteraction": {
    "score": 1-10,
    "comments": "How well the AI handled player actions"
  },
  "tracking": {
    "score": 1-10,
    "comments": "Evaluation of state tracking"
  },
  "turnManagement": {
    "score": 1-10,
    "comments": "Did the AI only ask for player input on their turn"
  },
  "inventoryStateUpdates": {
    "score": 1-10,
    "comments": "How well the AI tracked inventory and state changes"
  },
  "diceRollHandling": {
    "score": 1-10,
    "comments": "Did the AI handle dice rolls appropriately"
  },
  "actionImplementation": {
    "score": 1-10,
    "comments": "Did the AI use the correct action commands"
  },
  "immersion": {
    "score": 1-10,
    "comments": "Assessment of world-building and atmosphere"
  },
  "overallScore": 1-10,
  "strengths": [
    "Key strength 1",
    "Key strength 2",
    "..."
  ],
  "weaknesses": [
    "Key weakness 1",
    "Key weakness 2",
    "..."
  ],
  "recommendedPromptImprovements": [
    "Specific recommendation 1",
    "Specific recommendation 2",
    "..."
  ],
  "summary": "A concise 2-3 sentence summary of the overall evaluation"
}
```

Be thorough and specific in your evaluation, citing examples from the transcript.
Focus on how the combat AI could be improved through better prompting or instruction.
For each criteria, provide evidence from the transcript to support your score and comments.
"""

    return prompt

def validate_response(response):
    """
    Validate the AI's response against key requirements

    Returns:
        tuple: (is_valid, issues_list)
    """
    issues = []

    # Extract JSON from response
    json_response = extract_json_from_message(response)
    if not json_response:
        issues.append("Response does not contain valid JSON")
        return False, issues

    # Check for required fields
    if "narration" not in json_response:
        issues.append("Missing 'narration' field in JSON")

    if "actions" not in json_response:
        issues.append("Missing 'actions' field in JSON")

    # Check if asking player to roll dice
    narration = json_response.get("narration", "").lower()
    dice_request_phrases = [
        "roll a d", "roll the d", "roll your d",
        "roll for", "roll your attack", "roll your damage",
        "roll d", "roll 1d", "roll 2d", "roll your dice",
        "please roll", "roll and add", "make a roll",
        "roll to attack", "roll to hit", "give me a roll",
        "provide your roll", "tell me your roll", "roll now"
    ]

    for phrase in dice_request_phrases:
        if phrase in narration:
            issues.append(f"Asked player to roll dice: '{phrase}'")

    # Check for player-facing questions about rolls
    question_phrases = ["what did you roll", "what's your roll", "what is your roll",
                         "your roll result", "result of your roll", "your dice roll"]

    for phrase in question_phrases:
        if phrase in narration:
            issues.append(f"Asked player about roll results: '{phrase}'")

    # Check for proper action implementation when required
    damage_indicators = ["hp", "hit point", "damage", "health", "injured", "wound", "hurt",
                          "slashes", "hits", "strikes", "pierces", "blood", "pain"]

    has_damage_narration = any(indicator in narration.lower() for indicator in damage_indicators)

    if has_damage_narration:
        has_update_action = False
        for action in json_response.get("actions", []):
            if action.get("action") in ["updatePlayerInfo", "updateNPCInfo", "updateEncounter"]:
                has_update_action = True
                break

        if not has_update_action:
            issues.append("Narrated damage or combat effects without corresponding action update")

    return len(issues) == 0, issues

def generate_correction_prompt(original_response, issues):
    """Generate a prompt to correct issues in the response"""
    correction = f"""Your previous response had the following issues that need to be fixed:

{chr(10).join(f"- {issue}" for issue in issues)}

Please correct your response based on these key requirements:

1. NEVER ask the player to roll dice. YOU must roll all dice for the player character, NPCs, and monsters.
2. Provide complete and descriptive combat narration including all dice rolls and their results.
3. Use appropriate action commands (updatePlayerInfo, updateNPCInfo, updateEncounter) for ALL state changes.
4. Structure JSON properly with narration and actions fields.

Your original response:
{original_response}

Please provide a corrected response that follows ALL requirements.
"""
    return correction

def get_validated_response(conversation_history, max_attempts=2):
    """
    Get a response from the AI and validate it against requirements.
    If validation fails, send correction prompt and try again.

    Args:
        conversation_history: The current conversation history
        max_attempts: Maximum number of validation attempts

    Returns:
        str: The final (hopefully valid) response
    """
    attempts = 0
    while attempts < max_attempts:
        # Get response from model
        ai_response = client.chat.completions.create(
            model=COMBAT_MAIN_MODEL,
            temperature=1.0,
            messages=[msg for msg in conversation_history]
        )
        response = ai_response.choices[0].message.content

        # Validate response
        is_valid, issues = validate_response(response)
        if is_valid:
            return response

        # If not valid and we have attempts left, try correction
        attempts += 1
        if attempts < max_attempts:
            print(f"{SOFT_REDDISH_ORANGE}Response validation failed. Issues:{RESET_COLOR}")
            for issue in issues:
                print(f"- {issue}")
            print(f"{YELLOW}Sending correction prompt (attempt {attempts+1}/{max_attempts})...{RESET_COLOR}")

            # Create correction messages
            correction_prompt = generate_correction_prompt(response, issues)
            correction_messages = [msg for msg in conversation_history]
            correction_messages.append({"role": "assistant", "content": response})
            correction_messages.append({"role": "user", "content": correction_prompt})

            # Get corrected response
            correction_response = client.chat.completions.create(
                model=COMBAT_MAIN_MODEL,
                temperature=1.0,
                messages=correction_messages
            )
            response = correction_response.choices[0].message.content

    # Return the last response even if not valid (after max attempts)
    if not is_valid:
        print(f"{SOFT_REDDISH_ORANGE}Warning: Returning response that failed validation after {max_attempts} attempts.{RESET_COLOR}")

    return response

def extract_json_from_message(message):
    """Extract JSON from a message that might contain it in a code block or as plain text"""
    try:
        # Check if the message is already a JSON string
        json_obj = json.loads(message)
        return json_obj
    except json.JSONDecodeError:
        # Try to extract JSON from a code block in the message
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', message)
        if json_match:
            try:
                json_obj = json.loads(json_match.group(1))
                return json_obj
            except json.JSONDecodeError:
                pass
        
        # Try to extract JSON based on opening and closing braces
        json_match = re.search(r'({[\s\S]*})', message)
        if json_match:
            try:
                json_obj = json.loads(json_match.group(1))
                return json_obj
            except json.JSONDecodeError:
                pass
    
    return None

def save_test_results(test_id, conversation_history, evaluation_results):
    """Save test results to the logs directory"""
    test_dir = os.path.join(LOGS_DIR, test_id)
    os.makedirs(test_dir, exist_ok=True)
    
    # Save conversation history
    conversation_file = os.path.join(test_dir, "conversation.json")
    save_json_file(conversation_file, conversation_history)
    
    # Save evaluation results
    evaluation_file = os.path.join(test_dir, "evaluation.json")
    save_json_file(evaluation_file, evaluation_results)
    
    # Save a copy of the system prompt used
    system_prompt = ""
    for message in conversation_history:
        if message["role"] == "system":
            system_prompt = message["content"]
            break
    
    if system_prompt:
        prompt_file = os.path.join(test_dir, "system_prompt.txt")
        with open(prompt_file, "w") as f:
            f.write(system_prompt)
    
    # Create a human-readable summary
    summary_file = os.path.join(test_dir, "summary.md")
    with open(summary_file, "w") as f:
        f.write(f"# Combat Test Summary: {test_id}\n\n")
        f.write(f"Test conducted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Conversation Transcript\n\n")
        for message in conversation_history:
            role = message["role"]
            content = message["content"]
            
            # Skip system messages
            if role == "system":
                continue
                
            f.write(f"### {role.upper()}:\n")
            f.write(f"{content}\n\n")
        
        f.write("## Evaluation Results\n\n")
        if isinstance(evaluation_results, dict):
            # Write overall scores
            f.write("### Scores\n\n")
            f.write("| Category | Score | Comments |\n")
            f.write("|----------|-------|----------|\n")
            for category in ["schemaAdherence", "combatRules", "narrationQuality", 
                           "tacticalIntelligence", "playerInteraction", "tracking", 
                           "turnManagement", "inventoryStateUpdates", "diceRollHandling", 
                           "actionImplementation", "immersion"]:
                if category in evaluation_results:
                    score = evaluation_results[category].get("score", "N/A")
                    comments = evaluation_results[category].get("comments", "N/A")
                    f.write(f"| {category} | {score} | {comments} |\n")
            
            f.write(f"\n**Overall Score**: {evaluation_results.get('overallScore', 'N/A')}\n\n")
            
            # Write strengths and weaknesses
            f.write("### Strengths\n\n")
            for strength in evaluation_results.get("strengths", []):
                f.write(f"- {strength}\n")
            
            f.write("\n### Weaknesses\n\n")
            for weakness in evaluation_results.get("weaknesses", []):
                f.write(f"- {weakness}\n")
            
            f.write("\n### Recommended Prompt Improvements\n\n")
            for recommendation in evaluation_results.get("recommendedPromptImprovements", []):
                f.write(f"- {recommendation}\n")
            
            f.write("\n### Summary\n\n")
            f.write(f"{evaluation_results.get('summary', 'No summary provided.')}\n")
    
    print(f"{CYAN}Test results saved to: {test_dir}{RESET_COLOR}")
    return test_dir

def generate_chat_history(conversation_history, encounter_id):
    """
    Generate a lightweight combat chat history without system messages
    for a specific encounter ID
    """
    # Create a formatted timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create directory for this encounter if it doesn't exist
    encounter_dir = f"combat_logs/{encounter_id}"
    os.makedirs(encounter_dir, exist_ok=True)
    
    # Create a unique filename based on encounter ID and timestamp
    output_file = f"{encounter_dir}/combat_chat_{timestamp}.json"
    
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
        
        print(f"\n{SOFT_REDDISH_ORANGE}Combat chat history updated!{RESET_COLOR}")
        print(f"Encounter ID: {encounter_id}")
        print(f"System messages removed: {system_count}")
        print(f"User messages: {user_count}")
        print(f"Assistant messages: {assistant_count}")
        print(f"Total messages (including system): {total_count}")
        print(f"Output saved to: {output_file}")
        
        # Also create/update the latest version of this encounter for easy reference
        latest_file = f"{encounter_dir}/combat_chat_latest.json"
        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump(chat_history, f, indent=2)
        print(f"Latest version also saved to: {latest_file}\n")
        
    except Exception as e:
        print(f"Error generating combat chat history: {str(e)}")

def run_combat_test():
    """Run a controlled combat test and evaluate the results"""
    print(f"{SOLID_GREEN}Starting Combat Test Manager{RESET_COLOR}")
    print("Loading test data...")
    
    # Load test data
    player_stats = load_json_file(TEST_FILES["player"])
    npc_stats = load_json_file(TEST_FILES["npc"])
    monster_stats = load_json_file(TEST_FILES["monster"])
    location_info = load_json_file(TEST_FILES["location"])
    encounter_data = load_json_file(TEST_FILES["encounter"])
    
    # Generate a unique test ID
    test_id = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    print(f"Test ID: {test_id}")
    
    # Initialize conversation history
    conversation_history = []
    
    # Add initial system prompt using the encounter data
    combat_prompt = generate_prompt_schema(
        player_stats, 
        [npc_stats], 
        [monster_stats], 
        location_info,
        encounter_data
    )
    
    if combat_prompt == "Error formatting prompt":
        print(f"{SOFT_REDDISH_ORANGE}Failed to format system prompt. Aborting test.{RESET_COLOR}")
        return
    
    conversation_history.append({"role": "system", "content": combat_prompt})
    
    # Start combat - get initial narration from combat AI
    print(f"{YELLOW}Initializing combat with {COMBAT_MAIN_MODEL}...{RESET_COLOR}")

    # Initial message with validation
    initial_messages = [{"role": "system", "content": combat_prompt}]
    ai_message = get_validated_response(initial_messages)
    conversation_history.append({"role": "assistant", "content": ai_message})
    
    # Display the narration
    json_response = extract_json_from_message(ai_message)
    if json_response and "narration" in json_response:
        print(f"\n{CYAN}Dungeon Master:{RESET_COLOR} {json_response['narration']}")
    else:
        print(f"\n{CYAN}Dungeon Master:{RESET_COLOR} {ai_message}")
    
    # Combat loop for specified number of turns
    turn_count = 0
    while turn_count < TEST_TURNS:
        turn_count += 1
        print(f"\n{SOLID_GREEN}--- TURN {turn_count} ---{RESET_COLOR}")
        
        # Get player action from player simulator
        print(f"{YELLOW}Getting player action from {PLAYER_SIMULATOR_MODEL}...{RESET_COLOR}")
        player_prompt = generate_player_prompt(player_stats, location_info, ai_message)
        player_response = client.chat.completions.create(
            model=PLAYER_SIMULATOR_MODEL,
            temperature=0.7,
            messages=[{"role": "system", "content": player_prompt}]
        )
        player_message = player_response.choices[0].message.content
        conversation_history.append({"role": "user", "content": player_message})
        
        # Display player action
        print(f"\n{YELLOW}{player_stats['name']}:{RESET_COLOR} {player_message}")
        
        # Get combat AI response
        print(f"{YELLOW}Getting combat response from {COMBAT_MAIN_MODEL}...{RESET_COLOR}")

        # Get response with validation and potential correction
        ai_message = get_validated_response(conversation_history)
        conversation_history.append({"role": "assistant", "content": ai_message})
        
        # Display the combat AI response
        json_response = extract_json_from_message(ai_message)
        if json_response and "narration" in json_response:
            print(f"\n{CYAN}Dungeon Master:{RESET_COLOR} {json_response['narration']}")
            
            # Check if combat is concluded
            if "actions" in json_response and any(action.get("action") == "exit" for action in json_response["actions"]):
                print(f"\n{SOFT_REDDISH_ORANGE}Combat concluded early.{RESET_COLOR}")
                break
        else:
            print(f"\n{CYAN}Dungeon Master:{RESET_COLOR} {ai_message}")
    
    # Save chat history in the standard format
    generate_chat_history(conversation_history, encounter_data["encounterId"])
    
    # Evaluate the test results
    print(f"\n{SOLID_GREEN}--- EVALUATING COMBAT TEST ---{RESET_COLOR}")
    print(f"{YELLOW}Getting evaluation from {EVALUATION_MODEL}...{RESET_COLOR}")
    
    evaluation_prompt = generate_evaluation_prompt(
        conversation_history,
        player_stats,
        npc_stats,
        monster_stats,
        location_info,
        test_id
    )
    
    evaluation_response = client.chat.completions.create(
        model=EVALUATION_MODEL,
        temperature=0.3,
        messages=[{"role": "system", "content": evaluation_prompt}]
    )
    evaluation_message = evaluation_response.choices[0].message.content
    
    # Extract evaluation JSON
    evaluation_results = extract_json_from_message(evaluation_message)
    if not evaluation_results:
        print(f"{SOFT_REDDISH_ORANGE}Warning: Could not extract JSON from evaluation results.{RESET_COLOR}")
        evaluation_results = {"error": "Could not parse evaluation results", "raw": evaluation_message}
    
    # Save test results
    results_dir = save_test_results(test_id, conversation_history, evaluation_results)
    
    # Print summary of evaluation
    print(f"\n{SOLID_GREEN}--- EVALUATION SUMMARY ---{RESET_COLOR}")
    if isinstance(evaluation_results, dict) and "overallScore" in evaluation_results:
        print(f"Overall Score: {evaluation_results['overallScore']}/10")

        # Print key category scores
        print("\nCategory Scores:")
        for category in ["schemaAdherence", "combatRules", "turnManagement", 
                       "inventoryStateUpdates", "diceRollHandling", "actionImplementation"]:
            if category in evaluation_results:
                score = evaluation_results[category].get("score", "N/A")
                print(f"- {category}: {score}/10")
        
        print("\nStrengths:")
        for strength in evaluation_results.get("strengths", []):
            print(f"- {strength}")
        
        print("\nWeaknesses:")
        for weakness in evaluation_results.get("weaknesses", []):
            print(f"- {weakness}")
        
        print("\nRecommended Prompt Improvements:")
        for recommendation in evaluation_results.get("recommendedPromptImprovements", []):
            print(f"- {recommendation}")
        
        print(f"\nSummary: {evaluation_results.get('summary', 'No summary provided.')}")
    else:
        print(f"Error: Could not extract structured evaluation. See {results_dir}/evaluation.json for details.")
    
    print(f"\n{SOLID_GREEN}Test completed. Results saved to: {results_dir}{RESET_COLOR}")

if __name__ == "__main__":
    run_combat_test()