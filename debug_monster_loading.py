#!/usr/bin/env python3
"""Debug script to test monster loading in combat_manager.py"""

import json
from campaign_path_manager import CampaignPathManager

# Initialize path manager
path_manager = CampaignPathManager()

# Test the same logic as combat_manager.py
monster_type = "giant_centipede"
monster_file = path_manager.get_monster_path(monster_type)

print(f"Campaign dir: {path_manager.campaign_dir}")
print(f"Monster type: {monster_type}")
print(f"Monster file path: {monster_file}")

# Try to open and load the file
try:
    print(f"Attempting to open: {monster_file}")
    with open(monster_file, "r") as file:
        monster_data = json.load(file)
        print(f"Successfully loaded monster data: {monster_data['name']}")
        print(f"Monster HP: {monster_data['hitPoints']}")
except FileNotFoundError as e:
    print(f"FileNotFoundError: {e}")
except json.JSONDecodeError as e:
    print(f"JSONDecodeError: {e}")
except Exception as e:
    print(f"Unexpected error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()