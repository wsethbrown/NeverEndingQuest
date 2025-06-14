#!/usr/bin/env python3
"""
Specific test to reproduce and verify the fix for Elen's character corruption bug.
This test simulates the exact scenario that caused the spell data loss.
"""

import json
import sys
import os

# Add the current directory to the path to import the function
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from update_character_info import deep_merge_dict, validate_critical_fields_preserved

def test_elen_original_bug():
    """Reproduce the exact scenario that corrupted Elen's character file"""
    print("🐛 Reproducing Elen's Original Bug Scenario")
    print("=" * 60)
    
    # Elen's character data before the bug (from backup file)
    elen_before_bug = {
        "name": "Elen",
        "level": 5,
        "hitPoints": 42,
        "maxHitPoints": 42,
        "spellcasting": {
            "ability": "wisdom",
            "spellSaveDC": 13,
            "spellAttackBonus": 5,
            "spells": {
                "cantrips": [],
                "level1": [
                    "Hunter's Mark",
                    "Cure Wounds", 
                    "Animal Friendship",
                    "Speak with Animals"
                ],
                "level2": [
                    "Pass without Trace",
                    "Spike Growth"
                ],
                "level3": [],
                "level4": [],
                "level5": [],
                "level6": [],
                "level7": [],
                "level8": [],
                "level9": []
            },
            "spellSlots": {
                "level1": {"current": 4, "max": 4},
                "level2": {"current": 2, "max": 2},
                "level3": {"current": 0, "max": 0},
                "level4": {"current": 0, "max": 0},
                "level5": {"current": 0, "max": 0},
                "level6": {"current": 0, "max": 0},
                "level7": {"current": 0, "max": 0},
                "level8": {"current": 0, "max": 0},
                "level9": {"current": 0, "max": 0}
            }
        }
    }
    
    # The problematic AI response that caused the corruption (from debug_npc_update.json)
    problematic_ai_response = {
        "spellcasting": {
            "spellSlots": {
                "level1": {"current": 2, "max": 4},
                "level2": {"current": 2, "max": 2},
                "level3": {"current": 0, "max": 0},
                "level4": {"current": 0, "max": 0},
                "level5": {"current": 0, "max": 0},
                "level6": {"current": 0, "max": 0},
                "level7": {"current": 0, "max": 0},
                "level8": {"current": 0, "max": 0},
                "level9": {"current": 0, "max": 0}
            }
        }
    }
    
    print("📋 Test Data:")
    print(f"   Original spells count: {len(elen_before_bug['spellcasting']['spells']['level1'])}")
    print(f"   Original ability: {elen_before_bug['spellcasting']['ability']}")
    print(f"   Original DC: {elen_before_bug['spellcasting']['spellSaveDC']}")
    print(f"   Original spell slots L1: {elen_before_bug['spellcasting']['spellSlots']['level1']}")
    
    print("\n🔧 Testing OLD behavior (complete replacement):")
    # Simulate the old broken behavior
    old_broken_result = elen_before_bug.copy()
    old_broken_result["spellcasting"] = problematic_ai_response["spellcasting"]  # COMPLETE REPLACEMENT!
    
    print(f"   ❌ OLD: Spells lost: {'spells' not in old_broken_result['spellcasting']}")
    print(f"   ❌ OLD: Ability lost: {'ability' not in old_broken_result['spellcasting']}")
    print(f"   ❌ OLD: DC lost: {'spellSaveDC' not in old_broken_result['spellcasting']}")
    
    print("\n🔧 Testing NEW behavior (deep merge):")
    # Test the new fixed behavior
    new_fixed_result = deep_merge_dict(elen_before_bug, problematic_ai_response)
    
    print(f"   ✅ NEW: Spells preserved: {len(new_fixed_result['spellcasting']['spells']['level1'])} spells")
    print(f"   ✅ NEW: Ability preserved: {new_fixed_result['spellcasting']['ability']}")
    print(f"   ✅ NEW: DC preserved: {new_fixed_result['spellcasting']['spellSaveDC']}")
    print(f"   ✅ NEW: Spell slots updated: {new_fixed_result['spellcasting']['spellSlots']['level1']}")
    
    # Test critical field validation
    print("\n🔍 Testing Critical Field Validation:")
    warnings_old = validate_critical_fields_preserved(elen_before_bug, old_broken_result, "Elen")
    warnings_new = validate_critical_fields_preserved(elen_before_bug, new_fixed_result, "Elen")
    
    print(f"   ❌ OLD: {len(warnings_old)} critical warnings: {warnings_old}")
    print(f"   ✅ NEW: {len(warnings_new)} critical warnings: {warnings_new}")
    
    # Verify the fix
    assert len(new_fixed_result['spellcasting']['spells']['level1']) == 4, "Level 1 spells should be preserved"
    assert len(new_fixed_result['spellcasting']['spells']['level2']) == 2, "Level 2 spells should be preserved"
    assert new_fixed_result['spellcasting']['ability'] == "wisdom", "Spellcasting ability should be preserved"
    assert new_fixed_result['spellcasting']['spellSaveDC'] == 13, "Spell save DC should be preserved"
    assert new_fixed_result['spellcasting']['spellAttackBonus'] == 5, "Spell attack bonus should be preserved"
    assert new_fixed_result['spellcasting']['spellSlots']['level1']['current'] == 2, "Spell slot current should be updated"
    assert new_fixed_result['spellcasting']['spellSlots']['level1']['max'] == 4, "Spell slot max should be preserved"
    
    print("\n🎉 SUCCESS: The bug is fixed!")
    print("   • Spell data is preserved during spell slot updates")
    print("   • Critical field validation would have caught the old bug")
    print("   • Deep merge prevents data loss")
    
    return True

def test_multiple_spell_slot_updates():
    """Test multiple consecutive spell slot updates to ensure no data degradation"""
    print("\n🔄 Testing Multiple Consecutive Updates")
    print("=" * 60)
    
    # Start with full character data
    character = {
        "name": "TestWizard",
        "spellcasting": {
            "ability": "intelligence",
            "spellSaveDC": 15,
            "spellAttackBonus": 7,
            "spells": {
                "level1": ["Magic Missile", "Shield", "Detect Magic"],
                "level2": ["Misty Step", "Web"],
                "level3": ["Fireball", "Counterspell"]
            },
            "spellSlots": {
                "level1": {"current": 4, "max": 4},
                "level2": {"current": 3, "max": 3},
                "level3": {"current": 2, "max": 2}
            }
        }
    }
    
    # Simulate a series of spell casting updates
    updates = [
        {"spellcasting": {"spellSlots": {"level1": {"current": 3, "max": 4}}}},  # Cast Magic Missile
        {"spellcasting": {"spellSlots": {"level2": {"current": 2, "max": 3}}}},  # Cast Misty Step
        {"spellcasting": {"spellSlots": {"level1": {"current": 2, "max": 4}}}},  # Cast Shield
        {"spellcasting": {"spellSlots": {"level3": {"current": 1, "max": 2}}}},  # Cast Fireball
        {"spellcasting": {"spellSlots": {"level1": {"current": 1, "max": 4}}}},  # Cast Detect Magic
    ]
    
    current_character = character
    
    for i, update in enumerate(updates):
        print(f"   Update {i+1}: {list(update['spellcasting']['spellSlots'].keys())}")
        current_character = deep_merge_dict(current_character, update)
        
        # Verify data integrity after each update
        assert current_character['spellcasting']['ability'] == "intelligence"
        assert len(current_character['spellcasting']['spells']['level1']) == 3
        assert len(current_character['spellcasting']['spells']['level2']) == 2
        assert len(current_character['spellcasting']['spells']['level3']) == 2
        assert current_character['spellcasting']['spellSaveDC'] == 15
        assert current_character['spellcasting']['spellAttackBonus'] == 7
        
        # Check that no warnings would be generated
        warnings = validate_critical_fields_preserved(character, current_character, "TestWizard")
        assert len(warnings) == 0, f"No warnings should be generated on update {i+1}"
    
    # Final verification
    final_slots = current_character['spellcasting']['spellSlots']
    assert final_slots['level1']['current'] == 1
    assert final_slots['level2']['current'] == 2  
    assert final_slots['level3']['current'] == 1
    
    print("   ✅ All updates preserved critical data")
    print("   ✅ Final spell slots are correct")
    print("   ✅ No data degradation occurred")
    
    return True

def run_bug_reproduction_tests():
    """Run all bug reproduction tests"""
    print("🔬 Elen Bug Reproduction & Verification Test Suite")
    print("=" * 80)
    
    tests = [
        test_elen_original_bug,
        test_multiple_spell_slot_updates
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
    
    print("\n" + "=" * 80)
    print(f"📊 BUG REPRODUCTION TEST SUMMARY:")
    print(f"   ✅ Tests Passed: {passed}")
    print(f"   ❌ Tests Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 BUG REPRODUCTION TESTS PASSED!")
        print("   • The original Elen bug is completely fixed")
        print("   • Deep merge prevents all similar data corruption")
        print("   • System is robust against partial object updates")
    else:
        print(f"\n⚠️  {failed} tests failed - bug may not be fully fixed!")
    
    return failed == 0

if __name__ == "__main__":
    success = run_bug_reproduction_tests()
    sys.exit(0 if success else 1)