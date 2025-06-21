#!/usr/bin/env python3
"""
Feature Discovery Tests for DungeonMasterAI
Specialized tests for AI discovery of non-obvious features like storage chests
"""

import json
from typing import Dict, List, Optional
from isolated_test_environment import create_isolated_test_environment
from enhanced_test_runner import EnhancedTestRunner
from enhanced_logger import game_logger
from encoding_utils import safe_json_load, safe_json_dump

class FeatureDiscoveryTester:
    """Specialized tester for AI discovery of game features"""
    
    def __init__(self):
        self.discovery_scenarios = self._load_discovery_scenarios()
        
    def _load_discovery_scenarios(self) -> Dict:
        """Load or create discovery test scenarios"""
        
        scenarios = {
            "storage_chest_discovery": {
                "name": "Storage Chest Discovery",
                "description": "Test AI ability to discover and use storage chest system",
                "objectives": [
                    "Discover that storage containers can be created",
                    "Successfully create a storage container", 
                    "Store items in the container",
                    "Retrieve items from the container",
                    "Understand container persistence"
                ],
                "hints_allowed": False,
                "max_actions": 200,
                "success_criteria": [
                    "created_storage_container",
                    "stored_items",
                    "retrieved_items"
                ]
            },
            "location_transition_discovery": {
                "name": "Location Transition Discovery", 
                "description": "Test AI ability to discover location movement mechanics",
                "objectives": [
                    "Discover available exits from current location",
                    "Understand movement commands",
                    "Successfully transition between areas",
                    "Navigate back to original location"
                ],
                "hints_allowed": False,
                "max_actions": 150,
                "success_criteria": [
                    "discovered_exits",
                    "successful_transitions",
                    "returned_to_origin"
                ]
            },
            "npc_interaction_discovery": {
                "name": "NPC Interaction Discovery",
                "description": "Test AI ability to discover and engage with NPCs",
                "objectives": [
                    "Identify NPCs in the environment",
                    "Initiate conversation with NPCs",
                    "Explore dialogue options",
                    "Discover quest or information mechanics"
                ],
                "hints_allowed": False,
                "max_actions": 250,
                "success_criteria": [
                    "identified_npcs",
                    "initiated_conversations",
                    "explored_dialogue"
                ]
            },
            "inventory_management_discovery": {
                "name": "Inventory Management Discovery",
                "description": "Test AI ability to discover inventory and item management",
                "objectives": [
                    "Discover inventory system",
                    "Understand item types and properties",
                    "Learn item usage mechanics",
                    "Discover item combination or crafting"
                ],
                "hints_allowed": False,
                "max_actions": 180,
                "success_criteria": [
                    "accessed_inventory",
                    "used_items",
                    "managed_equipment"
                ]
            },
            "combat_system_discovery": {
                "name": "Combat System Discovery",
                "description": "Test AI ability to discover combat mechanics",
                "objectives": [
                    "Encounter combat situation",
                    "Discover available combat actions",
                    "Use different attack types",
                    "Understand defensive options",
                    "Learn resource management in combat"
                ],
                "hints_allowed": False,
                "max_actions": 300,
                "success_criteria": [
                    "entered_combat",
                    "used_combat_actions",
                    "managed_resources"
                ]
            }
        }
        
        return scenarios
    
    def run_discovery_test(self, scenario_name: str) -> Dict:
        """Run a specific discovery test scenario"""
        
        if scenario_name not in self.discovery_scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
            
        scenario = self.discovery_scenarios[scenario_name]
        game_logger.info(f"Running discovery test: {scenario['name']}")
        
        with create_isolated_test_environment(f"discovery_{scenario_name}") as test_env:
            try:
                # Create specialized AI player configuration for discovery
                discovery_config = self._create_discovery_config(scenario)
                
                # Run discovery test with specialized configuration
                result = self._execute_discovery_test(discovery_config, test_env)
                
                # Analyze discovery success
                analysis = self._analyze_discovery_success(result, scenario)
                
                return {
                    "scenario": scenario_name,
                    "test_result": result,
                    "discovery_analysis": analysis,
                    "success": analysis.get("criteria_met", 0) >= len(scenario["success_criteria"]) * 0.7
                }
                
            except Exception as e:
                game_logger.error(f"Discovery test failed: {str(e)}")
                return {
                    "scenario": scenario_name,
                    "status": "failed",
                    "error": str(e)
                }
    
    def _create_discovery_config(self, scenario: Dict) -> Dict:
        """Create AI configuration optimized for discovery testing"""
        
        return {
            "test_profile": "custom_discovery",
            "description": scenario["description"],
            "expected_duration_minutes": scenario["max_actions"] // 10,  # Rough estimate
            "personality": "intuitive_explorer",
            "objectives": scenario["objectives"],
            "focus_areas": ["organic_discovery", "feature_exploration"],
            "discovery_mode": True,
            "instruction_following": False,
            "hints_allowed": scenario.get("hints_allowed", False),
            "max_actions": scenario["max_actions"]
        }
    
    def _execute_discovery_test(self, config: Dict, test_env) -> Dict:
        """Execute the discovery test with custom configuration"""
        
        # Create temporary test objectives file with our custom config
        temp_objectives = {
            "test_profiles": {
                "custom_discovery": config
            },
            "ai_personalities": {
                "intuitive_explorer": {
                    "behavior": "Explores organically, tries different approaches, learns from trial and error",
                    "risk_tolerance": "medium",
                    "interaction_style": "experimental",
                    "decision_pattern": "organic_discovery"
                }
            }
        }
        
        # Save temporary objectives file in test environment
        objectives_path = test_env.isolated_dir / "test_objectives.json"
        safe_json_dump(temp_objectives, str(objectives_path))
        
        # Import and run test in the isolated environment
        from run_automated_test import AutomatedGameRunner
        
        runner = AutomatedGameRunner(
            test_profile_name="custom_discovery",
            max_actions=config["max_actions"]
        )
        
        results_file = runner.run_test()
        results = safe_json_load(results_file) if results_file else {}
        
        return results
    
    def _analyze_discovery_success(self, test_result: Dict, scenario: Dict) -> Dict:
        """Analyze how successfully the AI discovered the target features"""
        
        analysis = {
            "criteria_met": 0,
            "total_criteria": len(scenario["success_criteria"]),
            "discovery_details": {},
            "timeline": [],
            "efficiency_score": 0.0
        }
        
        conversation = test_result.get("conversation_log", [])
        success_criteria = scenario["success_criteria"]
        
        # Analyze conversation for discovery patterns
        for criterion in success_criteria:
            discovered = self._check_discovery_criterion(criterion, conversation)
            if discovered:
                analysis["criteria_met"] += 1
                analysis["discovery_details"][criterion] = discovered
        
        # Calculate efficiency score
        total_actions = test_result.get("total_actions", 1)
        if total_actions > 0:
            analysis["efficiency_score"] = analysis["criteria_met"] / total_actions
        
        # Create discovery timeline
        analysis["timeline"] = self._create_discovery_timeline(conversation, success_criteria)
        
        return analysis
    
    def _check_discovery_criterion(self, criterion: str, conversation: List[Dict]) -> Optional[Dict]:
        """Check if a specific discovery criterion was met"""
        
        # Define patterns for different discovery criteria
        patterns = {
            "created_storage_container": [
                "storage", "chest", "container", "store", "put", "place"
            ],
            "stored_items": [
                "stored", "put in", "placed in", "added to"
            ],
            "retrieved_items": [
                "retrieved", "got from", "took from", "removed from"
            ],
            "discovered_exits": [
                "exit", "door", "path", "way", "direction", "go"
            ],
            "successful_transitions": [
                "moved to", "went to", "traveled to", "arrived at"
            ],
            "returned_to_origin": [
                "returned", "went back", "back to"
            ],
            "identified_npcs": [
                "npc", "character", "person", "talk to", "speak with"
            ],
            "initiated_conversations": [
                "talked", "spoke", "conversation", "dialogue"
            ],
            "explored_dialogue": [
                "asked", "said", "response", "replied"
            ],
            "accessed_inventory": [
                "inventory", "items", "equipment", "gear"
            ],
            "used_items": [
                "used", "consumed", "equipped", "activated"
            ],
            "managed_equipment": [
                "equipped", "unequipped", "changed", "swapped"
            ],
            "entered_combat": [
                "combat", "fight", "battle", "attack", "encounter"
            ],
            "used_combat_actions": [
                "attacked", "defended", "cast", "action", "turn"
            ],
            "managed_resources": [
                "health", "mana", "spell slot", "stamina", "resource"
            ]
        }
        
        if criterion not in patterns:
            return None
            
        criterion_patterns = patterns[criterion]
        
        for i, entry in enumerate(conversation):
            content = entry.get("content", "").lower()
            
            # Check if any pattern matches
            if any(pattern in content for pattern in criterion_patterns):
                return {
                    "discovered": True,
                    "step": i,
                    "content": content[:200],  # First 200 chars
                    "timestamp": entry.get("timestamp", f"step_{i}")
                }
        
        return None
    
    def _create_discovery_timeline(self, conversation: List[Dict], criteria: List[str]) -> List[Dict]:
        """Create timeline of discoveries"""
        
        timeline = []
        
        for criterion in criteria:
            discovery = self._check_discovery_criterion(criterion, conversation)
            if discovery:
                timeline.append({
                    "criterion": criterion,
                    "step": discovery["step"],
                    "timestamp": discovery["timestamp"]
                })
        
        # Sort by step
        timeline.sort(key=lambda x: x["step"])
        
        return timeline
    
    def run_all_discovery_tests(self) -> Dict:
        """Run all discovery test scenarios"""
        
        results = {
            "test_suite": "feature_discovery",
            "scenarios_tested": len(self.discovery_scenarios),
            "individual_results": {},
            "summary": {
                "total_scenarios": len(self.discovery_scenarios),
                "successful_discoveries": 0,
                "partially_successful": 0,
                "failed_discoveries": 0
            }
        }
        
        for scenario_name in self.discovery_scenarios:
            game_logger.info(f"Running discovery scenario: {scenario_name}")
            
            scenario_result = self.run_discovery_test(scenario_name)
            results["individual_results"][scenario_name] = scenario_result
            
            # Update summary
            if scenario_result.get("success", False):
                results["summary"]["successful_discoveries"] += 1
            elif scenario_result.get("discovery_analysis", {}).get("criteria_met", 0) > 0:
                results["summary"]["partially_successful"] += 1
            else:
                results["summary"]["failed_discoveries"] += 1
        
        # Save comprehensive results
        results_file = f"feature_discovery_results_{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        safe_json_dump(results, results_file)
        
        game_logger.info(f"Feature discovery tests completed. Results: {results_file}")
        return results

def main():
    """Run feature discovery tests"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Feature Discovery Testing for DungeonMasterAI")
    parser.add_argument(
        "--scenario",
        choices=["storage_chest_discovery", "location_transition_discovery", 
                "npc_interaction_discovery", "inventory_management_discovery", 
                "combat_system_discovery"],
        help="Run specific discovery scenario"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all discovery scenarios"
    )
    
    args = parser.parse_args()
    
    tester = FeatureDiscoveryTester()
    
    try:
        if args.all:
            results = tester.run_all_discovery_tests()
            
            print(f"\nFeature Discovery Test Results:")
            summary = results["summary"]
            print(f"  Total Scenarios: {summary['total_scenarios']}")
            print(f"  Successful: {summary['successful_discoveries']}")
            print(f"  Partial Success: {summary['partially_successful']}")
            print(f"  Failed: {summary['failed_discoveries']}")
            
        elif args.scenario:
            result = tester.run_discovery_test(args.scenario)
            
            print(f"\nDiscovery Test: {result['scenario']}")
            print(f"  Success: {result.get('success', False)}")
            
            if "discovery_analysis" in result:
                analysis = result["discovery_analysis"]
                print(f"  Criteria Met: {analysis['criteria_met']}/{analysis['total_criteria']}")
                print(f"  Efficiency Score: {analysis['efficiency_score']:.3f}")
                print(f"  Discoveries: {len(analysis['discovery_details'])}")
        else:
            print("Please specify --scenario <name> or --all")
            print("\nAvailable scenarios:")
            for name, scenario in tester.discovery_scenarios.items():
                print(f"  {name}: {scenario['description']}")
            
    except Exception as e:
        print(f"Error running discovery tests: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())