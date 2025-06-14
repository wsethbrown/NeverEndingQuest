#!/usr/bin/env python3
"""
Comprehensive test suite for the deep_merge_dict functionality.
Tests various scenarios to ensure the function correctly merges nested dictionaries
while preserving data integrity.
"""

import json
import copy
import sys
import os

# Add the current directory to the path to import the function
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from update_character_info import deep_merge_dict, validate_critical_fields_preserved

class TestDeepMerge:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []

    def assert_equal(self, actual, expected, test_name):
        """Helper function to assert equality and track results"""
        if actual == expected:
            self.tests_passed += 1
            self.test_results.append(f"✅ PASS: {test_name}")
            print(f"✅ PASS: {test_name}")
        else:
            self.tests_failed += 1
            self.test_results.append(f"❌ FAIL: {test_name}")
            print(f"❌ FAIL: {test_name}")
            print(f"   Expected: {expected}")
            print(f"   Actual:   {actual}")

    def test_basic_merges(self):
        """Test basic merge scenarios"""
        print("\n=== Testing Basic Merge Scenarios ===")
        
        # Test 1: Simple value replacement
        base = {"name": "John", "level": 1}
        update = {"level": 2}
        expected = {"name": "John", "level": 2}
        result = deep_merge_dict(base, update)
        self.assert_equal(result, expected, "Simple value replacement")

        # Test 2: Adding new fields
        base = {"name": "John"}
        update = {"level": 5, "class": "Wizard"}
        expected = {"name": "John", "level": 5, "class": "Wizard"}
        result = deep_merge_dict(base, update)
        self.assert_equal(result, expected, "Adding new fields")

        # Test 3: Array replacement (arrays are replaced, not merged)
        base = {"items": ["sword", "shield"]}
        update = {"items": ["bow", "arrows"]}
        expected = {"items": ["bow", "arrows"]}
        result = deep_merge_dict(base, update)
        self.assert_equal(result, expected, "Array replacement")

    def test_nested_object_merges(self):
        """Test nested object merge scenarios"""
        print("\n=== Testing Nested Object Merges ===")
        
        # Test 1: Basic nested merge
        base = {
            "character": {
                "name": "Alice",
                "stats": {"str": 10, "dex": 12}
            }
        }
        update = {
            "character": {
                "stats": {"str": 15}
            }
        }
        expected = {
            "character": {
                "name": "Alice",
                "stats": {"str": 15, "dex": 12}
            }
        }
        result = deep_merge_dict(base, update)
        self.assert_equal(result, expected, "Basic nested merge")

        # Test 2: Deep nested merge
        base = {
            "a": {
                "b": {
                    "c": {"x": 1, "y": 2},
                    "d": "keep_me"
                }
            }
        }
        update = {
            "a": {
                "b": {
                    "c": {"x": 99}
                }
            }
        }
        expected = {
            "a": {
                "b": {
                    "c": {"x": 99, "y": 2},
                    "d": "keep_me"
                }
            }
        }
        result = deep_merge_dict(base, update)
        self.assert_equal(result, expected, "Deep nested merge")

    def test_spellcasting_scenarios(self):
        """Test spell slot specific scenarios that caused the original bug"""
        print("\n=== Testing Spellcasting Scenarios ===")
        
        # Test 1: The original bug scenario - partial spellcasting update
        base = {
            "name": "Elen",
            "spellcasting": {
                "ability": "wisdom",
                "spellSaveDC": 13,
                "spellAttackBonus": 5,
                "spells": {
                    "level1": ["Hunter's Mark", "Cure Wounds"],
                    "level2": ["Pass without Trace"]
                },
                "spellSlots": {
                    "level1": {"current": 4, "max": 4},
                    "level2": {"current": 2, "max": 2}
                }
            }
        }
        
        # This was the problematic update that wiped spell data
        problematic_update = {
            "spellcasting": {
                "spellSlots": {
                    "level1": {"current": 2, "max": 4}
                }
            }
        }
        
        # With deep merge, this should preserve all other spellcasting data
        expected = {
            "name": "Elen",
            "spellcasting": {
                "ability": "wisdom",
                "spellSaveDC": 13,
                "spellAttackBonus": 5,
                "spells": {
                    "level1": ["Hunter's Mark", "Cure Wounds"],
                    "level2": ["Pass without Trace"]
                },
                "spellSlots": {
                    "level1": {"current": 2, "max": 4},
                    "level2": {"current": 2, "max": 2}
                }
            }
        }
        
        result = deep_merge_dict(base, problematic_update)
        self.assert_equal(result, expected, "Spell slot update preserves spell data")

        # Test 2: Multiple spell slot level updates
        update2 = {
            "spellcasting": {
                "spellSlots": {
                    "level1": {"current": 1, "max": 4},
                    "level2": {"current": 0, "max": 2}
                }
            }
        }
        
        expected2 = {
            "name": "Elen",
            "spellcasting": {
                "ability": "wisdom",
                "spellSaveDC": 13,
                "spellAttackBonus": 5,
                "spells": {
                    "level1": ["Hunter's Mark", "Cure Wounds"],
                    "level2": ["Pass without Trace"]
                },
                "spellSlots": {
                    "level1": {"current": 1, "max": 4},
                    "level2": {"current": 0, "max": 2}
                }
            }
        }
        
        result2 = deep_merge_dict(base, update2)
        self.assert_equal(result2, expected2, "Multiple spell slot updates")

    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        print("\n=== Testing Edge Cases ===")
        
        # Test 1: Empty dictionaries
        base = {"a": 1}
        update = {}
        expected = {"a": 1}
        result = deep_merge_dict(base, update)
        self.assert_equal(result, expected, "Empty update dictionary")

        # Test 2: Empty base
        base = {}
        update = {"a": 1}
        expected = {"a": 1}
        result = deep_merge_dict(base, update)
        self.assert_equal(result, expected, "Empty base dictionary")

        # Test 3: None values
        base = {"a": 1, "b": None}
        update = {"b": 2, "c": None}
        expected = {"a": 1, "b": 2, "c": None}
        result = deep_merge_dict(base, update)
        self.assert_equal(result, expected, "None values handling")

        # Test 4: Type mismatches (dict vs non-dict)
        base = {"config": {"setting1": "value1"}}
        update = {"config": "new_string_value"}
        expected = {"config": "new_string_value"}
        result = deep_merge_dict(base, update)
        self.assert_equal(result, expected, "Type mismatch - dict to string")

        # Test 5: Type mismatch (non-dict to dict)
        base = {"config": "string_value"}
        update = {"config": {"setting1": "value1"}}
        expected = {"config": {"setting1": "value1"}}
        result = deep_merge_dict(base, update)
        self.assert_equal(result, expected, "Type mismatch - string to dict")

    def test_complex_scenarios(self):
        """Test complex real-world scenarios"""
        print("\n=== Testing Complex Scenarios ===")
        
        # Test 1: Multiple nested updates
        base = {
            "character": {
                "basic": {"name": "Test", "level": 1},
                "combat": {"hp": 10, "ac": 15},
                "spellcasting": {
                    "ability": "wisdom",
                    "spells": {"level1": ["spell1"]},
                    "spellSlots": {"level1": {"current": 2, "max": 2}}
                }
            },
            "inventory": ["item1", "item2"]
        }
        
        update = {
            "character": {
                "basic": {"level": 2},
                "combat": {"hp": 12},
                "spellcasting": {
                    "spellSlots": {"level1": {"current": 1, "max": 2}}
                }
            },
            "inventory": ["item3", "item4"]
        }
        
        expected = {
            "character": {
                "basic": {"name": "Test", "level": 2},
                "combat": {"hp": 12, "ac": 15},
                "spellcasting": {
                    "ability": "wisdom",
                    "spells": {"level1": ["spell1"]},
                    "spellSlots": {"level1": {"current": 1, "max": 2}}
                }
            },
            "inventory": ["item3", "item4"]
        }
        
        result = deep_merge_dict(base, update)
        self.assert_equal(result, expected, "Complex multi-level update")

    def test_critical_field_validation(self):
        """Test the critical field preservation validation"""
        print("\n=== Testing Critical Field Validation ===")
        
        # Test 1: No critical fields lost
        original = {
            "spellcasting": {
                "ability": "wisdom",
                "spellSaveDC": 13,
                "spellAttackBonus": 5,
                "spells": {"level1": ["spell1"]}
            }
        }
        
        updated = {
            "spellcasting": {
                "ability": "wisdom",
                "spellSaveDC": 13,
                "spellAttackBonus": 5,
                "spells": {"level1": ["spell1"]},
                "spellSlots": {"level1": {"current": 1, "max": 2}}
            }
        }
        
        warnings = validate_critical_fields_preserved(original, updated, "TestChar")
        self.assert_equal(len(warnings), 0, "No warnings when fields preserved")

        # Test 2: Critical field lost
        original = {
            "spellcasting": {
                "ability": "wisdom",
                "spellSaveDC": 13,
                "spellAttackBonus": 5,
                "spells": {"level1": ["spell1"]}
            }
        }
        
        updated = {
            "spellcasting": {
                "spellSaveDC": 13,
                "spellAttackBonus": 5
                # Missing ability and spells!
            }
        }
        
        warnings = validate_critical_fields_preserved(original, updated, "TestChar")
        self.assert_equal(len(warnings), 2, "Warnings when critical fields lost")

    def test_real_character_data(self):
        """Test with real character data from Elen's file"""
        print("\n=== Testing Real Character Data ===")
        
        # Simulate Elen's original data
        elen_base = {
            "name": "Elen",
            "level": 5,
            "hitPoints": 42,
            "spellcasting": {
                "ability": "wisdom",
                "spellSaveDC": 13,
                "spellAttackBonus": 5,
                "spells": {
                    "cantrips": [],
                    "level1": ["Hunter's Mark", "Cure Wounds", "Animal Friendship", "Speak with Animals"],
                    "level2": ["Pass without Trace", "Spike Growth"]
                },
                "spellSlots": {
                    "level1": {"current": 4, "max": 4},
                    "level2": {"current": 2, "max": 2}
                }
            }
        }
        
        # Simulate the AI update that caused the original bug
        spell_slot_update = {
            "spellcasting": {
                "spellSlots": {
                    "level1": {"current": 2, "max": 4}
                }
            }
        }
        
        result = deep_merge_dict(elen_base, spell_slot_update)
        
        # Verify all critical data is preserved
        self.assert_equal(result["spellcasting"]["ability"], "wisdom", "Spellcasting ability preserved")
        self.assert_equal(result["spellcasting"]["spellSaveDC"], 13, "Spell save DC preserved")
        self.assert_equal(result["spellcasting"]["spellAttackBonus"], 5, "Spell attack bonus preserved")
        self.assert_equal(len(result["spellcasting"]["spells"]["level1"]), 4, "Level 1 spells preserved")
        self.assert_equal(len(result["spellcasting"]["spells"]["level2"]), 2, "Level 2 spells preserved")
        self.assert_equal(result["spellcasting"]["spellSlots"]["level1"]["current"], 2, "Spell slot current updated")
        self.assert_equal(result["spellcasting"]["spellSlots"]["level1"]["max"], 4, "Spell slot max preserved")

    def test_immutability(self):
        """Test that original objects are not modified"""
        print("\n=== Testing Immutability ===")
        
        base = {"a": {"b": 1}}
        update = {"a": {"c": 2}}
        original_base = copy.deepcopy(base)
        original_update = copy.deepcopy(update)
        
        result = deep_merge_dict(base, update)
        
        # Verify originals weren't modified
        self.assert_equal(base, original_base, "Base object not modified")
        self.assert_equal(update, original_update, "Update object not modified")
        
        # Verify result is correct
        expected = {"a": {"b": 1, "c": 2}}
        self.assert_equal(result, expected, "Result is correct")

    def run_all_tests(self):
        """Run all test suites"""
        print("🧪 Starting Deep Merge Comprehensive Test Suite")
        print("=" * 60)
        
        self.test_basic_merges()
        self.test_nested_object_merges()
        self.test_spellcasting_scenarios()
        self.test_edge_cases()
        self.test_complex_scenarios()
        self.test_critical_field_validation()
        self.test_real_character_data()
        self.test_immutability()
        
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY:")
        print(f"   ✅ Tests Passed: {self.tests_passed}")
        print(f"   ❌ Tests Failed: {self.tests_failed}")
        print(f"   📈 Success Rate: {(self.tests_passed / (self.tests_passed + self.tests_failed)) * 100:.1f}%")
        
        if self.tests_failed == 0:
            print("\n🎉 ALL TESTS PASSED! Deep merge functionality is working correctly.")
        else:
            print(f"\n⚠️  {self.tests_failed} tests failed. Review the failures above.")
        
        return self.tests_failed == 0

if __name__ == "__main__":
    tester = TestDeepMerge()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)