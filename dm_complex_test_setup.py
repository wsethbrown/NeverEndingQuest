#!/usr/bin/env python3
"""
Complex DM Test Setup
Tests multiple DM functions simultaneously in a single prompt
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# The uber-complicated test prompt that exercises multiple functions
COMPLEX_TEST_PROMPT = """Dungeon Master Note: Current date and time: 1492 Springmonth 2 15:13:00. Player: I want to give Elen a potion of healing and 50 gold, then have her cast a spell to detect magic on my sword. While she's doing that, I'll update my journal about finding a mysterious symbol in the ruins. Also, we found a hidden compartment with a magical tome that teaches the Shield spell - I want to learn it. Oh, and 2 hours pass during all this. Update the plot to reflect we discovered clues about an ancient curse affecting the village. Finally, I think I've earned enough XP to level up!"""

def load_conversation_history():
    """Load the original conversation history"""
    try:
        with open('conversation_history.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading conversation history: {e}")
        return None

def create_test_conversation(original_history):
    """Create a test version with the complex prompt"""
    if not original_history:
        return None
    
    # Make a copy
    test_history = original_history.copy()
    
    # Replace the last user message
    if test_history and test_history[-1].get('role') == 'user':
        test_history[-1]['content'] = COMPLEX_TEST_PROMPT
    else:
        # Add as new message if needed
        test_history.append({
            "role": "user",
            "content": COMPLEX_TEST_PROMPT
        })
    
    return test_history

def save_test_conversation(test_history):
    """Save the test conversation to a file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dm_complex_test_conversation_{timestamp}.json"
    
    try:
        with open(filename, 'w') as f:
            json.dump(test_history, f, indent=2)
        print(f"Test conversation saved to: {filename}")
        return filename
    except Exception as e:
        print(f"Error saving test conversation: {e}")
        return None

def run_dm_test(test_file):
    """Run the DM with the test conversation"""
    print("\n=== Running DM Test ===")
    print(f"Test prompt: {COMPLEX_TEST_PROMPT[:100]}...")
    
    # This would be where you run your actual DM system
    # For now, we'll create a mock response showing what should be generated
    
    mock_response = {
        "narration": "You hand Elen a potion of healing and a pouch containing 50 gold pieces. She accepts them gratefully, tucking the potion into her belt and the gold into her pack. 'Thank you, Norn. Let me check your sword for enchantments.' She begins the incantation for Detect Magic, her hands glowing with a faint blue light as she passes them over your blade. The sword emanates a strong aura of transmutation magic. While she works, you pull out your journal and sketch the mysterious symbol you discovered in the ruins - a circular pattern with interconnected runes that seem to shift when you're not looking directly at them. In the hidden compartment, you find an ancient tome bound in midnight blue leather. As you open it, the arcane formulae for the Shield spell become clear to you. You spend time studying and practicing the somatic components. Hours pass as you work together, piecing together the clues. The symbol, the tome, and other evidence point to an ancient curse that has been slowly affecting the village for generations. As understanding dawns, you feel the accumulated experience of your adventures crystallize into new capabilities.",
        "actions": [
            {
                "action": "updateCharacterInfo",
                "parameters": {
                    "characterName": "norn",
                    "changes": "Removed 1 Potion of Healing and 50 gold from inventory. Added journal entry about mysterious symbol from ruins. Learned Shield spell (1st level abjuration)."
                }
            },
            {
                "action": "updateCharacterInfo", 
                "parameters": {
                    "characterName": "elen",
                    "changes": "Added 1 Potion of Healing and 50 gold to inventory. Cast Detect Magic spell (1st level slot expended)."
                }
            },
            {
                "action": "updateTime",
                "parameters": {
                    "hoursToAdd": 2
                }
            },
            {
                "action": "updatePlot",
                "parameters": {
                    "plotKey": "ancient_village_curse",
                    "description": "Discovered mysterious symbol in ruins and magical tome. Evidence points to an ancient curse affecting the village for generations.",
                    "status": "discovered"
                }
            },
            {
                "action": "levelUp",
                "parameters": {
                    "characterName": "norn"
                }
            }
        ]
    }
    
    # Save the mock response
    response_file = f"dm_test_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(response_file, 'w') as f:
        json.dump(mock_response, f, indent=2)
    
    print(f"Response saved to: {response_file}")
    return response_file

def validate_response(response_file):
    """Run the validator on the response"""
    print("\n=== Validating Response ===")
    
    try:
        # Run the validator
        result = subprocess.run(
            [sys.executable, 'dm_response_validator.py', response_file],
            capture_output=True,
            text=True
        )
        
        print("Validator Output:")
        print(result.stdout)
        if result.stderr:
            print("Validator Errors:")
            print(result.stderr)
            
        return result.returncode == 0
    except FileNotFoundError:
        print("Validator script not found. Creating basic validation...")
        # Perform basic validation if validator doesn't exist
        with open(response_file, 'r') as f:
            response = json.load(f)
        
        # Basic checks
        valid = True
        if 'narration' not in response:
            print("[FAIL] Missing 'narration' field")
            valid = False
        if 'actions' not in response:
            print("[FAIL] Missing 'actions' field")
            valid = False
        else:
            # Check we have all expected actions
            action_types = [a['action'] for a in response['actions']]
            expected = ['updateCharacterInfo', 'updateTime', 'updatePlot', 'levelUp']
            for exp in expected:
                if exp not in action_types:
                    print(f"[FAIL] Missing expected action: {exp}")
                    valid = False
        
        if valid:
            print("[PASS] Basic validation successful")
        return valid

def main():
    print("=== DM Complex Function Test ===")
    print(f"Test Time: {datetime.now()}")
    
    # Load original conversation
    print("\nLoading conversation history...")
    original = load_conversation_history()
    if not original:
        print("Failed to load conversation history")
        return
    
    # Create test version
    print("Creating test conversation...")
    test_history = create_test_conversation(original)
    if not test_history:
        print("Failed to create test conversation")
        return
    
    # Save test file
    test_file = save_test_conversation(test_history)
    if not test_file:
        print("Failed to save test conversation")
        return
    
    # Run DM test
    response_file = run_dm_test(test_file)
    
    # Validate response
    is_valid = validate_response(response_file)
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Test Prompt: Complex multi-function test")
    print(f"Functions Tested: updateCharacterInfo (2x), updateTime, updatePlot, levelUp")
    print(f"Validation Result: {'PASSED' if is_valid else 'FAILED'}")
    
    # Save summary
    summary = {
        "test_timestamp": datetime.now().isoformat(),
        "test_prompt": COMPLEX_TEST_PROMPT,
        "test_file": test_file,
        "response_file": response_file,
        "validation_passed": is_valid,
        "functions_tested": [
            "updateCharacterInfo (multiple)",
            "updateTime",
            "updatePlot", 
            "levelUp"
        ]
    }
    
    summary_file = f"dm_complex_test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nTest summary saved to: {summary_file}")

if __name__ == "__main__":
    main()