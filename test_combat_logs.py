#!/usr/bin/env python3
"""
Test script for the combat logging functionality in combat_manager.py.
This script creates a mock combat session and tests the logging features.
"""

import os
import json
import shutil
from datetime import datetime
from combat_manager import generate_chat_history

def create_test_conversation():
    """Create a mock conversation history for testing"""
    return [
        {"role": "system", "content": "This is a system prompt that should be filtered out."},
        {"role": "assistant", "content": "Welcome to the combat encounter!"},
        {"role": "user", "content": "I attack the goblin with my sword."},
        {"role": "assistant", "content": "You swing your sword at the goblin, hitting it for 6 damage."},
        {"role": "system", "content": "Another system message to filter out."},
        {"role": "user", "content": "I'll use my bonus action to move behind cover."},
        {"role": "assistant", "content": "You move swiftly behind a large rock, providing you with partial cover."}
    ]

def cleanup_test_files(encounter_id):
    """Remove test files and directories created during testing"""
    encounter_dir = f"combat_logs/{encounter_id}"
    if os.path.exists(encounter_dir):
        shutil.rmtree(encounter_dir)
    
    all_latest_file = "combat_logs/all_combat_latest.json"
    if os.path.exists(all_latest_file):
        os.remove(all_latest_file)

def verify_log_files(encounter_id):
    """Verify that log files were created correctly"""
    encounter_dir = f"combat_logs/{encounter_id}"
    latest_file = f"{encounter_dir}/combat_chat_latest.json"
    all_latest_file = "combat_logs/all_combat_latest.json"
    
    success = True
    errors = []
    
    # Check if encounter directory was created
    if not os.path.exists(encounter_dir):
        success = False
        errors.append(f"Encounter directory '{encounter_dir}' was not created")
    
    # Check if latest file was created
    if not os.path.exists(latest_file):
        success = False
        errors.append(f"Latest file '{latest_file}' was not created")
    else:
        # Check if latest file has correct content
        with open(latest_file, "r", encoding="utf-8") as f:
            content = json.load(f)
            # Should be a list of messages with system messages filtered out
            if not isinstance(content, list) or len(content) != 5:
                success = False
                errors.append(f"Latest file '{latest_file}' has incorrect content structure. Expected 5 messages, got {len(content) if isinstance(content, list) else 'not a list'}")
    
    # Check if combined file was created
    if not os.path.exists(all_latest_file):
        success = False
        errors.append(f"Combined latest file '{all_latest_file}' was not created")
    else:
        # Check if combined file has correct content
        with open(all_latest_file, "r", encoding="utf-8") as f:
            content = json.load(f)
            if not isinstance(content, dict) or encounter_id not in content:
                success = False
                errors.append(f"Combined latest file '{all_latest_file}' has incorrect content structure")
    
    return success, errors

def test_combat_logging():
    """Test the combat logging functionality"""
    print("Testing combat logging functionality...")
    
    # Create a test encounter ID
    test_encounter_id = "TEST-E1"
    
    # Clean up any existing test files
    cleanup_test_files(test_encounter_id)
    
    # Create test conversation history
    conversation_history = create_test_conversation()
    
    # Call the generate_chat_history function
    print("\nGenerating test combat logs...")
    generate_chat_history(conversation_history, test_encounter_id)
    
    # Verify the results
    success, errors = verify_log_files(test_encounter_id)
    
    if success:
        print("\nTEST PASSED: Combat logging functionality is working correctly!")
        
        # Display test files
        print("\nTest files created:")
        encounter_dir = f"combat_logs/{test_encounter_id}"
        for file in os.listdir(encounter_dir):
            print(f"- {encounter_dir}/{file}")
        print(f"- combat_logs/all_combat_latest.json")
        
        # Automatically clean up test files when running automated tests
        # Comment out the next line if you want to keep test files for manual inspection
        cleanup_test_files(test_encounter_id)
        print("Test files have been automatically removed.")
        print("To preserve test files in the future, comment out the cleanup_test_files() line in the script.")
    else:
        print("\nTEST FAILED: Combat logging functionality has issues:")
        for error in errors:
            print(f"- {error}")

if __name__ == "__main__":
    # Make sure the combat_logs directory exists
    os.makedirs("combat_logs", exist_ok=True)
    
    # Run the test
    test_combat_logging()