#!/usr/bin/env python3
"""
Quick test launcher for common test scenarios
"""

import subprocess
import sys

def run_test(profile, max_actions=None):
    """Run a test with the given profile"""
    cmd = ["python", "run_automated_test.py", profile]
    if max_actions:
        cmd.extend(["--max-actions", str(max_actions)])
    
    subprocess.run(cmd)

def main():
    print("\n=== DungeonMasterAI Quick Test Launcher ===\n")
    print("Select a test to run:")
    print("1. Quick Exploration (15 min) - Basic village exploration")
    print("2. Combat Test (30 min) - Test combat mechanics") 
    print("3. Skill Check Test (20 min) - Verify skill checks work")
    print("4. Bug Hunter (30 min) - Try to break things")
    print("5. Main Quest (90 min) - Full storyline test")
    print("6. Full Test Suite (4+ hours) - Run all tests")
    print("0. Exit")
    
    choice = input("\nEnter choice (0-6): ").strip()
    
    if choice == "1":
        print("\nRunning Quick Exploration Test...")
        run_test("thorough_explorer", 50)
    elif choice == "2":
        print("\nRunning Combat Test...")
        run_test("combat_stress_test", 100)
    elif choice == "3":
        print("\nRunning Skill Check Test...")
        run_test("skill_check_validator", 75)
    elif choice == "4":
        print("\nRunning Bug Hunter Test...")
        run_test("edge_case_hunter", 100)
    elif choice == "5":
        print("\nRunning Main Quest Test...")
        run_test("main_quest_speedrun", 200)
    elif choice == "6":
        print("\nRunning Full Test Suite...")
        profiles = [
            ("thorough_explorer", 100),
            ("skill_check_validator", 100),
            ("combat_stress_test", 150),
            ("edge_case_hunter", 150),
            ("main_quest_speedrun", 300),
            ("narrative_completionist", 400)
        ]
        
        for profile, actions in profiles:
            print(f"\n\n=== Running {profile} ===")
            run_test(profile, actions)
            print("\nPress Enter to continue to next test...")
            input()
    elif choice == "0":
        print("Exiting...")
        return
    else:
        print("Invalid choice")
        return
    
    print("\nTest completed! Check test_results_*.json for details")

if __name__ == "__main__":
    main()