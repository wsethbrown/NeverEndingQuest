#!/usr/bin/env python3
"""
Enhanced Test Runner for DungeonMasterAI
Comprehensive testing framework with isolated environments and feature discovery
"""

import json
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import queue

from isolated_test_environment import create_isolated_test_environment
from run_automated_test import AutomatedGameRunner
from enhanced_logger import game_logger, game_event
from encoding_utils import safe_json_load, safe_json_dump

class EnhancedTestRunner:
    """Enhanced test runner with comprehensive feature testing and isolation"""
    
    def __init__(self):
        self.test_results = {}
        self.test_environments = {}
        self.validation_results = {}
        
    def run_comprehensive_test_suite(self, test_profiles: Optional[List[str]] = None) -> Dict:
        """Run comprehensive test suite across multiple profiles"""
        
        # Load test objectives
        objectives = safe_json_load("test_objectives.json")
        if not objectives:
            raise ValueError("Could not load test_objectives.json")
        
        # Use specified profiles or run all
        if test_profiles is None:
            test_profiles = list(objectives["test_profiles"].keys())
        
        suite_results = {
            "suite_start_time": datetime.now().isoformat(),
            "profiles_tested": test_profiles,
            "individual_results": {},
            "summary": {},
            "validation_report": {}
        }
        
        game_logger.info(f"Starting comprehensive test suite with {len(test_profiles)} profiles")
        
        # Run each test profile in isolated environments
        for profile_name in test_profiles:
            game_logger.info(f"Running test profile: {profile_name}")
            
            try:
                # Create isolated environment for this test
                with create_isolated_test_environment(f"profile_{profile_name}") as test_env:
                    
                    # Run the test in isolation
                    test_result = self._run_isolated_test(profile_name, test_env)
                    suite_results["individual_results"][profile_name] = test_result
                    
                    # Validate test results
                    validation = self._validate_test_results(profile_name, test_result, objectives)
                    suite_results["validation_report"][profile_name] = validation
                    
            except Exception as e:
                game_logger.error(f"Test profile {profile_name} failed: {str(e)}")
                suite_results["individual_results"][profile_name] = {
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        # Generate summary
        suite_results["summary"] = self._generate_suite_summary(suite_results)
        suite_results["suite_end_time"] = datetime.now().isoformat()
        
        # Save comprehensive results
        results_file = f"comprehensive_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        safe_json_dump(suite_results, results_file)
        
        game_logger.info(f"Comprehensive test suite completed. Results: {results_file}")
        return suite_results
    
    def _run_isolated_test(self, profile_name: str, test_env) -> Dict:
        """Run a single test profile in isolated environment"""
        try:
            # Initialize automated game runner in the isolated environment
            runner = AutomatedGameRunner(
                test_profile_name=profile_name,
                max_actions=1000  # Increased for comprehensive testing
            )
            
            # Track additional metrics
            start_time = time.time()
            
            # Run the test
            results_file = runner.run_test()
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Load and enhance results
            test_results = safe_json_load(results_file) if results_file else {}
            
            # Add enhanced metrics
            enhanced_results = {
                **test_results,
                "environment_info": {
                    "isolated": True,
                    "environment_path": str(test_env.isolated_dir),
                    "test_id": test_env.test_id
                },
                "performance_metrics": {
                    "total_duration_seconds": duration,
                    "actions_per_minute": (test_results.get("total_actions", 0) / duration) * 60 if duration > 0 else 0
                },
                "feature_coverage": self._analyze_feature_coverage(test_results),
                "discovery_analysis": self._analyze_discovery_patterns(test_results)
            }
            
            return enhanced_results
            
        except Exception as e:
            game_logger.error(f"Isolated test failed for {profile_name}: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "profile": profile_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_feature_coverage(self, test_results: Dict) -> Dict:
        """Analyze which features were tested during the run"""
        
        coverage = {
            "actions_used": {},
            "locations_visited": [],
            "features_discovered": [],
            "systems_tested": []
        }
        
        # Analyze action usage from conversation history
        conversation = test_results.get("conversation_log", [])
        action_counts = {}
        
        for entry in conversation:
            content = entry.get("content", "")
            
            # Look for action patterns
            if "transitionLocation" in content:
                action_counts["location_transitions"] = action_counts.get("location_transitions", 0) + 1
                coverage["systems_tested"].append("location_system")
                
            if "storageInteraction" in content:
                action_counts["storage_interactions"] = action_counts.get("storage_interactions", 0) + 1
                coverage["systems_tested"].append("storage_system")
                
            if "createEncounter" in content:
                action_counts["combat_encounters"] = action_counts.get("combat_encounters", 0) + 1
                coverage["systems_tested"].append("combat_system")
                
            if "updateCharacterInfo" in content:
                action_counts["character_updates"] = action_counts.get("character_updates", 0) + 1
                coverage["systems_tested"].append("character_system")
                
            # Look for location mentions
            if any(loc in content for loc in ["HH001", "G001", "SK001", "TBM001", "TCD001"]):
                location_match = next((loc for loc in ["HH001", "G001", "SK001", "TBM001", "TCD001"] if loc in content), None)
                if location_match and location_match not in coverage["locations_visited"]:
                    coverage["locations_visited"].append(location_match)
        
        coverage["actions_used"] = action_counts
        coverage["systems_tested"] = list(set(coverage["systems_tested"]))  # Remove duplicates
        
        return coverage
    
    def _analyze_discovery_patterns(self, test_results: Dict) -> Dict:
        """Analyze how the AI discovered features organically"""
        
        discovery = {
            "organic_discoveries": [],
            "help_requests": 0,
            "trial_and_error_patterns": [],
            "feature_accessibility_score": 0.0
        }
        
        conversation = test_results.get("conversation_log", [])
        
        for entry in conversation:
            content = entry.get("content", "").lower()
            
            # Look for discovery patterns
            if any(phrase in content for phrase in ["i try", "let me try", "i attempt", "experiment"]):
                discovery["trial_and_error_patterns"].append(entry.get("timestamp", "unknown"))
                
            if any(phrase in content for phrase in ["help", "how do i", "what can i do"]):
                discovery["help_requests"] += 1
                
            # Look for successful organic discoveries
            if any(phrase in content for phrase in ["i found", "discovered", "figured out"]):
                discovery["organic_discoveries"].append({
                    "timestamp": entry.get("timestamp", "unknown"),
                    "discovery": content[:100]  # First 100 chars
                })
        
        # Calculate accessibility score (lower help requests = higher accessibility)
        total_actions = test_results.get("total_actions", 1)
        if total_actions > 0:
            discovery["feature_accessibility_score"] = max(0.0, 1.0 - (discovery["help_requests"] / total_actions))
        
        return discovery
    
    def _validate_test_results(self, profile_name: str, test_results: Dict, objectives: Dict) -> Dict:
        """Validate test results against expected criteria"""
        
        profile_config = objectives["test_profiles"].get(profile_name, {})
        validation_criteria = objectives.get("validation_criteria", {})
        
        validation = {
            "profile_objectives_met": False,
            "feature_coverage_adequate": False,
            "performance_acceptable": False,
            "error_handling_validated": False,
            "details": {}
        }
        
        # Check if profile objectives were met
        objectives_met = 0
        total_objectives = len(profile_config.get("objectives", []))
        
        if total_objectives > 0:
            # Analyze if objectives were addressed
            coverage = test_results.get("feature_coverage", {})
            focus_areas = profile_config.get("focus_areas", [])
            
            for focus_area in focus_areas:
                if focus_area in coverage.get("systems_tested", []):
                    objectives_met += 1
            
            validation["profile_objectives_met"] = objectives_met >= (total_objectives * 0.7)  # 70% threshold
            validation["details"]["objectives_score"] = f"{objectives_met}/{total_objectives}"
        
        # Check feature coverage
        systems_tested = test_results.get("feature_coverage", {}).get("systems_tested", [])
        validation["feature_coverage_adequate"] = len(systems_tested) >= 2  # At least 2 systems
        validation["details"]["systems_tested"] = systems_tested
        
        # Check performance
        duration = test_results.get("performance_metrics", {}).get("total_duration_seconds", 0)
        expected_max = profile_config.get("expected_duration_minutes", 60) * 60 * 1.5  # 150% of expected
        validation["performance_acceptable"] = duration <= expected_max
        validation["details"]["duration_check"] = f"{duration}s <= {expected_max}s"
        
        # Check for errors
        issues_found = test_results.get("issues_found", 0)
        validation["error_handling_validated"] = issues_found < 5  # Arbitrary threshold
        validation["details"]["issues_found"] = issues_found
        
        return validation
    
    def _generate_suite_summary(self, suite_results: Dict) -> Dict:
        """Generate summary of comprehensive test suite"""
        
        individual_results = suite_results.get("individual_results", {})
        validation_report = suite_results.get("validation_report", {})
        
        summary = {
            "total_profiles": len(individual_results),
            "successful_tests": 0,
            "failed_tests": 0,
            "validation_passed": 0,
            "feature_coverage": {
                "systems_covered": set(),
                "locations_covered": set(),
                "total_actions": 0
            },
            "performance_summary": {
                "total_duration": 0,
                "average_duration": 0,
                "total_actions": 0,
                "average_actions_per_minute": 0
            },
            "issues_summary": {
                "total_issues": 0,
                "critical_issues": [],
                "common_issues": {}
            }
        }
        
        # Analyze individual results
        for profile_name, result in individual_results.items():
            if result.get("status") != "failed":
                summary["successful_tests"] += 1
                
                # Aggregate coverage data
                coverage = result.get("feature_coverage", {})
                summary["feature_coverage"]["systems_covered"].update(coverage.get("systems_tested", []))
                summary["feature_coverage"]["locations_covered"].update(coverage.get("locations_visited", []))
                summary["feature_coverage"]["total_actions"] += result.get("total_actions", 0)
                
                # Aggregate performance data
                perf = result.get("performance_metrics", {})
                summary["performance_summary"]["total_duration"] += perf.get("total_duration_seconds", 0)
                summary["performance_summary"]["total_actions"] += result.get("total_actions", 0)
                
                # Aggregate issues
                issues = result.get("issues_found", 0)
                summary["issues_summary"]["total_issues"] += issues
                
            else:
                summary["failed_tests"] += 1
        
        # Check validation results
        for profile_name, validation in validation_report.items():
            if all([
                validation.get("profile_objectives_met", False),
                validation.get("feature_coverage_adequate", False),
                validation.get("performance_acceptable", False)
            ]):
                summary["validation_passed"] += 1
        
        # Calculate averages
        if summary["successful_tests"] > 0:
            summary["performance_summary"]["average_duration"] = (
                summary["performance_summary"]["total_duration"] / summary["successful_tests"]
            )
            
        if summary["performance_summary"]["total_duration"] > 0:
            summary["performance_summary"]["average_actions_per_minute"] = (
                (summary["performance_summary"]["total_actions"] / summary["performance_summary"]["total_duration"]) * 60
            )
        
        # Convert sets to lists for JSON serialization
        summary["feature_coverage"]["systems_covered"] = list(summary["feature_coverage"]["systems_covered"])
        summary["feature_coverage"]["locations_covered"] = list(summary["feature_coverage"]["locations_covered"])
        
        return summary
    
    def run_discovery_focused_test(self, max_actions: int = 500) -> Dict:
        """Run special test focused on AI feature discovery without instructions"""
        
        game_logger.info("Starting discovery-focused test")
        
        with create_isolated_test_environment("discovery_test") as test_env:
            try:
                # Run feature discoverer profile
                runner = AutomatedGameRunner(
                    test_profile_name="feature_discoverer",
                    max_actions=max_actions
                )
                
                results_file = runner.run_test()
                results = safe_json_load(results_file) if results_file else {}
                
                # Enhanced discovery analysis
                discovery_analysis = self._detailed_discovery_analysis(results)
                
                enhanced_results = {
                    **results,
                    "test_type": "discovery_focused",
                    "discovery_analysis": discovery_analysis,
                    "accessibility_score": discovery_analysis.get("feature_accessibility_score", 0.0)
                }
                
                return enhanced_results
                
            except Exception as e:
                game_logger.error(f"Discovery test failed: {str(e)}")
                return {"status": "failed", "error": str(e)}
    
    def _detailed_discovery_analysis(self, test_results: Dict) -> Dict:
        """Detailed analysis of discovery patterns for AI accessibility"""
        
        analysis = self._analyze_discovery_patterns(test_results)
        
        # Add more detailed discovery metrics
        conversation = test_results.get("conversation_log", [])
        
        discovery_timeline = []
        feature_first_use = {}
        
        for i, entry in enumerate(conversation):
            content = entry.get("content", "")
            timestamp = entry.get("timestamp", f"step_{i}")
            
            # Track first use of each feature
            features = ["storage", "combat", "location", "character", "npc"]
            for feature in features:
                if feature in content.lower() and feature not in feature_first_use:
                    feature_first_use[feature] = {
                        "timestamp": timestamp,
                        "step": i,
                        "context": content[:200]
                    }
                    discovery_timeline.append({
                        "feature": feature,
                        "discovered_at_step": i,
                        "total_steps": len(conversation)
                    })
        
        analysis["discovery_timeline"] = discovery_timeline
        analysis["feature_first_use"] = feature_first_use
        analysis["discovery_efficiency"] = len(feature_first_use) / len(conversation) if conversation else 0
        
        return analysis

def backup_debug_log():
    """Backup previous game_debug.log with timestamp"""
    import os
    import shutil
    from datetime import datetime
    import logging
    
    debug_log_file = "game_debug.log"
    
    if os.path.exists(debug_log_file):
        # Create backup directory if it doesn't exist
        backup_dir = "debug_log_backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create timestamped backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"game_debug_{timestamp}.log"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        try:
            # Try to safely close any logging handlers first
            try:
                from enhanced_logger import game_logger
                # Get all handlers and temporarily close file handlers
                handlers_to_reopen = []
                for handler in game_logger.handlers[:]:
                    if hasattr(handler, 'stream') and hasattr(handler.stream, 'name'):
                        if handler.stream.name == debug_log_file:
                            handler.close()
                            game_logger.removeHandler(handler)
                            handlers_to_reopen.append(handler)
            except:
                pass  # If logger setup fails, continue anyway
            
            # Copy instead of move to avoid file lock issues
            shutil.copy2(debug_log_file, backup_path)
            print(f"Previous debug log backed up to: {backup_path}")
            
            # Truncate the original file to make it empty
            with open(debug_log_file, 'w') as f:
                pass  # Creates empty file
            print(f"Cleared {debug_log_file} for new test run")
            
            # Restore logging handlers if we had them
            try:
                for handler in handlers_to_reopen:
                    # Recreate the handler
                    new_handler = logging.FileHandler(debug_log_file)
                    new_handler.setFormatter(handler.formatter)
                    new_handler.setLevel(handler.level)
                    game_logger.addHandler(new_handler)
            except:
                pass  # If restoration fails, logging will recreate as needed
                
        except PermissionError as e:
            print(f"Warning: Could not backup debug log due to file lock: {e}")
            print("Continuing with existing log file...")
    else:
        print(f"No existing {debug_log_file} found - starting fresh")

def main():
    """Main entry point for enhanced testing"""
    parser = argparse.ArgumentParser(description="Enhanced automated testing for DungeonMasterAI")
    parser.add_argument(
        "--profiles",
        nargs="+",
        help="Specific test profiles to run"
    )
    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Run comprehensive test suite"
    )
    parser.add_argument(
        "--discovery",
        action="store_true", 
        help="Run discovery-focused test"
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available test profiles"
    )
    
    args = parser.parse_args()
    
    # Backup previous debug log before starting new test
    backup_debug_log()
    
    # List profiles if requested
    if args.list_profiles:
        objectives = safe_json_load("test_objectives.json")
        if objectives:
            print("\nAvailable test profiles:")
            for name, profile in objectives["test_profiles"].items():
                print(f"  {name:20} - {profile['description']}")
                print(f"  {'':20}   Duration: {profile.get('expected_duration_minutes', '?')} min")
                print(f"  {'':20}   Focus: {', '.join(profile.get('focus_areas', []))}")
                print()
        return 0
    
    # Initialize enhanced test runner
    runner = EnhancedTestRunner()
    
    try:
        if args.comprehensive:
            # Run comprehensive test suite
            results = runner.run_comprehensive_test_suite(args.profiles)
            
            print(f"\nComprehensive Test Suite Results:")
            summary = results.get("summary", {})
            print(f"  Total Profiles: {summary.get('total_profiles', 0)}")
            print(f"  Successful: {summary.get('successful_tests', 0)}")
            print(f"  Failed: {summary.get('failed_tests', 0)}")
            print(f"  Validation Passed: {summary.get('validation_passed', 0)}")
            print(f"  Systems Covered: {len(summary.get('feature_coverage', {}).get('systems_covered', []))}")
            print(f"  Total Actions: {summary.get('feature_coverage', {}).get('total_actions', 0)}")
            
        elif args.discovery:
            # Run discovery-focused test
            results = runner.run_discovery_focused_test()
            
            print(f"\nDiscovery Test Results:")
            print(f"  Status: {results.get('status', 'completed')}")
            print(f"  Actions: {results.get('total_actions', 0)}")
            print(f"  Accessibility Score: {results.get('accessibility_score', 0.0):.2f}")
            
            discovery = results.get("discovery_analysis", {})
            print(f"  Organic Discoveries: {len(discovery.get('organic_discoveries', []))}")
            print(f"  Help Requests: {discovery.get('help_requests', 0)}")
            print(f"  Features Discovered: {len(discovery.get('feature_first_use', {}))}")
            
        else:
            print("Please specify --comprehensive, --discovery, or --list-profiles")
            return 1
            
    except Exception as e:
        print(f"Error running enhanced tests: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())