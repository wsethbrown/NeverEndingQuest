#!/usr/bin/env python3
"""
Simplified Combat Test Manager for DungeonMasterAI

This version avoids importing the original combat_manager.py and uses its own
prompt generation logic to ensure compatibility.
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
COMBAT_MAIN_MODEL = "gpt-4.1-mini-2025-04-14"  # Model to test
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
    "encounter": os.path.join(DUMMY_DIR, "dummy_encounter.json")
}

# Log directories
LOGS_DIR = os.path.join(DUMMY_DIR, "combat_logs")
os.makedirs(LOGS_DIR, exist_ok=True)

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

def read_system_prompt():
    """Read the original system prompt from the combat_manager.py file"""
    try:
        manager_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'combat_manager.py'))
        with open(manager_path, 'r') as f:
            content = f.read()
            # Look for the generate_prompt_schema function and extract the prompt template
            start_marker = 'prompt = f"""'
            end_marker = '"""'
            start_idx = content.find(start_marker)
            if start_idx == -1:
                return None
            
            # Find the actual prompt content
            prompt_start = start_idx + len(start_marker)
            prompt_end = content.find(end_marker, prompt_start)
            if prompt_end == -1:
                return None
                
            # Return the raw prompt template
            return content[prompt_start:prompt_end]
    except Exception as e:
        print(f"{SOFT_REDDISH_ORANGE}Error reading system prompt: {str(e)}{RESET_COLOR}")
        return None

def generate_prompt_schema(player_stats, npc_stats_list, monster_stats_list, location_info):
    """Generate the combat prompt schema with all character and environment details"""
    # Try to read the original prompt format from combat_manager.py
    original_template = read_system_prompt()
    
    if original_template:
        print(f"{CYAN}Using original prompt template from combat_manager.py{RESET_COLOR}")
        
        # Process player stats
        player_name = player_stats['name']
        player_class = player_stats['class']
        player_level = player_stats['level']
        player_hp = player_stats['hitPoints']
        player_max_hp = player_stats['maxHitPoints']
        player_ac = player_stats['armorClass']
        player_str = player_stats['abilities']['strength']
        player_str_mod = (player_str-10)//2
        player_dex = player_stats['abilities']['dexterity']
        player_dex_mod = (player_dex-10)//2
        player_con = player_stats['abilities']['constitution']
        player_con_mod = (player_con-10)//2
        player_int = player_stats['abilities']['intelligence']
        player_int_mod = (player_int-10)//2
        player_wis = player_stats['abilities']['wisdom']
        player_wis_mod = (player_wis-10)//2
        player_cha = player_stats['abilities']['charisma']
        player_cha_mod = (player_cha-10)//2
        
        # Format player skills and attacks
        player_skills = ', '.join([f"{skill} +{bonus}" for skill, bonus in player_stats['skills'].items()])
        
        # Filter and format attacks
        player_attacks = []
        for attack in player_stats['attacksAndSpellcasting']:
            if 'type' in attack and attack['type'] == 'ability':
                continue
            if 'attackBonus' in attack and 'damageDice' in attack and 'damageBonus' in attack and 'damageType' in attack:
                player_attacks.append(f"{attack['name']} +{attack['attackBonus']} to hit, {attack['damageDice']}+{attack['damageBonus']} {attack['damageType']} damage")
        player_attacks_str = ', '.join(player_attacks)
        
        player_features = ', '.join(player_stats['features'])
        
        # Process NPCs
        npc_section = "\nNPCs:\n"
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
                    if 'attackBonus' in action and 'damageDice' in action and 'damageBonus' in action and 'damageType' in action:
                        valid_actions.append(f"{action['name']} +{action['attackBonus']} to hit, {action['damageDice']}+{action['damageBonus']} {action['damageType']} damage")
                
                if valid_actions:
                    attacks_str = ", ".join(valid_actions)
                    npc_section += f"Attacks: {attacks_str}\n"
            
            # Add special abilities if present
            if "specialAbilities" in npc:
                abilities_str = ", ".join([ability['name'] for ability in npc['specialAbilities']])
                npc_section += f"Special Abilities: {abilities_str}\n"
            
            npc_section += "\n"
            
        # Process monsters
        monster_section = "\nMonsters:\n"
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
                    if 'attackBonus' in action and 'damageDice' in action and 'damageBonus' in action and 'damageType' in action:
                        valid_actions.append(f"{action['name']} +{action['attackBonus']} to hit, {action['damageDice']}+{action['damageBonus']} {action['damageType']} damage")
                
                if valid_actions:
                    actions_str = ", ".join(valid_actions)
                    monster_section += f"Actions: {actions_str}\n"
            
            monster_section += "\n"
        
        # Create location section
        location_section = f"""
Environment: {location_info.get('description', 'No description available')}

Combat Setup:
1. You'll narrate the scene and manage initiative based on creature stats
2. Roll initiative for all combatants (players, NPCs, monsters) and determine turn order
3. Describe each turn, including attacks, damage, movement, and special actions
4. Manage and apply combat modifiers (cover, conditions, advantage/disadvantage)
5. Determine outcomes of attacks, spells, and abilities
6. Track hit points, conditions, and resources of all combatants
7. Narrate environmental interactions and tactical choices
8. Ask the player(s) for their actions on their turns
9. Determine when combat has resolved (enemies defeated, fled, or surrendered)
"""
        
        # Create output schema section
        schema_section = """
Output Format (Important):
For normal narration, use JSON as shown below.

```json
{
  "narration": "Your vivid description of the combat scene, turn, or outcome...",
  "combatDetails": {
    "initiative": [
      {"name": "Character Name", "initiative": 18, "status": "active/wounded/unconscious"},
      ...ordered by initiative from highest to lowest
    ],
    "currentTurn": "Character Name",
    "round": 1
  }
}
```

When combat concludes, use this format for the final summary:

```json
{
  "narration": "Your vivid description of the outcome, consequences, xp granted, and next steps...",
  "actions": [
    {
      "action": "updateEncounter",
      "parameters": {
        "encounterId": "[ENCOUNTER_ID]",
        "changes": "Summary of status changes - defeated enemies, conditions, etc."
      }
    },
    {
      "action": "updatePlayerInfo",
      "parameters": {
        "changes": "Player lost X hit points from attacks, current HP is Y."
      }
    },
    {
      "action": "updateNPCInfo",
      "parameters": {
        "npcName": "NPC_NAME",
        "changes": "NPC lost X hit points from attacks, current HP is Y."
      }
    },
    ...any other relevant updates...
    {
      "action": "exit",
      "parameters": {}
    }
  ]
}
```

When asking the player for actions, remember to give them clear options, explain the current situation, and provide all relevant tactical information.

Begin the combat by rolling initiative and setting the scene.
"""
        
        # Assemble the prompt
        prompt = """You are a Dungeon Master controlling combat in a role-playing game. Your job is to manage and describe a combat encounter fairly and engagingly, following the rules below:

- Combat proceeds in turns based on initiative
- Each entity acts once per round in initiative order
- Attacks involve rolling a d20 + modifiers against AC
- Damage is rolled after hits
- NPCs and monsters act logically, use appropriate tactics, and coordinate when possible
- Describe combat vividly with sensory details and tactical dynamics
- Maintain the fantasy world's immersion
- Track hit points, positions, and conditions
- Natural 20s are critical hits doing double damage dice
- Natural 1s are critical fails with consequences

"""
        
        prompt += f"The combat is taking place in: {location_info.get('name', 'Unknown Location')}\n"
        prompt += f"Description: {location_info.get('description', 'No description available')}\n\n"
        
        # Add player details
        prompt += f"""Player Character:
Name: {player_name}
Class: {player_class}
Level: {player_level}
HP: {player_hp}/{player_max_hp}
AC: {player_ac}
STR: {player_str} ({player_str_mod})
DEX: {player_dex} ({player_dex_mod})
CON: {player_con} ({player_con_mod})
INT: {player_int} ({player_int_mod})
WIS: {player_wis} ({player_wis_mod})
CHA: {player_cha} ({player_cha_mod})
Skills: {player_skills}
Attacks: {player_attacks_str}
Features: {player_features}
"""
        
        # Add NPC and monster sections
        prompt += npc_section
        prompt += monster_section
        
        # Add location and schema sections
        prompt += location_section
        prompt += schema_section
        
        return prompt
    
    # Fallback to a simplified prompt if we can't extract from the original
    print(f"{SOFT_REDDISH_ORANGE}Using fallback prompt generator. Original template could not be loaded.{RESET_COLOR}")
    prompt = f"""You are a Dungeon Master controlling combat in a role-playing game. Your job is to manage and describe a combat encounter fairly and engagingly.

The combat is taking place in: {location_info.get('name', 'Unknown Location')}
Description: {location_info.get('description', 'No description available')}

Player Character:
Name: {player_stats['name']}
Class: {player_stats['class']}
Level: {player_stats['level']}
HP: {player_stats['hitPoints']}/{player_stats['maxHitPoints']}
AC: {player_stats['armorClass']}

NPC Ally:
Name: {npc_stats_list[0]['name'] if npc_stats_list else 'None'}

Monster:
Name: {monster_stats_list[0]['name'] if monster_stats_list else 'None'}
Type: {monster_stats_list[0]['type'] if monster_stats_list else 'Unknown'}

Output Format (Important): 
Use JSON format for all responses with the following structure:

```json
{
  "narration": "Your description of the combat...",
  "combatDetails": {
    "initiative": [...],
    "currentTurn": "Character Name",
    "round": 1
  }
}
```

When combat concludes, include "actions" with updateEncounter, updatePlayerInfo, and exit commands.
"""
    return prompt

def generate_player_prompt(player_stats, location_info, current_message=None):
    """Generate prompt for the LLM simulating player actions"""
    prompt = f"""You are roleplaying as a player character in a D&D-style combat scenario. 
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
            
    prompt = f"""You are an expert D&D Dungeon Master evaluating an AI-driven combat system's performance.
You will analyze a 2-turn combat transcript between a combat AI (acting as DM) and a player character AI to determine if the combat AI adhered to its requirements.

Test ID: {test_id}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

EVALUATION CRITERIA:
1. Schema Adherence: Did the combat AI use the correct JSON format for its responses?
2. Combat Rules: Did the AI follow the D&D-style combat rules (initiative, attack rolls, damage, etc.)?
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
{original_prompt[:500]}...
[System prompt truncated for brevity - it instructs the AI to run D&D combat with initiative order, proper JSON formatting, status tracking, and action commands for state changes]
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
    
    # Add initial system prompt
    combat_prompt = generate_prompt_schema(
        player_stats, 
        [npc_stats], 
        [monster_stats], 
        location_info
    )
    conversation_history.append({"role": "system", "content": combat_prompt})
    
    # Start combat - get initial narration from combat AI
    print(f"{YELLOW}Initializing combat with {COMBAT_MAIN_MODEL}...{RESET_COLOR}")
    response = client.chat.completions.create(
        model=COMBAT_MAIN_MODEL,
        temperature=1.0,
        messages=[{"role": "system", "content": combat_prompt}]
    )
    ai_message = response.choices[0].message.content
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
        ai_response = client.chat.completions.create(
            model=COMBAT_MAIN_MODEL,
            temperature=1.0,
            messages=[msg for msg in conversation_history]
        )
        ai_message = ai_response.choices[0].message.content
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