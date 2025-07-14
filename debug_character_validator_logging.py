#!/usr/bin/env python3
"""
Debug script to test character validator logging and ammunition consolidation
"""

import json
import sys
from character_validator import AICharacterValidator
from enhanced_logger import debug, info, warning, error, set_script_name
from file_operations import safe_read_json

# Set script name for logging
set_script_name("DebugValidator")

def test_validator_logging():
    """Test that validator messages are properly logged"""
    
    # Test basic logging first
    print("\n=== Testing Basic Logging ===")
    info("TEST: Basic info message", category="character_validation")
    debug("TEST: Basic debug message", category="character_validation")
    warning("TEST: Basic warning message", category="character_validation")
    error("TEST: Basic error message", category="character_validation")
    
    # Test character update messages
    print("\n=== Testing Character Update Messages ===")
    info("[Character Update] Test character update message", category="character_updates")
    
    # Load Eirik's character file
    character_path = "characters/eirik_hearthwise.json.backup_latest"
    print(f"\n=== Loading character from {character_path} ===")
    
    character_data = safe_read_json(character_path)
    if not character_data:
        error(f"Failed to load character file: {character_path}")
        return
    
    print(f"Loaded character: {character_data.get('name', 'Unknown')}")
    
    # Check current equipment
    print("\n=== Current Equipment (Ammunition items) ===")
    equipment = character_data.get('equipment', [])
    for item in equipment:
        if item.get('item_type') == 'ammunition' or 'bolt' in item.get('item_name', '').lower():
            print(f"- {item.get('item_name')}: Type={item.get('item_type')}, Qty={item.get('quantity')}")
    
    # Check current ammunition section
    print("\n=== Current Ammunition Section ===")
    ammunition = character_data.get('ammunition', [])
    for ammo in ammunition:
        print(f"- {ammo.get('name')}: Qty={ammo.get('quantity')}")
    
    # Test the validator
    print("\n=== Testing Character Validator ===")
    validator = AICharacterValidator()
    
    # Test just the logging inside validate_and_correct_character
    print("\nCalling validate_and_correct_character...")
    validator.corrections_made = []  # Reset corrections
    
    # Add some test corrections to see if they're logged
    validator.corrections_made.append("TEST: Sample correction")
    
    # Test the info/debug calls directly
    info("TEST: Direct info call from test script", category="character_validation")
    debug("TEST: Direct debug call from test script", category="character_validation")
    
    # Now test with actual character data
    print("\n=== Testing with actual character data ===")
    # We'll call the ai_consolidate_inventory method directly to test its logging
    try:
        # First, let's see what the prompt looks like
        prompt = validator.build_inventory_consolidation_prompt(character_data)
        print("\n=== Consolidation Prompt Preview ===")
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        
        # Test parsing a mock response
        print("\n=== Testing Mock Consolidation Response ===")
        mock_response = """
        {
            "ammunition": [
                {
                    "name": "Crossbow bolt",
                    "quantity": 50,
                    "description": "Ammunition for crossbows."
                }
            ],
            "equipment": [
                {"item_name": "Crossbow bolts", "_remove": true}
            ],
            "consolidations_made": [
                "Moved 'Crossbow bolts x 10' to ammunition section",
                "Ammunition 'Crossbow bolt' increased from 40 to 50"
            ]
        }
        """
        
        updates = validator.parse_currency_consolidation_response(mock_response, character_data)
        print(f"Parsed updates: {json.dumps(updates, indent=2)}")
        print(f"Corrections made: {validator.corrections_made}")
        
    except Exception as e:
        error(f"Error during consolidation test: {str(e)}", category="character_validation")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_validator_logging()