#!/usr/bin/env python3
"""
Synthetic test for path validation integration in main.py
Tests the path validation logic without running the full DM system
"""

import json
import re
import sys
import os

# Add the current directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from location_path_finder import LocationGraph


def test_path_validation_logic():
    """Test the exact logic that's integrated into main.py"""
    
    print("=" * 60)
    print("TESTING PATH VALIDATION INTEGRATION")
    print("=" * 60)
    
    # Initialize location graph (same as main.py)
    try:
        location_graph = LocationGraph()
        location_graph.load_module_data()
        print("✓ Location graph initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize location graph: {e}")
        return False
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Valid transition (same area)",
            "current_location_id": "A01", 
            "ai_response": '{"narration": "You head to the town square.", "actions": [{"action": "transitionLocation", "parameters": {"newLocation": "A02"}}]}',
            "should_succeed": True
        },
        {
            "name": "Valid transition (cross-area)",
            "current_location_id": "A02",
            "ai_response": '{"narration": "You enter the secret passage.", "actions": [{"action": "transitionLocation", "parameters": {"newLocation": "C08"}}]}',
            "should_succeed": True
        },
        {
            "name": "AI provides location name instead of ID",
            "current_location_id": "A01",
            "ai_response": '{"narration": "You go to the town square.", "actions": [{"action": "transitionLocation", "parameters": {"newLocation": "Town Square"}}]}',
            "should_succeed": False
        },
        {
            "name": "Invalid destination",
            "current_location_id": "A01",
            "ai_response": '{"narration": "You go somewhere.", "actions": [{"action": "transitionLocation", "parameters": {"newLocation": "XXX"}}]}',
            "should_succeed": False
        },
        {
            "name": "Malformed JSON",
            "current_location_id": "A01", 
            "ai_response": '{"narration": "You go somewhere.", "actions": [{"action": "transitionLocation", "parameters": {"newLocation": "}}]}',
            "should_succeed": False
        },
        {
            "name": "No newLocation parameter",
            "current_location_id": "A01",
            "ai_response": '{"narration": "You go somewhere.", "actions": [{"action": "transitionLocation", "parameters": {}}]}',
            "should_succeed": False
        },
        {
            "name": "Missing current location",
            "current_location_id": None,
            "ai_response": '{"narration": "You go somewhere.", "actions": [{"action": "transitionLocation", "parameters": {"newLocation": "A02"}}]}',
            "should_succeed": False
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\nTest {i}: {scenario['name']}")
        print(f"  Current: {scenario['current_location_id']}")
        print(f"  AI Response: {scenario['ai_response']}")
        
        # Simulate the exact logic from main.py validate_ai_response function
        location_details = "Location Details: Test location"
        current_location_id = scenario['current_location_id']
        primary_response = scenario['ai_response']
        
        # === COPIED LOGIC FROM MAIN.PY ===
        if '"action": "transitionLocation"' in primary_response:
            try:
                # Extract the destination from the AI response
                destination_match = re.search(r'"newLocation":\s*"([^"]*)"', primary_response)
                if destination_match:
                    destination = destination_match.group(1).strip()
                    current_origin = current_location_id
                    
                    # Validate we have required data
                    if not destination:
                        path_info = f"Path Validation ERROR: Empty destination in transitionLocation action."
                    elif not current_origin:
                        path_info = f"Path Validation ERROR: Current location ID not available in party tracker."
                    elif not location_graph:
                        path_info = f"Path Validation ERROR: Location graph not initialized."
                    else:
                        # Validate path using location graph
                        success, path, message = location_graph.find_path(current_origin, destination)
                        
                        if success:
                            path_info = f"The party is currently at {current_origin} and desires to travel to {destination}. The path of travel is: {' -> '.join(path)}."
                        else:
                            path_info = f"The party is currently at {current_origin} and desires to travel to {destination}. WARNING: {message}"
                    
                    # Add path validation to location details
                    location_details += f"\n\nPath Validation: {path_info}"
                else:
                    # transitionLocation detected but no newLocation parameter found
                    location_details += f"\n\nPath Validation ERROR: transitionLocation action detected but destination could not be extracted."
                    
            except Exception as e:
                # Catch any unexpected errors in path validation
                location_details += f"\n\nPath Validation ERROR: Failed to validate path - {str(e)}"
        # === END COPIED LOGIC ===
        
        # Check if validation was added
        has_path_validation = "Path Validation:" in location_details
        
        print(f"  Result: {'✓' if has_path_validation else '✗'} Path validation {'added' if has_path_validation else 'NOT added'}")
        
        if has_path_validation:
            # Extract the path validation part
            path_validation_line = location_details.split("Path Validation: ")[1]
            print(f"  Validation: {path_validation_line}")
            
            # Check if it succeeded as expected
            is_error = "ERROR:" in path_validation_line or "WARNING:" in path_validation_line
            actual_success = not is_error
            
            if actual_success == scenario['should_succeed']:
                print(f"  Status: ✓ PASS (expected {'success' if scenario['should_succeed'] else 'failure'})")
                passed += 1
            else:
                print(f"  Status: ✗ FAIL (expected {'success' if scenario['should_succeed'] else 'failure'}, got {'success' if actual_success else 'failure'})")
                failed += 1
        else:
            print(f"  Status: ✗ FAIL (no path validation added)")
            failed += 1
    
    print(f"\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = test_path_validation_logic()
    sys.exit(0 if success else 1)