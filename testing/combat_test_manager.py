#!/usr/bin/env python3
"""
Combat Test Manager for DungeonMasterAI

A streamlined version of the combat_manager.py specifically designed
for testing prompt adherence in an isolated environment.
"""

import json
import os
import time
import shutil
import sys
import copy
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

def use_combat_manager_prompt_schema(player_stats, npc_stats_list, monster_stats_list, location_info):
    """
    Wrapper function for the original generate_prompt_schema function 
    from combat_manager.py with compatibility handling
    """
    import copy
    
    # Make copies of the data to avoid modifying the originals
    player_stats_copy = copy.deepcopy(player_stats)
    npc_stats_list_copy = copy.deepcopy(npc_stats_list)
    monster_stats_list_copy = copy.deepcopy(monster_stats_list)
    
    # Add compatibility for player attacks
    if 'attacksAndSpellcasting' in player_stats_copy:
        for attack in player_stats_copy['attacksAndSpellcasting']:
            if 'type' in attack and attack['type'] == 'ability':
                continue
            if 'attackBonus' not in attack:
                attack['attackBonus'] = 0
            if 'damageDice' not in attack:
                attack['damageDice'] = '0'
            if 'damageBonus' not in attack:
                attack['damageBonus'] = 0
            if 'damageType' not in attack:
                attack['damageType'] = 'none'
    
    # Add compatibility for NPC actions
    for npc in npc_stats_list_copy:
        if 'actions' in npc:
            for action in npc['actions']:
                if 'attackBonus' not in action:
                    action['attackBonus'] = 0
                if 'damageDice' not in action:
                    action['damageDice'] = '0'
                if 'damageBonus' not in action:
                    action['damageBonus'] = 0
                if 'damageType' not in action:
                    action['damageType'] = 'none'
    
    # Add compatibility for monster actions
    for monster in monster_stats_list_copy:
        if 'actions' in monster:
            for action in monster['actions']:
                if 'attackBonus' not in action:
                    action['attackBonus'] = 0
                if 'damageDice' not in action:
                    action['damageDice'] = '0'
                if 'damageBonus' not in action:
                    action['damageBonus'] = 0
                if 'damageType' not in action:
                    action['damageType'] = 'none'
    
    # Import the original generate_prompt_schema function from combat_manager.py
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(parent_dir)
    
    # Import the module directly
    try:
        import combat_manager
        # Get the function
        original_func = combat_manager.generate_prompt_schema
        # Call the original function with our compatible data
        return original_func(
            player_stats_copy, 
            npc_stats_list_copy, 
            monster_stats_list_copy, 
            location_info
        )
    except ImportError:
        print(f"{SOFT_REDDISH_ORANGE}Error importing combat_manager module. Falling back to local implementation.{RESET_COLOR}")
        # Fallback to a simplified version if import fails
        return generate_fallback_prompt(player_stats, npc_stats_list, monster_stats_list, location_info)

# Use the wrapper function for prompt generation
generate_prompt_schema = use_combat_manager_prompt_schema

def generate_fallback_prompt(player_stats, npc_stats_list, monster_stats_list, location_info):
    """Fallback prompt generator in case the import fails"""
    print(f"{SOFT_REDDISH_ORANGE}Using fallback prompt generator. This should only happen if the combat_manager.py import fails.{RESET_COLOR}")
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
Use JSON format for all responses.
"""
    return prompt

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
{original_prompt}
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