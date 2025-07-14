#!/usr/bin/env python3
"""Debug script to test character update functionality"""

import json
import os
from update_character_info import update_character_info, normalize_character_name, get_character_path, detect_character_role
from module_path_manager import ModulePathManager
from file_operations import safe_read_json

def debug_character_update():
    print("=== Character Update Debug ===")
    
    # Test 1: Check character name normalization
    print("\n1. Testing character name normalization:")
    names = ["eirik_hearthwise", "Scout Kira"]
    for name in names:
        normalized = normalize_character_name(name)
        print(f"   {name} -> {normalized}")
    
    # Test 2: Check character role detection
    print("\n2. Testing character role detection:")
    for name in names:
        role = detect_character_role(name)
        print(f"   {name}: {role}")
    
    # Test 3: Check file paths
    print("\n3. Testing file paths:")
    for name in names:
        role = detect_character_role(name)
        path = get_character_path(name, role)
        exists = os.path.exists(path)
        print(f"   {name}: {path} (exists: {exists})")
    
    # Test 4: Try to load character data
    print("\n4. Testing character data loading:")
    for name in names:
        role = detect_character_role(name)
        path = get_character_path(name, role)
        data = safe_read_json(path)
        if data:
            print(f"   {name}: Loaded successfully, type: {type(data)}")
            if isinstance(data, dict):
                print(f"      Keys: {list(data.keys())[:5]}...")
        else:
            print(f"   {name}: Failed to load")
    
    # Test 5: Check party tracker
    print("\n5. Party tracker info:")
    party_data = safe_read_json("party_tracker.json")
    if party_data:
        print(f"   Module: {party_data.get('module')}")
        print(f"   Party Members: {party_data.get('partyMembers')}")
        print(f"   Party NPCs: {[npc['name'] for npc in party_data.get('partyNPCs', [])]}")
    
    # Test 6: Module path manager
    print("\n6. Module path manager:")
    path_manager = ModulePathManager()
    print(f"   Module name: {path_manager.module_name}")
    print(f"   Module dir: {path_manager.module_dir}")
    
    # Test 7: Try a minimal update
    print("\n7. Testing minimal character update:")
    test_changes = "Testing character update system."
    result = update_character_info("eirik_hearthwise", test_changes)
    print(f"   Update result: {result}")

if __name__ == "__main__":
    debug_character_update()