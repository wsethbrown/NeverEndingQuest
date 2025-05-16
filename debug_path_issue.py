#!/usr/bin/env python3
"""Debug script to test path issues"""

import os
import json
from campaign_path_manager import CampaignPathManager

# Check current working directory
print(f"Current working directory: {os.getcwd()}")

# Initialize path manager
path_manager = CampaignPathManager()
print(f"Campaign name: {path_manager.campaign_name}")
print(f"Campaign dir: {path_manager.campaign_dir}")

# Test monster path
monster_type = "giant_centipede"
monster_path = path_manager.get_monster_path(monster_type)
print(f"Monster path: {monster_path}")

# Check if the path is absolute or relative
print(f"Is absolute path: {os.path.isabs(monster_path)}")

# Check if the file exists using different methods
print(f"os.path.exists(): {os.path.exists(monster_path)}")
print(f"os.path.isfile(): {os.path.isfile(monster_path)}")

# Try to resolve the full path
try:
    full_path = os.path.abspath(monster_path)
    print(f"Full absolute path: {full_path}")
    print(f"Full path exists: {os.path.exists(full_path)}")
except Exception as e:
    print(f"Error resolving path: {e}")

# List the actual files in the campaign directory
if os.path.exists(path_manager.campaign_dir):
    print(f"\nFiles in {path_manager.campaign_dir}:")
    for root, dirs, files in os.walk(path_manager.campaign_dir):
        level = root.replace(path_manager.campaign_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")