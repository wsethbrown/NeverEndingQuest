#!/usr/bin/env python3
"""
Automated test runner for DungeonMasterAI
Runs the game with an AI player instead of human input
"""

import json
import sys
import time
import argparse
from datetime import datetime
import threading
import queue

# Import game modules
from main import main_game_loop
from ai_player import AIPlayer, AIPlayerPersonality
from enhanced_logger import game_logger, game_event
from file_operations import safe_write_json, safe_read_json
from encoding_utils import safe_json_dump, safe_json_load

class AutomatedGameRunner:
    """Runs the game with AI player input"""
    
    def __init__(self, test_profile_name="thorough_explorer", max_actions=500):
        self.test_profile_name = test_profile_name
        self.max_actions = max_actions
        self.action_count = 0
        self.game_output_queue = queue.Queue()
        self.ai_input_queue = queue.Queue()
        self.game_thread = None
        self.running = False
        self.ai_player = None
        
        # Load test objectives
        self.test_objectives = safe_json_load("test_objectives.json")
        if not self.test_objectives:
            raise ValueError("Could not load test_objectives.json")
        
        # Get specific test profile
        self.test_profile = self.test_objectives["test_profiles"].get(test_profile_name)
        if not self.test_profile:
            raise ValueError(f"Test profile '{test_profile_name}' not found")
    
    def mock_input(self, prompt=""):
        """Mock input function that gets AI decisions"""
        # Send the prompt to AI player
        self.game_output_queue.put(prompt)
        
        # Wait for AI response
        ai_response = self.ai_input_queue.get(timeout=30)
        
        # Log the interaction
        game_logger.info(f"Game: {prompt}")
        game_logger.info(f"AI: {ai_response}")
        
        # Count actions
        self.action_count += 1
        
        # Check if we should stop
        if self.action_count >= self.max_actions:
            game_logger.warning(f"Reached maximum actions ({self.max_actions})")
            self.running = False
            return "exit game"
        
        return ai_response
    
    def mock_print(self, *args, **kwargs):
        """Mock print function that captures game output"""
        output = " ".join(str(arg) for arg in args)
        
        # Send to AI player
        self.game_output_queue.put(output)
        
        # Still print to console using original print
        import builtins
        if hasattr(builtins, '_original_print'):
            builtins._original_print(*args, **kwargs)
        else:
            # Fallback if original print is not saved
            import sys
            sys.stdout.write(output + '\n')
    
    def run_game_thread(self):
        """Run the game in a separate thread"""
        try:
            # Monkey patch input and print
            import builtins
            original_input = builtins.input
            original_print = builtins.print
            
            # Save original print for mock_print to use
            builtins._original_print = original_print
            
            builtins.input = self.mock_input
            builtins.print = self.mock_print
            
            # Run the game
            main_game_loop()
            
            # Restore original functions
            builtins.input = original_input
            builtins.print = original_print
            
        except Exception as e:
            game_logger.error(f"Game thread error: {str(e)}")
            self.running = False
    
    def run_ai_thread(self):
        """Run the AI player in a separate thread"""
        try:
            while self.running:
                try:
                    # Get game output
                    game_output = self.game_output_queue.get(timeout=1)
                    
                    if game_output:
                        # Get AI decision
                        ai_action = self.ai_player.get_next_action(game_output)
                        
                        # Only process non-None actions (filtered output)
                        if ai_action:
                            # Send action to game
                            self.ai_input_queue.put(ai_action)
                            
                            # Check for special commands
                            if "ISSUE DETECTED:" in ai_action:
                                game_logger.warning(f"AI reported issue: {ai_action}")
                            
                            if ai_action.lower() in ["exit game", "quit", "exit"]:
                                game_logger.info("AI requested game exit")
                                self.running = False
                            
                except queue.Empty:
                    continue
                    
        except Exception as e:
            game_logger.error(f"AI thread error: {str(e)}")
            self.running = False
    
    def run_test(self):
        """Run the automated test"""
        game_logger.info(f"Starting automated test: {self.test_profile_name}")
        game_event("test_start", {
            "profile": self.test_profile_name,
            "max_actions": self.max_actions
        })
        
        # Initialize AI player (will read campaign from party_tracker.json)
        self.ai_player = AIPlayer(self.test_profile)
        
        # Set up test environment
        self.setup_test_environment()
        
        # Start threads
        self.running = True
        
        self.game_thread = threading.Thread(target=self.run_game_thread)
        self.ai_thread = threading.Thread(target=self.run_ai_thread)
        
        self.game_thread.start()
        time.sleep(2)  # Let game initialize
        self.ai_thread.start()
        
        # Monitor progress
        start_time = time.time()
        expected_duration = self.test_profile.get("expected_duration_minutes", 60) * 60
        
        while self.running and self.game_thread.is_alive():
            time.sleep(5)
            
            # Check timeout
            if time.time() - start_time > expected_duration * 1.5:
                game_logger.warning("Test exceeded expected duration")
                self.running = False
            
            # Status update
            if self.action_count % 10 == 0:
                game_logger.info(f"Progress: {self.action_count} actions taken")
        
        # Clean up
        self.running = False
        
        if self.game_thread.is_alive():
            self.ai_input_queue.put("exit game")
            self.game_thread.join(timeout=10)
        
        if self.ai_thread.is_alive():
            self.ai_thread.join(timeout=5)
        
        # Generate report
        test_results_file = self.ai_player.save_test_results()
        
        game_logger.info(f"Test completed: {self.action_count} actions taken")
        game_event("test_complete", {
            "profile": self.test_profile_name,
            "actions": self.action_count,
            "issues_found": len(self.ai_player.issues_found),
            "results_file": test_results_file
        })
        
        return test_results_file
    
    def setup_test_environment(self):
        """Set up a clean test environment"""
        # Create test-specific directories
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_dir = f"test_runs/{self.test_profile_name}_{timestamp}"
        
        import os
        os.makedirs(test_dir, exist_ok=True)
        
        # Copy necessary files
        import shutil
        
        # Start with fresh party tracker
        test_party_tracker = {
            "campaign": "Keep_of_Doom",
            "partyMembers": ["norn"],
            "partyNPCs": [],
            "worldConditions": {
                "year": 1492,
                "month": "Ches", 
                "day": 1,
                "time": "08:00:00",
                "weather": "Overcast",
                "season": "Spring",
                "dayNightCycle": "Morning",
                "moonPhase": "New Moon",
                "currentLocation": "Harrow's Hollow General Store",
                "currentLocationId": "R01",
                "currentArea": "Harrow's Hollow",
                "currentAreaId": "HH001",
                "majorEventsUnderway": [],
                "politicalClimate": "",
                "activeEncounter": "",
                "activeCombatEncounter": ""
            },
            "activeQuests": []
        }
        
        safe_json_dump(test_party_tracker, "party_tracker.json")
        
        # Clear conversation history
        if os.path.exists("conversation_history.json"):
            os.remove("conversation_history.json")
        
        # Clear journal
        safe_json_dump({"campaign": "Keep_of_Doom", "entries": []}, "journal.json")
        
        game_logger.info(f"Test environment set up in {test_dir}")

def main():
    """Main entry point for automated testing"""
    parser = argparse.ArgumentParser(description="Run automated tests for DungeonMasterAI")
    parser.add_argument(
        "profile",
        nargs="?",
        default="thorough_explorer",
        help="Test profile to run (default: thorough_explorer)"
    )
    parser.add_argument(
        "--max-actions",
        type=int,
        default=500,
        help="Maximum number of actions before stopping (default: 500)"
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available test profiles"
    )
    
    args = parser.parse_args()
    
    # List profiles if requested
    if args.list_profiles:
        objectives = safe_json_load("test_objectives.json")
        if objectives:
            print("\nAvailable test profiles:")
            for name, profile in objectives["test_profiles"].items():
                print(f"  {name:25} - {profile['description']}")
                print(f"  {'':25}   Expected duration: {profile.get('expected_duration_minutes', '?')} minutes")
                print()
        return
    
    # Run the test
    try:
        runner = AutomatedGameRunner(
            test_profile_name=args.profile,
            max_actions=args.max_actions
        )
        
        results_file = runner.run_test()
        
        print(f"\nTest completed successfully!")
        print(f"Results saved to: {results_file}")
        
        # Show summary
        results = safe_json_load(results_file)
        if results:
            print(f"\nTest Summary:")
            print(f"  Profile: {results['test_profile']}")
            print(f"  Actions taken: {results['total_actions']}")
            print(f"  Issues found: {results['issues_found']}")
            print(f"  Objectives completed: {results['objectives_completed']}/{results['objectives_attempted']}")
            
            if results['issues_found'] > 0:
                print(f"\nIssues detected:")
                for issue in results['issues_detail'][:5]:  # Show first 5
                    print(f"  - {issue['type']} at {issue['location']}")
                if len(results['issues_detail']) > 5:
                    print(f"  ... and {len(results['issues_detail']) - 5} more")
        
    except Exception as e:
        print(f"Error running test: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())