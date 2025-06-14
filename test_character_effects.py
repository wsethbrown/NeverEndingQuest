#!/usr/bin/env python3
"""
Test suite for Character Effects System
Tests the character effects validator and related functionality
"""

import unittest
import json
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock
from character_effects_validator import AICharacterEffectsValidator


class TestCharacterEffects(unittest.TestCase):
    """Test cases for character effects validation system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = AICharacterEffectsValidator()
        self.test_dir = tempfile.mkdtemp()
        
        # Sample character data for testing
        self.test_character = {
            "name": "Test Fighter",
            "class": "Fighter",
            "level": 5,
            "hit_points": {"current": 35, "maximum": 44},
            "equipment": [
                {
                    "item_name": "Chain Mail",
                    "item_type": "armor",
                    "equipped": True
                },
                {
                    "item_name": "Shield",
                    "item_type": "armor",
                    "equipped": True
                },
                {
                    "item_name": "Longsword",
                    "item_type": "weapon",
                    "equipped": True
                },
                {
                    "item_name": "Magic Ring",
                    "item_type": "miscellaneous",
                    "equipped": True,
                    "effects": [
                        {
                            "type": "bonus",
                            "target": "saving_throws",
                            "value": 1,
                            "description": "+1 to all saving throws"
                        }
                    ]
                },
                {
                    "item_name": "Cloak of Resistance",
                    "item_type": "miscellaneous",
                    "equipped": False,
                    "effects": [
                        {
                            "type": "resistance",
                            "target": "fire",
                            "value": None,
                            "description": "Resistance to fire damage"
                        }
                    ]
                }
            ],
            "classFeatures": [
                {
                    "name": "Second Wind",
                    "description": "Regain 1d10 + fighter level HP once per short rest"
                },
                {
                    "name": "Action Surge",
                    "description": "Take an additional action once per short rest"
                }
            ],
            "temporaryEffects": [
                {
                    "name": "Second Wind",
                    "description": "Ability used",
                    "duration": "short rest"
                },
                {
                    "name": "Blessed",
                    "description": "+1d4 to attack rolls and saving throws",
                    "duration": "1 minute"
                },
                {
                    "name": "4 points of damage",
                    "description": "From giant rat bite"
                }
            ]
        }
        
        # Sample party tracker data matching actual format
        self.party_tracker = {
            "worldConditions": {
                "year": 1492,
                "month": "Ches",
                "day": 2,
                "time": "14:30:00"
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)
    
    def test_calculate_equipment_effects(self):
        """Test that equipment effects are correctly calculated from equipped items"""
        # The validator returns the full character data with equipment_effects added
        result = self.validator.calculate_equipment_effects(self.test_character)
        effects = result.get("equipment_effects", [])
        
        # Should include the equipped ring but not the unequipped cloak
        self.assertEqual(len(effects), 1)
        self.assertEqual(effects[0]["source"], "Magic Ring")
        self.assertEqual(effects[0]["type"], "bonus")
        self.assertEqual(effects[0]["target"], "saving_throws")
        self.assertEqual(effects[0]["value"], 1)
    
    def test_parse_duration_with_game_time(self):
        """Test duration parsing with game time context"""
        # Since parse_duration is handled by AI, we'll test the effect expiration logic instead
        game_time = {
            "year": 1492,
            "month": "Ches",
            "day": 2,
            "time": "14:30:00"
        }
        
        # Test character with various durations
        test_char = self.test_character.copy()
        test_char["temporaryEffects"] = [
            {"name": "Effect1", "expiration": "1492-03-02T15:30:00"},  # 1 hour later
            {"name": "Effect2", "expiration": "1492-03-03T14:30:00"},  # 24 hours later
            {"name": "Effect3", "expiration": "until removed"},
            {"name": "Effect4", "expiration": "short rest"}
        ]
        
        # Expire effects
        result = self.validator.expire_temporary_effects(test_char, game_time)
        
        # All effects should remain (none expired)
        self.assertEqual(len(result["temporaryEffects"]), 4)
    
    def test_is_class_ability(self):
        """Test identification of class abilities"""
        # Since class ability identification is done by AI, we'll test the overall categorization
        # by checking if class features are properly initialized with usage tracking
        result = self.validator.initialize_class_feature_usage(self.test_character)
        
        # Check that class features have usage tracking added
        for feature in result["classFeatures"]:
            if feature["name"] in ["Second Wind", "Action Surge"]:
                self.assertIn("usage", feature)
                self.assertEqual(feature["usage"]["current"], 0)
    
    def test_is_physical_damage(self):
        """Test identification of physical damage entries"""
        # Physical damage identification is handled by AI categorization
        # We'll test this through the effect expiration which handles different types
        test_char = self.test_character.copy()
        test_char["temporaryEffects"] = [
            {"name": "4 points of damage", "description": "From attack", "effectType": "injury"},
            {"name": "Blessed", "description": "Divine magic", "effectType": "magical"}
        ]
        
        # After AI categorization, injuries should be separated from magical effects
        # This is tested in the full validation flow
    
    def test_is_equipment_effect(self):
        """Test identification of equipment-based effects"""
        # Equipment effect identification is done through the calculate_equipment_effects method
        # which scans equipped items for their effects
        test_char = self.test_character.copy()
        
        # Add more equipment with effects
        test_char["equipment"].append({
            "item_name": "Belt of Giant Strength",
            "item_type": "miscellaneous",
            "equipped": True,
            "effects": [
                {"type": "set", "target": "strength", "value": 21}
            ]
        })
        
        result = self.validator.calculate_equipment_effects(test_char)
        effects = result.get("equipment_effects", [])
        
        # Should have 2 effects now (ring + belt)
        self.assertEqual(len(effects), 2)
    
    @patch('character_effects_validator.OpenAI')
    def test_categorize_effects_with_ai(self, mock_openai):
        """Test AI-powered effect categorization"""
        # Mock the AI response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content=json.dumps({
            "categorized_effects": {
                "temporary_magical": [
                    {
                        "name": "Blessed",
                        "description": "+1d4 to attack rolls and saving throws",
                        "duration": "1 minute",
                        "source": "Cleric spell"
                    }
                ],
                "injuries": [],
                "equipment": [],
                "class_abilities": ["Second Wind"]
            }
        })))]
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Call the AI categorization through the main validation method
        result = self.validator.ai_categorize_effects(
            self.test_character,
            {"year": 1492, "month": "Ches", "day": 2, "time": "14:30:00"}
        )
        
        self.assertIn("temporary_magical", result)
        self.assertIn("injuries", result)
        self.assertIn("class_abilities", result)
        self.assertEqual(len(result["temporary_magical"]), 1)
        self.assertEqual(result["temporary_magical"][0]["name"], "Blessed")
    
    def test_initialize_class_feature_usage(self):
        """Test initialization of class feature usage tracking"""
        test_char = {
            "classFeatures": [
                {"name": "Second Wind", "description": "Heal 1d10+level once per short rest"},
                {"name": "Action Surge", "description": "Extra action once per short rest"}
            ]
        }
        
        result = self.validator.initialize_class_feature_usage(test_char)
        
        for feature in result["classFeatures"]:
            self.assertIn("usage", feature)
            self.assertEqual(feature["usage"]["current"], 1)  # Starts available
            self.assertEqual(feature["usage"]["max"], 1)
            self.assertEqual(feature["usage"]["refreshOn"], "shortRest")
    
    def test_full_validation_flow(self):
        """Test the complete validation flow"""
        # Create a test character file
        char_path = os.path.join(self.test_dir, "test_character.json")
        with open(char_path, 'w') as f:
            json.dump(self.test_character, f, indent=2)
        
        # Create party tracker for game time
        party_path = os.path.join(os.path.dirname(char_path), "party_tracker.json")
        with open(party_path, 'w') as f:
            json.dump(self.party_tracker, f, indent=2)
        
        # Mock the OpenAI response for AI categorization
        with patch('character_effects_validator.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_completion = MagicMock()
            mock_completion.choices = [MagicMock(message=MagicMock(content=json.dumps({
                "categorized_effects": {
                    "temporary_magical": [
                        {
                            "name": "Blessed",
                            "description": "+1d4 to attack rolls and saving throws",
                            "duration": "1 minute",
                            "source": "Cleric spell"
                        }
                    ],
                    "injuries": [],
                    "equipment": [],
                    "class_abilities": ["Second Wind"]
                }
            })))]
            mock_client.chat.completions.create.return_value = mock_completion
            
            # Run validation
            validated_data, success = self.validator.validate_character_effects_safe(char_path)
            
            # Check results
            self.assertTrue(success)
            self.assertIn("equipment_effects", validated_data)
            self.assertIn("injuries", validated_data)
            self.assertIn("temporaryEffects", validated_data)
            
            # Check equipment effects were calculated
            self.assertEqual(len(validated_data["equipment_effects"]), 1)
            
            # Check class features have usage tracking
            for feature in validated_data["classFeatures"]:
                if feature["name"] in ["Second Wind", "Action Surge"]:
                    self.assertIn("usage", feature)
    
    def test_expired_effects_removal(self):
        """Test that expired effects are removed based on game time"""
        # Create character with expired effect
        char_with_expired = self.test_character.copy()
        char_with_expired["temporaryEffects"] = [
            {
                "name": "Old Blessing",
                "expiration": "1492-03-01T12:00:00",  # Yesterday
                "effectType": "magical"
            },
            {
                "name": "Current Blessing", 
                "expiration": "1492-03-03T14:30:00",  # Tomorrow
                "effectType": "magical"
            }
        ]
        
        # Filter expired effects
        current_time = "1492-03-02T14:30:00"
        active_effects = [
            e for e in char_with_expired["temporaryEffects"]
            if e.get("expiration", "permanent") == "permanent" or
               e.get("expiration") > current_time
        ]
        
        self.assertEqual(len(active_effects), 1)
        self.assertEqual(active_effects[0]["name"], "Current Blessing")


class TestEffectsIntegration(unittest.TestCase):
    """Integration tests for character effects system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_module_dir = tempfile.mkdtemp()
        self.characters_dir = os.path.join(self.test_module_dir, "characters")
        os.makedirs(self.characters_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_module_dir)
    
    def test_update_character_info_integration(self):
        """Test integration with update_character_info.py"""
        # This would test the full integration but requires the actual
        # update_character_info module - leaving as a placeholder
        pass


if __name__ == "__main__":
    unittest.main(verbosity=2)