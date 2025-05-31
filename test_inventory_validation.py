#!/usr/bin/env python3
"""Test script to verify inventory validation works correctly"""

import json
from update_character_info import update_character_info

# Test scenarios
def test_validation():
    print("Testing inventory validation system...\n")
    
    # Test 1: Item consumption that returns empty array
    print("Test 1: Item consumption (empty array)")
    original = {
        "name": "Norn",
        "equipment": [
            {"item_name": "Longsword", "item_type": "weapon", "quantity": 1},
            {"item_name": "Shield", "item_type": "armor", "quantity": 1},
            {"item_name": "Potion of Healing", "item_type": "miscellaneous", "quantity": 1}
        ],
        "hitPoints": 20
    }
    
    proposed = {
        "equipment": [],  # Wrong! This clears all equipment
        "hitPoints": 28
    }
    
    changes = "Used potion of healing to restore 8 hit points"
    
    is_valid, issues, corrections = validate_player_update(original, proposed, changes)
    print(f"Valid: {is_valid}")
    print(f"Issues: {issues}")
    print(f"Corrections: {json.dumps(corrections, indent=2)}\n")
    
    # Test 2: Adding item (single item array)
    print("\nTest 2: Adding item (single item array)")
    proposed2 = {
        "equipment": [
            {"item_name": "Rope", "item_type": "miscellaneous", "quantity": 1}
        ]
    }
    
    changes2 = "Found 50 feet of rope"
    
    is_valid2, issues2, corrections2 = validate_player_update(original, proposed2, changes2)
    print(f"Valid: {is_valid2}")
    print(f"Issues: {issues2}")
    print(f"Corrections: {json.dumps(corrections2, indent=2)}\n")
    
    # Test 3: Correct update
    print("\nTest 3: Correct update (full array)")
    proposed3 = {
        "equipment": [
            {"item_name": "Longsword", "item_type": "weapon", "quantity": 1},
            {"item_name": "Shield", "item_type": "armor", "quantity": 1}
        ],
        "hitPoints": 28
    }
    
    changes3 = "Used potion of healing to restore 8 hit points"
    
    is_valid3, issues3, corrections3 = validate_player_update(original, proposed3, changes3)
    print(f"Valid: {is_valid3}")
    print(f"Issues: {issues3}")
    print(f"Corrections: {corrections3}\n")

if __name__ == "__main__":
    test_validation()