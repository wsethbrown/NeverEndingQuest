#!/usr/bin/env python3
"""
DM System Integration Test Runner

Orchestrates comprehensive testing of the DM system using predefined scenarios
and validation rules.
"""

import json
import sys
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openai import OpenAI
from config import OPENAI_API_KEY, DM_MAIN_MODEL
from dm_response_validator import DMResponseValidator
import subprocess


class DMTestRunner:
    """Orchestrates DM system testing"""
    
    def __init__(self, scenarios_file: str = "dm_test_scenarios.json"):
        self.scenarios_file = scenarios_file
        self.scenarios = self.load_scenarios()
        self.validator = DMResponseValidator()
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = DM_MAIN_MODEL
        self.results = []
        self.summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "by_category": {},
            "by_action": {},
            "errors": []
        }
    
    def load_scenarios(self) -> Dict:
        """Load test scenarios from JSON file"""
        try:
            with open(self.scenarios_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading scenarios: {e}")
            return {"test_scenarios": [], "validation_rules": {}}
    
    def get_system_prompt(self) -> str:
        """Load the actual system prompt used by the game"""
        try:
            with open("system_prompt.txt", "r", encoding="utf-8") as f:
                return f.read()
        except:
            # Fallback to test prompt
            return """You are a D&D 5e Dungeon Master. You must ALWAYS respond with a JSON object in this exact format:

{
  "narration": "Your descriptive text and dialogue here",
  "actions": [
    {
      "action": "actionType",
      "parameters": {}
    }
  ]
}

Available actions: updateCharacterInfo, transitionLocation, createEncounter, updatePlot, updateTime, levelUp, updatePartyNPCs, createNewModule, establishHub, storageInteraction, exitGame"""
    
    def run_scenario(self, scenario: Dict) -> Dict:
        """Run a single test scenario"""
        print(f"\nRunning: {scenario['name']} ({scenario['id']})")
        print("-" * 40)
        
        start_time = time.time()
        
        # Get DM response
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": scenario["prompt"]}
                ],
                temperature=0.7
            )
            dm_response = response.choices[0].message.content.strip()
            response_time = time.time() - start_time
            
        except Exception as e:
            return {
                "scenario_id": scenario["id"],
                "scenario_name": scenario["name"],
                "category": scenario["category"],
                "success": False,
                "errors": [f"API Error: {str(e)}"],
                "response_time": 0,
                "response": None
            }
        
        # Validate response
        is_valid, errors, parsed_data = self.validator.validate_response(
            dm_response, scenario
        )
        
        # Extract action types for statistics
        action_types = [a["action"] for a in parsed_data.get("actions", [])]
        
        result = {
            "scenario_id": scenario["id"],
            "scenario_name": scenario["name"],
            "category": scenario["category"],
            "success": is_valid,
            "errors": errors,
            "response_time": response_time,
            "response": dm_response,
            "parsed_data": parsed_data,
            "action_types": action_types,
            "validation_summary": self.validator.get_validation_summary()
        }
        
        # Print immediate feedback
        if is_valid:
            print(f"[PASS] Response valid in {response_time:.2f}s")
            if action_types:
                print(f"       Actions: {', '.join(action_types)}")
        else:
            print(f"[FAIL] {len(errors)} errors found:")
            for error in errors[:3]:  # Show first 3 errors
                print(f"       - {error}")
            if len(errors) > 3:
                print(f"       ... and {len(errors) - 3} more")
        
        return result
    
    def run_all_scenarios(self):
        """Run all test scenarios"""
        scenarios = self.scenarios.get("test_scenarios", [])
        
        print("=" * 80)
        print("DM SYSTEM INTEGRATION TEST")
        print("=" * 80)
        print(f"Model: {self.model}")
        print(f"Scenarios: {len(scenarios)}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        for scenario in scenarios:
            result = self.run_scenario(scenario)
            self.results.append(result)
            self.update_summary(result)
            
            # Brief pause to avoid rate limiting
            time.sleep(0.5)
        
        self.print_summary()
        self.save_detailed_results()
    
    def update_summary(self, result: Dict):
        """Update running summary statistics"""
        self.summary["total"] += 1
        
        if result["success"]:
            self.summary["passed"] += 1
        else:
            self.summary["failed"] += 1
            self.summary["errors"].extend(result["errors"])
        
        # Update category statistics
        category = result["category"]
        if category not in self.summary["by_category"]:
            self.summary["by_category"][category] = {"total": 0, "passed": 0}
        self.summary["by_category"][category]["total"] += 1
        if result["success"]:
            self.summary["by_category"][category]["passed"] += 1
        
        # Update action type statistics
        for action_type in result["action_types"]:
            if action_type not in self.summary["by_action"]:
                self.summary["by_action"][action_type] = {"total": 0, "passed": 0}
            self.summary["by_action"][action_type]["total"] += 1
            if result["success"]:
                self.summary["by_action"][action_type]["passed"] += 1
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        # Overall results
        print(f"\nOVERALL RESULTS:")
        print(f"  Total Tests: {self.summary['total']}")
        print(f"  Passed: {self.summary['passed']}")
        print(f"  Failed: {self.summary['failed']}")
        if self.summary['total'] > 0:
            success_rate = (self.summary['passed'] / self.summary['total']) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
        
        # Results by category
        print(f"\nRESULTS BY CATEGORY:")
        for category, stats in sorted(self.summary["by_category"].items()):
            success_rate = (stats["passed"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            print(f"  {category:20s}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Results by action type
        print(f"\nRESULTS BY ACTION TYPE:")
        for action, stats in sorted(self.summary["by_action"].items()):
            success_rate = (stats["passed"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            print(f"  {action:25s}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        # Common errors
        if self.summary["errors"]:
            print(f"\nCOMMON ERRORS:")
            error_counts = {}
            for error in self.summary["errors"]:
                # Simplify error for grouping
                error_key = error.split(":")[0] if ":" in error else error
                error_counts[error_key] = error_counts.get(error_key, 0) + 1
            
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {error}: {count} occurrences")
        
        # Performance metrics
        response_times = [r["response_time"] for r in self.results if r["response_time"] > 0]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            print(f"\nPERFORMANCE METRICS:")
            print(f"  Average Response Time: {avg_time:.2f}s")
            print(f"  Min Response Time: {min_time:.2f}s")
            print(f"  Max Response Time: {max_time:.2f}s")
        
        print("=" * 80)
    
    def save_detailed_results(self):
        """Save detailed test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save full results
        results_file = f"dm_integration_test_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "model": self.model,
                    "scenarios_file": self.scenarios_file,
                    "total_scenarios": len(self.results)
                },
                "summary": self.summary,
                "detailed_results": self.results
            }, f, indent=2)
        
        print(f"\nDetailed results saved to: {results_file}")
        
        # Save failed scenarios for debugging
        failed_scenarios = [r for r in self.results if not r["success"]]
        if failed_scenarios:
            failures_file = f"dm_test_failures_{timestamp}.json"
            with open(failures_file, 'w') as f:
                json.dump(failed_scenarios, f, indent=2)
            print(f"Failed scenarios saved to: {failures_file}")
        
        # Generate markdown report
        self.generate_markdown_report(timestamp)
    
    def generate_markdown_report(self, timestamp: str):
        """Generate a markdown report of test results"""
        report_file = f"dm_test_report_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write("# DM System Test Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Model:** {self.model}\n")
            f.write(f"**Total Scenarios:** {self.summary['total']}\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            success_rate = (self.summary['passed'] / self.summary['total']) * 100 if self.summary['total'] > 0 else 0
            f.write(f"- **Passed:** {self.summary['passed']}\n")
            f.write(f"- **Failed:** {self.summary['failed']}\n")
            f.write(f"- **Success Rate:** {success_rate:.1f}%\n\n")
            
            # Category breakdown
            f.write("## Results by Category\n\n")
            f.write("| Category | Passed | Total | Success Rate |\n")
            f.write("|----------|--------|-------|-------------|\n")
            for category, stats in sorted(self.summary["by_category"].items()):
                rate = (stats["passed"] / stats["total"]) * 100 if stats["total"] > 0 else 0
                f.write(f"| {category} | {stats['passed']} | {stats['total']} | {rate:.1f}% |\n")
            
            # Failed scenarios
            failed = [r for r in self.results if not r["success"]]
            if failed:
                f.write("\n## Failed Scenarios\n\n")
                for result in failed:
                    f.write(f"### {result['scenario_name']}\n\n")
                    f.write(f"**ID:** {result['scenario_id']}\n")
                    f.write(f"**Category:** {result['category']}\n")
                    f.write(f"**Errors:**\n")
                    for error in result['errors']:
                        f.write(f"- {error}\n")
                    f.write("\n")
            
            # Sample successful responses
            passed = [r for r in self.results if r["success"]][:3]
            if passed:
                f.write("\n## Sample Successful Responses\n\n")
                for result in passed:
                    f.write(f"### {result['scenario_name']}\n\n")
                    f.write("**Response:**\n```json\n")
                    f.write(json.dumps(result['parsed_data'], indent=2))
                    f.write("\n```\n\n")
        
        print(f"Markdown report saved to: {report_file}")
    
    def run_subset(self, category: str = None, action_type: str = None):
        """Run a subset of scenarios based on category or action type"""
        scenarios = self.scenarios.get("test_scenarios", [])
        
        if category:
            scenarios = [s for s in scenarios if s["category"] == category]
            print(f"Running {len(scenarios)} scenarios in category: {category}")
        
        if action_type:
            # Filter by expected action type
            filtered = []
            for s in scenarios:
                expected = s.get("expected_response", {})
                if action_type in expected.get("required_actions", []):
                    filtered.append(s)
            scenarios = filtered
            print(f"Running {len(scenarios)} scenarios with action: {action_type}")
        
        if not scenarios:
            print("No scenarios match the filter criteria")
            return
        
        # Run filtered scenarios
        self.scenarios["test_scenarios"] = scenarios
        self.run_all_scenarios()


def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run DM system integration tests")
    parser.add_argument("--category", help="Run only scenarios in this category")
    parser.add_argument("--action", help="Run only scenarios testing this action")
    parser.add_argument("--scenarios", default="dm_test_scenarios.json", 
                       help="Path to scenarios file")
    parser.add_argument("--quick", action="store_true", 
                       help="Run a quick subset of tests")
    
    args = parser.parse_args()
    
    runner = DMTestRunner(args.scenarios)
    
    if args.quick:
        # Run a representative subset
        quick_scenarios = [
            "basic_narration",
            "damage_update",
            "location_transition",
            "multiple_actions_combat",
            "invalid_location"
        ]
        all_scenarios = runner.scenarios.get("test_scenarios", [])
        runner.scenarios["test_scenarios"] = [
            s for s in all_scenarios if s["id"] in quick_scenarios
        ]
        print("Running quick test subset...")
        runner.run_all_scenarios()
    elif args.category or args.action:
        runner.run_subset(args.category, args.action)
    else:
        runner.run_all_scenarios()
    
    # Return exit code based on results
    sys.exit(0 if runner.summary["failed"] == 0 else 1)


if __name__ == "__main__":
    main()