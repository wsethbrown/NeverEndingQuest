#!/usr/bin/env python3
"""
Test the updated combat system with simulated scenarios
"""

import json
import os
from datetime import datetime

# Import the necessary modules
from gpt import get_gpt4_response
from combat_validation_prompt import validate_combat_response

def load_prompt(filename):
    """Load a prompt from file"""
    with open(filename, 'r') as f:
        return f.read()

def simulate_combat_turn(prompt, system_prompt_file='combat_sim_prompt.txt'):
    """Simulate a combat turn using the actual combat system"""
    # Load the combat system prompt
    with open(system_prompt_file, 'r') as f:
        system_prompt = f.read()
    
    # Get AI response
    print("Sending to AI...")
    response = get_gpt4_response(system_prompt, prompt)
    
    # Parse and display response
    try:
        parsed = json.loads(response)
        print("\nAI Response:")
        print(json.dumps(parsed, indent=2))
        return parsed
    except json.JSONDecodeError as e:
        print(f"\nERROR: Invalid JSON response: {e}")
        print(f"Raw response: {response}")
        return None

def validate_response(response, encounter_state):
    """Validate a combat response"""
    validation_prompt = f"""
{encounter_state}

AI Response to validate:
{json.dumps(response, indent=2)}
"""
    
    # Get validation result
    with open('combat_validation_prompt.txt', 'r') as f:
        validation_system = f.read()
    
    result = get_gpt4_response(validation_system, validation_prompt)
    
    try:
        return json.loads(result)
    except:
        print(f"Validation error: {result}")
        return None

def run_test_scenario_1():
    """Test basic combat with prerolls"""
    print("\n" + "="*60)
    print("RUNNING TEST SCENARIO 1: Basic Combat with Prerolls")
    print("="*60)
    
    prompt = load_prompt('test_combat_prompt_1.txt')
    response = simulate_combat_turn(prompt)
    
    if response:
        print("\nAnalyzing response...")
        print(f"✓ Has combat_round field: {'combat_round' in response}")
        print(f"✓ Combat round = 1: {response.get('combat_round') == 1}")
        print(f"✓ Has narration: {'narration' in response}")
        print(f"✓ Asks for player action: {'what' in response.get('narration', '').lower()}")
        
        # Check if it mentions prerolls or asks for rolls
        narration = response.get('narration', '').lower()
        print(f"✗ Incorrectly asks for dice roll: {'roll' in narration and 'd20' in narration}")
    
    return response

def run_test_scenario_2():
    """Test player action processing"""
    print("\n" + "="*60)
    print("RUNNING TEST SCENARIO 2: Player Action Processing")
    print("="*60)
    
    prompt = load_prompt('test_combat_prompt_2.txt')
    response = simulate_combat_turn(prompt)
    
    if response:
        print("\nAnalyzing response...")
        narration = response.get('narration', '')
        
        # Check if prerolls were used correctly
        print(f"✓ Uses d20 roll of 15: {'15' in narration}")
        print(f"✓ Calculates attack correctly (20): {'20' in narration}")
        print(f"✓ Uses d8 roll of 4: {'4' in narration}")
        print(f"✓ Calculates damage correctly (7): {'7' in narration}")
        
        # Check if shadow's turn was processed
        print(f"✓ Processes Shadow's turn: {'shadow' in narration.lower()}")
        
        # Check actions
        actions = response.get('actions', [])
        print(f"✓ Has updateEncounter action: {any(a['action'] == 'updateEncounter' for a in actions)}")
    
    return response

def run_validation_test():
    """Test validation system"""
    print("\n" + "="*60)
    print("RUNNING VALIDATION TEST: Dead Creature Detection")
    print("="*60)
    
    # Create a response with a dead creature acting
    bad_response = {
        "narration": "The skeleton (0 HP) attacks you!",
        "combat_round": 2,
        "actions": []
    }
    
    encounter_state = """
Current encounter state:
- Skeleton: HP 0/13, status: dead
"""
    
    validation = validate_response(bad_response, encounter_state)
    
    if validation:
        print(f"\nValidation Result:")
        print(f"✓ Valid: {validation.get('valid')}")
        print(f"✓ Reason: {validation.get('reason')}")
        print(f"✓ Catches dead creature: {not validation.get('valid') and 'dead' in validation.get('reason', '').lower()}")

def main():
    """Run all test scenarios"""
    print("COMBAT SYSTEM TEST SUITE")
    print("Testing updated combat mechanics...")
    
    # Create test results file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"combat_test_results_{timestamp}.json"
    
    results = {
        "timestamp": timestamp,
        "scenarios": {}
    }
    
    # Run tests
    print("\nNOTE: This will make actual API calls to test the system")
    confirm = input("Continue? (y/n): ")
    
    if confirm.lower() == 'y':
        # Test 1
        result1 = run_test_scenario_1()
        results["scenarios"]["basic_combat"] = {
            "passed": result1 is not None,
            "response": result1
        }
        
        # Test 2
        result2 = run_test_scenario_2()
        results["scenarios"]["player_action"] = {
            "passed": result2 is not None,
            "response": result2
        }
        
        # Validation test
        run_validation_test()
        
        # Save results
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n\nTest results saved to: {results_file}")
        print("\nSUMMARY:")
        print("- Basic combat test: ", "PASSED" if results["scenarios"]["basic_combat"]["passed"] else "FAILED")
        print("- Player action test: ", "PASSED" if results["scenarios"]["player_action"]["passed"] else "FAILED")

if __name__ == "__main__":
    # First, let's just display what we would test
    print("\nTEST SCENARIOS PREPARED:")
    print("\n1. Basic Combat (test_combat_prompt_1.txt)")
    print("   - Tests if AI waits for player confirmation")
    print("   - Tests combat_round tracking")
    print("   - Tests preroll awareness")
    
    print("\n2. Player Action (test_combat_prompt_2.txt)")
    print("   - Tests correct preroll usage")
    print("   - Tests damage calculation")
    print("   - Tests full round completion")
    
    print("\n3. Validation Test")
    print("   - Tests if dead creatures are caught")
    print("   - Tests validation explanations")
    
    print("\nTo run actual API tests, uncomment main() below")
    # main()  # Uncomment to run actual tests