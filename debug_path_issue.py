#!/usr/bin/env python3
"""Debug script to test path issues"""

import os
import json
from module_path_manager import ModulePathManager

# Check current working directory
print(f"Current working directory: {os.getcwd()}")

# Initialize path manager with current module for consistent path resolution
try:
    from encoding_utils import safe_json_load
    party_tracker = safe_json_load("party_tracker.json")
    current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
    path_manager = ModulePathManager(current_module)
except:
    path_manager = ModulePathManager()  # Fallback to reading from file
print(f"Module name: {path_manager.module_name}")
print(f"Module dir: {path_manager.module_dir}")

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

# List the actual files in the module directory
if os.path.exists(path_manager.module_dir):
    print(f"\nFiles in {path_manager.module_dir}:")
    for root, dirs, files in os.walk(path_manager.module_dir):
        level = root.replace(path_manager.module_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for f in files:
            print(f"{subindent}{f}")