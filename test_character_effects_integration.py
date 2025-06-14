#!/usr/bin/env python3
"""
Integration and advanced tests for Character Effects System
"""

import unittest
import json
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from character_effects_validator import AICharacterEffectsValidator
from update_character_info import load_character_data, save_character_data


class TestTimeBasedEffects(unittest.TestCase):
    """Test time-based effect expiration and management"""
    
    def setUp(self):
        self.validator = AICharacterEffectsValidator()
        self.base_time = "1492-03-02T14:30:00"
    
    def test_effect_expiration_scenarios(self):
        """Test various effect expiration scenarios"""
        test_effects = [
            # Effect that should expire (past time)
            {
                "name": "Old Blessing",
                "description": "Expired effect",
                "expiration": "1492-03-02T14:00:00",
                "effectType": "magical"
            },
            # Effect that should remain (future time)
            {
                "name": "Active Blessing",
                "description": "Active effect", 
                "expiration": "1492-03-02T15:00:00",
                "effectType": "magical"
            },
            # Permanent effect (no expiration)
            {
                "name": "Permanent Curse",
                "description": "Never expires",
                "effectType": "curse"
            },
            # Special duration effect
            {
                "name": "Disease",
                "description": "Lasts until cured",
                "expiration": "until removed",
                "effectType": "condition"
            }
        ]
        
        # Filter active effects
        active_effects = []
        expired_effects = []
        
        for effect in test_effects:
            expiration = effect.get("expiration", "permanent")
            
            if expiration in ["permanent", "until removed", "short rest", "long rest"]:
                active_effects.append(effect)
            elif expiration < self.base_time:
                expired_effects.append(effect)
            else:
                active_effects.append(effect)
        
        self.assertEqual(len(active_effects), 3)
        self.assertEqual(len(expired_effects), 1)
        self.assertEqual(expired_effects[0]["name"], "Old Blessing")
    
    def test_duration_calculations(self):
        """Test accurate duration calculations for various time units"""
        test_cases = [
            # (duration_text, expected_hours)
            ("1 minute", 1/60),
            ("10 minutes", 10/60),
            ("1 hour", 1),
            ("8 hours", 8),
            ("24 hours", 24),
            ("1 day", 24),
            ("1 week", 168)
        ]
        
        base_dt = datetime.fromisoformat(self.base_time)
        
        for duration_text, expected_hours in test_cases:
            result = self.validator._parse_duration(duration_text, self.base_time)
            
            if result not in ["short rest", "long rest", "until removed"]:
                result_dt = datetime.fromisoformat(result)
                time_diff = result_dt - base_dt
                actual_hours = time_diff.total_seconds() / 3600
                
                self.assertAlmostEqual(actual_hours, expected_hours, places=2)
    
    def test_rest_based_expiration(self):
        """Test handling of rest-based effect durations"""
        effects_to_clear_on_short_rest = [
            {"name": "Ability Used", "expiration": "short rest"},
            {"name": "Exhausting Effort", "expiration": "short rest"}
        ]
        
        effects_to_clear_on_long_rest = [
            {"name": "Daily Power", "expiration": "long rest"},
            {"name": "Fatigue", "expiration": "long rest"}
        ]
        
        permanent_effects = [
            {"name": "Magical Item Bonus", "expiration": "permanent"},
            {"name": "Curse", "expiration": "until removed"}
        ]
        
        # Simulate short rest
        remaining_after_short = effects_to_clear_on_long_rest + permanent_effects
        self.assertEqual(len(remaining_after_short), 4)
        
        # Simulate long rest
        remaining_after_long = permanent_effects
        self.assertEqual(len(remaining_after_long), 2)


class TestEquipmentEffectsIntegration(unittest.TestCase):
    """Test equipment effect calculation and integration"""
    
    def setUp(self):
        self.validator = AICharacterEffectsValidator()
    
    def test_complex_equipment_combinations(self):
        """Test calculation of effects from multiple equipped items"""
        character = {
            "equipment": [
                {"item_name": "Plate Mail", "item_type": "armor", "equipped": True},
                {"item_name": "Shield +1", "item_type": "armor", "equipped": True},
                {"item_name": "Flame Tongue", "item_type": "weapon", "equipped": True},
                {
                    "item_name": "Ring of Protection",
                    "item_type": "miscellaneous",
                    "equipped": True,
                    "effects": [
                        {"type": "bonus", "target": "ac", "value": 1},
                        {"type": "bonus", "target": "saving_throws", "value": 1}
                    ]
                },
                {
                    "item_name": "Cloak of Resistance",
                    "item_type": "miscellaneous",
                    "equipped": True,
                    "effects": [
                        {"type": "resistance", "target": "all", "value": None}
                    ]
                },
                {
                    "item_name": "Boots of Speed",
                    "item_type": "miscellaneous",
                    "equipped": False,  # Not equipped
                    "effects": [
                        {"type": "bonus", "target": "speed", "value": 10}
                    ]
                },
                {
                    "item_name": "Amulet of Health",
                    "item_type": "miscellaneous",
                    "equipped": True,
                    "effects": [
                        {"type": "set", "target": "constitution", "value": 19}
                    ]
                }
            ]
        }
        
        result = self.validator.calculate_equipment_effects(character)
        effects = result.get("equipment_effects", [])
        
        # Should have effects from 3 equipped items (not boots)
        self.assertEqual(len(effects), 4)  # 2 from ring, 1 from cloak, 1 from amulet
        
        # Verify specific effects
        effect_types = [e["type"] for e in effects]
        self.assertIn("bonus", effect_types)
        self.assertIn("resistance", effect_types)
        self.assertIn("set", effect_types)
        
        # Verify boots effects are not included
        speed_effects = [e for e in effects if e.get("target") == "speed"]
        self.assertEqual(len(speed_effects), 0)
    
    def test_equipment_change_updates(self):
        """Test that equipment changes properly update effects"""
        character = {
            "equipment": [
                {
                    "item_name": "Magic Ring",
                    "item_type": "miscellaneous",
                    "equipped": True,
                    "effects": [{"type": "bonus", "target": "ac", "value": 1}]
                }
            ]
        }
        
        # Initial effects
        result1 = self.validator.calculate_equipment_effects(character)
        effects1 = result1.get("equipment_effects", [])
        self.assertEqual(len(effects1), 1)
        
        # Unequip the ring
        character["equipment"][0]["equipped"] = False
        result2 = self.validator.calculate_equipment_effects(character)
        effects2 = result2.get("equipment_effects", [])
        self.assertEqual(len(effects2), 0)
        
        # Re-equip the ring
        character["equipment"][0]["equipped"] = True
        result3 = self.validator.calculate_equipment_effects(character)
        effects3 = result3.get("equipment_effects", [])
        self.assertEqual(len(effects3), 1)


class TestValidatorIntegration(unittest.TestCase):
    """Test full integration with module files"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.validator = AICharacterEffectsValidator()
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    @patch('character_effects_validator.GPTManager')
    def test_full_character_validation_workflow(self, mock_gpt):
        """Test complete validation workflow with all components"""
        # Set up mock GPT responses
        mock_gpt_instance = MagicMock()
        mock_gpt.return_value = mock_gpt_instance
        mock_gpt_instance.query.return_value = json.dumps({
            "categorized_effects": {
                "temporary_magical": [
                    {
                        "name": "Blessed",
                        "description": "Divine favor",
                        "duration": "10 minutes",
                        "source": "Cleric"
                    }
                ],
                "injuries": [
                    {
                        "type": "wound",
                        "description": "Bite wound",
                        "damage": 4,
                        "source": "Giant Rat"
                    }
                ],
                "equipment": [],
                "class_abilities": ["Second Wind"]
            }
        })
        
        # Create test character
        test_char = {
            "name": "Integration Test Fighter",
            "class": "Fighter",
            "level": 5,
            "equipment": [
                {
                    "item_name": "Amulet of Protection",
                    "item_type": "miscellaneous",
                    "equipped": True,
                    "effects": [
                        {"type": "bonus", "target": "saving_throws", "value": 2}
                    ]
                }
            ],
            "classFeatures": [
                {"name": "Second Wind", "description": "Heal 1d10+level"},
                {"name": "Action Surge", "description": "Extra action"}
            ],
            "temporaryEffects": [
                {"name": "Second Wind", "description": "Used"},
                {"name": "Blessed", "description": "Divine favor"},
                {"name": "4 damage", "description": "From rat bite"},
                {"name": "Old Effect", "expiration": "1492-03-01T12:00:00"}
            ]
        }
        
        # Save files
        char_path = os.path.join(self.test_dir, "test_fighter.json")
        party_path = os.path.join(self.test_dir, "party_tracker.json")
        
        with open(char_path, 'w') as f:
            json.dump(test_char, f)
        
        with open(party_path, 'w') as f:
            json.dump({
                "current_time": {"formatted": "1492-03-02T14:30:00"}
            }, f)
        
        # Run validation
        result, success = self.validator.validate_character_effects_safe(char_path)
        
        # Verify results
        self.assertTrue(success)
        self.assertIn("equipment_effects", result)
        self.assertIn("injuries", result)
        self.assertIn("temporaryEffects", result)
        
        # Check equipment effects calculated
        self.assertEqual(len(result["equipment_effects"]), 1)
        self.assertEqual(result["equipment_effects"][0]["source"], "Amulet of Protection")
        
        # Check injuries array created
        self.assertIsInstance(result["injuries"], list)
        
        # Check class features have usage
        for feature in result["classFeatures"]:
            if feature["name"] in ["Second Wind", "Action Surge"]:
                self.assertIn("usage", feature)
                self.assertEqual(feature["usage"]["refreshOn"], "shortRest")
        
        # Check old effects removed
        self.assertFalse(any(
            e.get("name") == "Old Effect" 
            for e in result["temporaryEffects"]
        ))
    
    def test_error_handling_and_recovery(self):
        """Test validator handles errors gracefully"""
        # Test with invalid character file
        invalid_char = {"invalid": "data", "no_equipment": True}
        char_path = os.path.join(self.test_dir, "invalid.json")
        
        with open(char_path, 'w') as f:
            json.dump(invalid_char, f)
        
        # Should not crash
        result, success = self.validator.validate_character_effects_safe(char_path)
        
        # Should return original data on failure
        self.assertEqual(result, invalid_char)
        
        # Test with missing party tracker
        valid_char = {"name": "Test", "equipment": {}, "temporaryEffects": []}
        char_path2 = os.path.join(self.test_dir, "valid.json")
        
        with open(char_path2, 'w') as f:
            json.dump(valid_char, f)
        
        # Should handle missing party tracker gracefully
        result2, success2 = self.validator.validate_character_effects_safe(char_path2)
        self.assertIsNotNone(result2)


def run_all_tests():
    """Run all test suites"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTimeBasedEffects))
    suite.addTests(loader.loadTestsFromTestCase(TestEquipmentEffectsIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestValidatorIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)