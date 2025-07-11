#!/usr/bin/env python3
"""Debug script to test spell slot updates for Eirik"""

import json
from update_character_info import update_character_info
from file_operations import safe_read_json
from enhanced_logger import set_script_name, debug, info, error

# Set up logging
set_script_name("debug_spell_slots")

def test_spell_slot_update():
    """Test updating Eirik's spell slots after long rest"""
    
    # Test 1: Simple spell slot update
    print("\n=== TEST 1: Simple spell slot restoration ===")
    result = update_character_info(
        "eirik_hearthwise",
        "Restore all spell slots after long rest (L1: 4/4, L2: 2/2)"
    )
    print(f"Result: {result}")
    
    # Check the current state
    character_data = safe_read_json("characters/eirik_hearthwise.json")
    if character_data:
        current_slots = character_data.get('spellcasting', {}).get('spellSlots', {})
        print(f"Current spell slots after update:")
        print(json.dumps(current_slots, indent=2))
    
    # Test 2: More explicit format
    print("\n=== TEST 2: Explicit spell slot format ===")
    result = update_character_info(
        "eirik_hearthwise",
        "Set spell slots to: level1 current=4 max=4, level2 current=2 max=2"
    )
    print(f"Result: {result}")
    
    # Check the state again
    character_data = safe_read_json("characters/eirik_hearthwise.json")
    if character_data:
        current_slots = character_data.get('spellcasting', {}).get('spellSlots', {})
        print(f"Current spell slots after update:")
        print(json.dumps(current_slots, indent=2))
    
    # Test 3: JSON-like format
    print("\n=== TEST 3: JSON-like spell slot format ===")
    result = update_character_info(
        "eirik_hearthwise",
        "Update spellcasting spell slots: level1 {current: 4, max: 4}, level2 {current: 2, max: 2}"
    )
    print(f"Result: {result}")
    
    # Final check
    character_data = safe_read_json("characters/eirik_hearthwise.json")
    if character_data:
        current_slots = character_data.get('spellcasting', {}).get('spellSlots', {})
        print(f"Final spell slots:")
        print(json.dumps(current_slots, indent=2))

if __name__ == "__main__":
    test_spell_slot_update()