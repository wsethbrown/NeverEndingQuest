#!/usr/bin/env python3
"""
Stress tests for deep_merge_dict to test performance and edge cases with larger datasets.
"""

import json
import time
import sys
import os

# Add the current directory to the path to import the function
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from update_character_info import deep_merge_dict

def test_large_nested_structure():
    """Test with a very large nested structure"""
    print("🔥 Testing large nested structure...")
    
    # Create a large base structure
    base = {
        "character": {
            f"section_{i}": {
                f"subsection_{j}": {
                    "data": [f"item_{k}" for k in range(10)],
                    "config": {f"setting_{k}": f"value_{k}" for k in range(5)}
                }
                for j in range(5)
            }
            for i in range(10)
        }
    }
    
    # Create an update that modifies deeply nested values
    update = {
        "character": {
            "section_0": {
                "subsection_0": {
                    "config": {"setting_0": "new_value_0"}
                }
            },
            "section_5": {
                "subsection_3": {
                    "data": ["new_item_1", "new_item_2"]
                }
            }
        }
    }
    
    start_time = time.time()
    result = deep_merge_dict(base, update)
    end_time = time.time()
    
    # Verify specific changes were applied
    assert result["character"]["section_0"]["subsection_0"]["config"]["setting_0"] == "new_value_0"
    assert result["character"]["section_5"]["subsection_3"]["data"] == ["new_item_1", "new_item_2"]
    
    # Verify other data was preserved
    assert result["character"]["section_0"]["subsection_0"]["config"]["setting_1"] == "value_1"
    assert len(result["character"]["section_1"]["subsection_0"]["data"]) == 10
    
    print(f"✅ Large structure test passed in {end_time - start_time:.4f} seconds")
    return True

def test_deeply_nested_structure():
    """Test with extremely deep nesting (50 levels)"""
    print("🔥 Testing deeply nested structure...")
    
    # Create a structure with 50 levels of nesting
    base = {}
    current = base
    for i in range(50):
        current[f"level_{i}"] = {}
        current = current[f"level_{i}"]
    current["final_value"] = "original"
    current["preserve_me"] = "keep_this"
    
    # Create an update for the deepest level
    update = {}
    current = update
    for i in range(50):
        current[f"level_{i}"] = {}
        current = current[f"level_{i}"]
    current["final_value"] = "updated"
    
    start_time = time.time()
    result = deep_merge_dict(base, update)
    end_time = time.time()
    
    # Navigate to the deepest level to verify
    current = result
    for i in range(50):
        current = current[f"level_{i}"]
    
    assert current["final_value"] == "updated"
    assert current["preserve_me"] == "keep_this"
    
    print(f"✅ Deep nesting test passed in {end_time - start_time:.4f} seconds")
    return True

def test_realistic_character_scenarios():
    """Test scenarios that mirror real character update patterns"""
    print("🔥 Testing realistic character scenarios...")
    
    # Simulate a full character sheet
    full_character = {
        "name": "TestCharacter",
        "level": 10,
        "hitPoints": 75,
        "maxHitPoints": 75,
        "abilities": {"strength": 16, "dexterity": 14, "constitution": 15, "intelligence": 12, "wisdom": 13, "charisma": 10},
        "skills": {f"skill_{i}": i + 10 for i in range(20)},
        "equipment": [{"item_name": f"item_{i}", "quantity": 1} for i in range(50)],
        "spellcasting": {
            "ability": "wisdom",
            "spellSaveDC": 15,
            "spellAttackBonus": 7,
            "spells": {
                f"level{i}": [f"spell_{i}_{j}" for j in range(5)] for i in range(1, 10)
            },
            "spellSlots": {
                f"level{i}": {"current": i, "max": i + 2} for i in range(1, 10)
            }
        }
    }
    
    # Test 1: HP damage
    hp_update = {"hitPoints": 60}
    result1 = deep_merge_dict(full_character, hp_update)
    assert result1["hitPoints"] == 60
    assert result1["spellcasting"]["ability"] == "wisdom"
    assert len(result1["equipment"]) == 50
    
    # Test 2: Spell slot usage
    spell_update = {
        "spellcasting": {
            "spellSlots": {
                "level1": {"current": 0, "max": 3},
                "level3": {"current": 2, "max": 5}
            }
        }
    }
    result2 = deep_merge_dict(full_character, spell_update)
    assert result2["spellcasting"]["spellSlots"]["level1"]["current"] == 0
    assert result2["spellcasting"]["spellSlots"]["level3"]["current"] == 2
    assert result2["spellcasting"]["ability"] == "wisdom"
    assert len(result2["spellcasting"]["spells"]["level1"]) == 5
    
    # Test 3: Equipment addition
    equipment_update = {
        "equipment": [{"item_name": "new_sword", "quantity": 1}]
    }
    result3 = deep_merge_dict(full_character, equipment_update)
    assert result3["equipment"] == [{"item_name": "new_sword", "quantity": 1}]
    assert result3["spellcasting"]["ability"] == "wisdom"
    
    print("✅ Realistic character scenarios passed")
    return True

def test_concurrent_updates():
    """Test multiple rapid updates in sequence"""
    print("🔥 Testing concurrent updates...")
    
    base_character = {
        "name": "ConcurrentTest",
        "stats": {"hp": 100, "mp": 50},
        "spellcasting": {
            "ability": "intelligence",
            "spells": {"level1": ["spell1", "spell2"]},
            "spellSlots": {"level1": {"current": 4, "max": 4}}
        }
    }
    
    # Simulate 100 rapid updates
    current_character = base_character
    for i in range(100):
        update = {
            "stats": {"hp": 100 - i},
            "spellcasting": {
                "spellSlots": {
                    "level1": {"current": max(0, 4 - (i % 5)), "max": 4}
                }
            }
        }
        current_character = deep_merge_dict(current_character, update)
        
        # Verify integrity after each update
        assert current_character["spellcasting"]["ability"] == "intelligence"
        assert len(current_character["spellcasting"]["spells"]["level1"]) == 2
        assert current_character["stats"]["hp"] == 100 - i
    
    print("✅ Concurrent updates test passed")
    return True

def test_malformed_updates():
    """Test with potentially malformed or unusual update patterns"""
    print("🔥 Testing malformed updates...")
    
    base = {
        "spellcasting": {
            "ability": "wisdom",
            "spells": {"level1": ["spell1"]},
            "spellSlots": {"level1": {"current": 2, "max": 2}}
        }
    }
    
    # Test 1: Nested None values
    update1 = {"spellcasting": {"newField": None}}
    result1 = deep_merge_dict(base, update1)
    assert result1["spellcasting"]["ability"] == "wisdom"
    assert result1["spellcasting"]["newField"] is None
    
    # Test 2: Mixed types
    update2 = {"spellcasting": {"mixedField": [1, "string", {"nested": True}]}}
    result2 = deep_merge_dict(base, update2)
    assert result2["spellcasting"]["ability"] == "wisdom"
    assert result2["spellcasting"]["mixedField"] == [1, "string", {"nested": True}]
    
    # Test 3: Very long strings
    long_string = "x" * 10000
    update3 = {"spellcasting": {"longString": long_string}}
    result3 = deep_merge_dict(base, update3)
    assert result3["spellcasting"]["ability"] == "wisdom"
    assert len(result3["spellcasting"]["longString"]) == 10000
    
    print("✅ Malformed updates test passed")
    return True

def run_stress_tests():
    """Run all stress tests"""
    print("🚀 Starting Deep Merge Stress Test Suite")
    print("=" * 60)
    
    total_start = time.time()
    
    tests = [
        test_large_nested_structure,
        test_deeply_nested_structure,
        test_realistic_character_scenarios,
        test_concurrent_updates,
        test_malformed_updates
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ FAIL: {test.__name__} - {str(e)}")
            failed += 1
    
    total_end = time.time()
    
    print("\n" + "=" * 60)
    print(f"📊 STRESS TEST SUMMARY:")
    print(f"   ✅ Tests Passed: {passed}")
    print(f"   ❌ Tests Failed: {failed}")
    print(f"   ⏱️  Total Time: {total_end - total_start:.4f} seconds")
    print(f"   📈 Success Rate: {(passed / (passed + failed)) * 100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL STRESS TESTS PASSED! Deep merge is robust and performant.")
    else:
        print(f"\n⚠️  {failed} stress tests failed.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_stress_tests()
    sys.exit(0 if success else 1)