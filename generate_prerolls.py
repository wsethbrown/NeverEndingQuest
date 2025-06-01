# generate_prerolls.py
import random
import json
import os

def roll_damage(damage_dice):
    """Parse and roll damage dice like '2d6+3'"""
    try:
        # Handle modifiers
        modifier = 0
        if "+" in damage_dice:
            dice_part, mod_part = damage_dice.split("+")
            damage_dice = dice_part
            modifier = int(mod_part)
        elif "-" in damage_dice:
            dice_part, mod_part = damage_dice.split("-")
            damage_dice = dice_part
            modifier = -int(mod_part)
            
        # Parse the dice notation
        parts = damage_dice.lower().split('d')
        num_dice = int(parts[0]) if parts[0] else 1
        dice_type = int(parts[1]) if len(parts) > 1 else 6
        
        # Roll the dice and add modifier
        rolls = [random.randint(1, dice_type) for _ in range(num_dice)]
        total = sum(rolls) + modifier
        
        return total
    except:
        # Fallback for any parsing errors
        return random.randint(1, 6)

def load_monster_stats(monster_name):
    """Load monster stats from file."""
    from campaign_path_manager import CampaignPathManager
    path_manager = CampaignPathManager()
    
    monster_file = path_manager.get_monster_path(monster_name)
    try:
        with open(monster_file, "r") as file:
            monster_stats = json.load(file)
        return monster_stats
    except Exception as e:
        print(f"Error loading monster data for {monster_name}: {str(e)}")
        return None

def load_npc_data(npc_name):
    """Load NPC data from file."""
    from campaign_path_manager import CampaignPathManager
    path_manager = CampaignPathManager()
    
    npc_file = path_manager.get_character_path(npc_name)
    try:
        with open(npc_file, "r") as file:
            npc_data = json.load(file)
        return npc_data
    except Exception as e:
        print(f"Error loading NPC data for {npc_name}: {str(e)}")
        return None

def generate_prerolls(encounter_data):
    """Generate random dice rolls for all non-player creatures in the encounter."""
    preroll_lines = []
    preroll_lines.append("DM Note: Pre-generated UNMODIFIED dice rolls for this round:")
    
    # First, identify the player character for reference
    player_name = "Unknown Player"
    for creature in encounter_data.get("creatures", []):
        if creature.get("type") == "player":
            player_name = creature.get("name", "Unknown Player")
            preroll_lines.append(f"[PLAYER CHARACTER: {player_name}] The player must make their own rolls.")
            break
    
    # Process each non-player creature with explicit type labels
    for creature in encounter_data.get("creatures", []):
        # Skip player characters
        if creature.get("type") == "player":
            continue
            
        creature_name = creature.get("name", "Unknown Creature")
        creature_type = creature.get("type", "unknown").upper()
        
        # Generate basic dice rolls
        attack_rolls = [random.randint(1, 20) for _ in range(3)]  # 3 potential attacks
        
        # Handle damage rolls based on creature type
        damage_rolls = []
        if creature.get("type") == "enemy":
            # For monsters, try to get their damage dice from templates
            monster_type = creature.get("monsterType", "")
            monster_data = load_monster_stats(monster_type)
            if monster_data and "attacksAndSpellcasting" in monster_data:
                for attack in monster_data.get("attacksAndSpellcasting", [])[:3]:  # Get up to 3 attacks
                    damage_dice = attack.get("damageDice", "1d6")
                    damage_rolls.append(roll_damage(damage_dice))
            else:
                # Fallback generic damage rolls
                damage_rolls = [roll_damage("1d6+1") for _ in range(3)]
        elif creature.get("type") == "npc":
            # For NPCs, use their weapon damage if available
            npc_name = creature_name.lower().replace(" ", "_").split('_')[0]
            npc_data = load_npc_data(npc_name)
            if npc_data and "equipment" in npc_data:
                for item in npc_data.get("equipment", [])[:3]:
                    if "damage" in item:
                        damage_rolls.append(roll_damage(item.get("damage", "1d6")))
                # Fill remaining slots with generic rolls
                while len(damage_rolls) < 3:
                    damage_rolls.append(roll_damage("1d6"))
            else:
                # Fallback generic damage rolls
                damage_rolls = [roll_damage("1d6") for _ in range(3)]
        
        # Generate saving throw rolls
        save_rolls = {
            "STR": random.randint(1, 20),
            "DEX": random.randint(1, 20),
            "CON": random.randint(1, 20),
            "INT": random.randint(1, 20),
            "WIS": random.randint(1, 20),
            "CHA": random.randint(1, 20)
        }
        
        # Also add a few generic rolls for spells or abilities
        ability_rolls = [random.randint(1, 20) for _ in range(3)]
        
        # Format rolls for this creature with EXPLICIT type labeling
        save_rolls_str = ", ".join([f"{ability}:{roll}" for ability, roll in save_rolls.items()])
        preroll_line = f"[{creature_type}: {creature_name}] Raw d20 rolls: {attack_rolls}, "
        preroll_line += f"Damage dice: {damage_rolls}, "
        preroll_line += f"Save dice: [{save_rolls_str}], "
        preroll_line += f"Ability rolls: {ability_rolls}"
        preroll_lines.append(preroll_line)
    
    # Add special reminder about creature types
    preroll_lines.append("\nCREATURE TYPES IN THIS ENCOUNTER:")
    type_counts = {"PLAYER": 0, "NPC": 0, "ENEMY": 0}
    
    for creature in encounter_data.get("creatures", []):
        creature_type = creature.get("type", "unknown").upper()
        creature_name = creature.get("name", "Unknown")
        if creature_type in type_counts:
            type_counts[creature_type] += 1
        
        # Add a line for each creature with its type
        if creature_type == "PLAYER":
            preroll_lines.append(f"- {creature_name}: {creature_type} CHARACTER (controlled by the human player)")
        elif creature_type == "NPC":
            preroll_lines.append(f"- {creature_name}: {creature_type} (friendly non-player character, allied with {player_name})")
        elif creature_type == "ENEMY MONSTER":
            monster_type = creature.get("monsterType", "monster")
            preroll_lines.append(f"- {creature_name}: {creature_type} ({monster_type}, hostile to {player_name})")
    
    # Add the modifier note
    preroll_lines.append("\nIMPORTANT: You must apply all appropriate modifiers to these rolls based on:")
    preroll_lines.append("- Ability score modifiers")
    preroll_lines.append("- Proficiency bonuses")
    preroll_lines.append("- Weapon/spell bonuses")
    preroll_lines.append("- Situational advantages/disadvantages")
    preroll_lines.append("- Special abilities and feats")
    preroll_lines.append("\nNote: The player must make their own rolls.")
    
    return "\n".join(preroll_lines)

def test_generate_prerolls():
    """Test function for generate_prerolls"""
    # Create a sample encounter
    sample_encounter = {
        "encounterId": "test_encounter",
        "creatures": [
            {
                "type": "player",
                "name": "Test Player"
            },
            {
                "type": "enemy",
                "name": "Goblin 1",
                "monsterType": "goblin"
            },
            {
                "type": "enemy",
                "name": "Goblin 2",
                "monsterType": "goblin"
            },
            {
                "type": "npc",
                "name": "Friendly NPC"
            }
        ]
    }
    
    prerolls = generate_prerolls(sample_encounter)
    print(prerolls)

if __name__ == "__main__":
    test_generate_prerolls()