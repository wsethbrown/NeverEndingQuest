#!/usr/bin/env python3
"""Fixed version of combat_manager.py that properly handles monster loading errors"""

# Changes made in simulate_combat_encounter:
# 1. Add better error handling for monster file loading
# 2. Check if monster_templates is empty before proceeding
# 3. Add more debug output

def simulate_combat_encounter(encounter_id):
    """Fixed version of simulate_combat_encounter with better error handling"""
    print(f"DEBUG: Starting combat simulation for encounter {encounter_id}")
    
    # Initialize path manager
    from campaign_path_manager import CampaignPathManager
    path_manager = CampaignPathManager()
    
    # ... (other initialization code remains the same) ...
    
    # Initialize data containers
    player_info = None
    monster_templates = {}
    npc_templates = {}
    
    # Extract data for all creatures in the encounter
    for creature in encounter_data["creatures"]:
        if creature["type"] == "player":
            player_name = creature["name"].lower().replace(" ", "_")
            player_file = path_manager.get_player_path(player_name)
            try:
                with open(player_file, "r") as file:
                    player_info = json.load(file)
                    print(f"DEBUG: Loaded player file: {player_file}")
            except Exception as e:
                print(f"ERROR: Failed to load player file {player_file}: {str(e)}")
                return None, None
        
        elif creature["type"] == "enemy":
            monster_type = creature["monsterType"]
            if monster_type not in monster_templates:
                monster_file = path_manager.get_monster_path(monster_type)
                print(f"DEBUG: Attempting to load monster file: {monster_file}")
                try:
                    with open(monster_file, "r") as file:
                        monster_templates[monster_type] = json.load(file)
                        print(f"DEBUG: Successfully loaded monster: {monster_type}")
                except FileNotFoundError as e:
                    print(f"ERROR: Monster file not found: {monster_file}")
                    print(f"ERROR: {str(e)}")
                    # Check if the problem is the file naming
                    print(f"DEBUG: Expected file path: {monster_file}")
                    print(f"DEBUG: Monster type from encounter: {monster_type}")
                    # List available monster files for debugging
                    monster_dir = f"{path_manager.campaign_dir}/monsters"
                    if os.path.exists(monster_dir):
                        print(f"DEBUG: Available monster files in {monster_dir}:")
                        for f in os.listdir(monster_dir):
                            print(f"  - {f}")
                    return None, None
                except json.JSONDecodeError as e:
                    print(f"ERROR: Invalid JSON in monster file {monster_file}: {str(e)}")
                    return None, None
                except Exception as e:
                    print(f"ERROR: Failed to load monster file {monster_file}: {str(e)}")
                    print(f"ERROR: Exception type: {type(e).__name__}")
                    import traceback
                    traceback.print_exc()
                    return None, None
    
    # Verify that we loaded all necessary data
    if not monster_templates:
        print("ERROR: No monster templates were loaded!")
        return None, None
    
    print(f"DEBUG: Loaded {len(monster_templates)} monster template(s)")
    for k, v in monster_templates.items():
        print(f"  - {k}: {v.get('name', 'Unknown')}")
    
    # ... (rest of the function remains the same) ...