# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

# ============================================================================
# CHARACTER_EFFECTS_VALIDATOR.PY - AI-POWERED EFFECTS VALIDATION
# ============================================================================
#
# ARCHITECTURE ROLE: AI Integration Layer - Character Effects Validation
#
# This module provides intelligent AI-powered validation and management of character
# effects, using GPT-4 to reason through complex effect categorization and state
# management that would be difficult with hardcoded logic.
#
# KEY RESPONSIBILITIES:
# - AI-driven categorization of mixed character effects into proper arrays
# - Intelligent equipment effect calculation from equipped items
# - Duration format standardization to timestamps for consistent tracking
# - Class feature usage tracking and state management
# - Time-based effect expiration with game world time integration
# - Flexible effect validation adaptable to any character structure
# - Complex effect interaction resolution through AI reasoning
#

"""
AI-Powered Character Effects Validator - UPDATED FOR MYTHIC BASTIONLAND

An intelligent validation system that uses AI to manage character effects,
including temporary effects, injuries, equipment bonuses, and Knight abilities.

Uses GPT-4 to intelligently:
- Categorize mixed effects into proper arrays
- Calculate equipment effects from equipped items
- Standardize duration formats to timestamps
- Track Knight ability usage and Virtue damage
- Expire effects based on game time
- Manage Guard damage and recovery
- Track trade goods and barter system effects

Updated for Mythic Bastionland:
- Replaces "class features" with "Knight abilities"
- Uses Guard system instead of AC
- Tracks Virtue damage (VIG/CLA/SPI) instead of ability scores
- Manages Glory-based effects and rank-related bonuses

The AI reasons through the categorization rather than following hardcoded logic,
making it flexible and adaptable to any character structure or edge case.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from openai import OpenAI
from config import OPENAI_API_KEY, CHARACTER_VALIDATOR_MODEL
from utils.file_operations import safe_read_json, safe_write_json
from utils.module_path_manager import ModulePathManager

class AICharacterEffectsValidator:
    def __init__(self):
        """Initialize AI-powered effects validator"""
        self.logger = logging.getLogger(__name__)
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.corrections_made = []
        # Get current module from party tracker for consistent path resolution
        try:
            from utils.encoding_utils import safe_json_load
            party_tracker = safe_json_load("party_tracker.json")
            current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
            self.path_manager = ModulePathManager(current_module)
        except:
            self.path_manager = ModulePathManager()  # Fallback to reading from file
        
    def validate_and_correct_effects(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered validation and correction of character effects
        
        Args:
            character_data: Character JSON data
            
        Returns:
            AI-corrected character data with proper effect categorization
        """
        self.corrections_made = []
        
        # Get current game time from party tracker
        game_time = self.get_current_game_time()
        
        # Step 1: Categorize mixed effects using AI
        corrected_data = self.ai_categorize_effects(character_data, game_time)
        
        # Step 2: Calculate equipment effects
        corrected_data = self.calculate_equipment_effects(corrected_data)
        
        # Step 3: Expire outdated temporary effects
        corrected_data = self.expire_temporary_effects(corrected_data, game_time)
        
        # Step 4: Initialize Knight ability usage if needed
        corrected_data = self.initialize_class_feature_usage(corrected_data)
        
        return corrected_data
    
    def get_current_game_time(self) -> Dict[str, Any]:
        """Get current game time from party tracker"""
        try:
            party_data = safe_read_json("party_tracker.json")
            if party_data and 'worldConditions' in party_data:
                world = party_data['worldConditions']
                return {
                    'year': world.get('year', 1492),
                    'month': world.get('month', 'Springmonth'),
                    'day': world.get('day', 1),
                    'time': world.get('time', '00:00:00')
                }
        except Exception as e:
            self.logger.error(f"Could not load game time: {str(e)}")
        
        # Default time if not found
        return {'year': 1492, 'month': 'Springmonth', 'day': 1, 'time': '00:00:00'}
    
    def calculate_equipment_effects(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate equipment effects from equipped items
        
        Args:
            character_data: Character JSON data
            
        Returns:
            Character data with calculated equipment_effects
        """
        equipment_effects = []
        
        # Check all equipped items for effects
        if 'equipment' in character_data:
            for item in character_data['equipment']:
                if item.get('equipped', False) and 'effects' in item:
                    # Add each effect from the equipped item
                    for effect in item['effects']:
                        equipment_effect = {
                            'name': f"{item['item_name']} - {effect.get('type', 'effect').title()}",
                            'type': effect.get('type', 'other'),
                            'target': effect.get('target', ''),
                            'value': effect.get('value'),
                            'description': effect.get('description', ''),
                            'source': item['item_name']
                        }
                        equipment_effects.append(equipment_effect)
        
        # Add Knight ability effects that are always active
        if 'classFeatures' in character_data:
            for feature in character_data['classFeatures']:
                # Check for passive bonuses like Fighting Style: Defense
                if 'Fighting Style: Defense' in feature.get('name', ''):
                    equipment_effects.append({
                        'name': 'Fighting Style: Defense',
                        'type': 'bonus',
                        'target': 'Guard',
                        'value': 1,
                        'description': '+1 to Guard when wearing armor',
                        'source': 'Class Feature'
                    })
        
        # Check for shield bonus
        if 'equipment' in character_data:
            for item in character_data['equipment']:
                if (item.get('equipped', False) and 
                    item.get('item_type') == 'armor' and 
                    item.get('armor_category') == 'shield'):
                    equipment_effects.append({
                        'name': 'Shield Guard Bonus',
                        'type': 'bonus',
                        'target': 'Guard',
                        'value': item.get('ac_bonus', 2),
                        'description': f"Shield provides +{item.get('ac_bonus', 2)} Guard",
                        'source': item['item_name']
                    })
        
        # Update character data
        character_data['equipment_effects'] = equipment_effects
        
        if len(equipment_effects) > 0:
            self.corrections_made.append(f"Calculated {len(equipment_effects)} equipment effects")
        
        return character_data
    
    def expire_temporary_effects(self, character_data: Dict[str, Any], game_time: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove expired temporary effects based on game time
        
        Args:
            character_data: Character JSON data
            game_time: Current game time
            
        Returns:
            Character data with expired effects removed
        """
        if 'temporaryEffects' not in character_data:
            return character_data
        
        current_datetime = self.game_time_to_datetime(game_time)
        active_effects = []
        expired_count = 0
        
        for effect in character_data['temporaryEffects']:
            if 'expiration' in effect:
                try:
                    expiration_dt = datetime.fromisoformat(effect['expiration'].replace('Z', '+00:00'))
                    if expiration_dt > current_datetime:
                        active_effects.append(effect)
                    else:
                        expired_count += 1
                        self.logger.info(f"Expired effect: {effect['name']}")
                except Exception as e:
                    self.logger.warning(f"Could not parse expiration for {effect['name']}: {str(e)}")
                    active_effects.append(effect)
            else:
                # Keep effects without expiration
                active_effects.append(effect)
        
        character_data['temporaryEffects'] = active_effects
        
        if expired_count > 0:
            self.corrections_made.append(f"Removed {expired_count} expired temporary effects")
        
        return character_data
    
    def game_time_to_datetime(self, game_time: Dict[str, Any]) -> datetime:
        """Convert game time to datetime object"""
        # Month conversion (SRD-compliant fantasy calendar)
        month_map = {
            'Firstmonth': 1, 'Coldmonth': 2, 'Thawmonth': 3, 'Springmonth': 4,
            'Bloommonth': 5, 'Sunmonth': 6, 'Heatmonth': 7, 'Harvestmonth': 8,
            'Autumnmonth': 9, 'Fademonth': 10, 'Frostmonth': 11, 'Yearend': 12
        }
        
        month_num = month_map.get(game_time['month'], 4)  # Default to Springmonth
        time_parts = game_time['time'].split(':')
        
        return datetime(
            year=game_time['year'],
            month=month_num,
            day=game_time['day'],
            hour=int(time_parts[0]),
            minute=int(time_parts[1]),
            second=int(time_parts[2]) if len(time_parts) > 2 else 0
        )
    
    def initialize_class_feature_usage(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize usage tracking for class features that don't have it
        
        Args:
            character_data: Character JSON data
            
        Returns:
            Character data with initialized usage tracking
        """
        if 'classFeatures' not in character_data:
            return character_data
        
        features_updated = 0
        
        for feature in character_data['classFeatures']:
            # Check if this feature needs usage tracking
            name_lower = feature.get('name', '').lower()
            desc_lower = feature.get('description', '').lower()
            
            # Skip if already has usage
            if 'usage' in feature:
                continue
            
            # Pattern matching for limited use features
            if any(phrase in desc_lower for phrase in ['once per short rest', 'once per long rest', 
                                                       'uses per', 'times per', 'charges']):
                # Try to determine usage pattern
                if 'once per short rest' in desc_lower:
                    feature['usage'] = {
                        'current': 1,
                        'max': 1,
                        'refreshOn': 'shortRest'
                    }
                    features_updated += 1
                elif 'once per long rest' in desc_lower:
                    feature['usage'] = {
                        'current': 1,
                        'max': 1,
                        'refreshOn': 'longRest'
                    }
                    features_updated += 1
        
        if features_updated > 0:
            self.corrections_made.append(f"Initialized usage tracking for {features_updated} class features")
        
        return character_data
    
    def ai_categorize_effects(self, character_data: Dict[str, Any], game_time: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to categorize mixed effects into proper arrays
        
        Args:
            character_data: Character JSON data
            game_time: Current game time
            
        Returns:
            Character data with properly categorized effects
        """
        # Check if character has the new arrays
        if 'injuries' not in character_data:
            character_data['injuries'] = []
        if 'equipment_effects' not in character_data:
            character_data['equipment_effects'] = []
        
        # Only process if there are legacy mixed effects
        if 'temporaryEffects' not in character_data or not character_data['temporaryEffects']:
            return character_data
        
        # Check if any effects need categorization
        needs_categorization = any(
            effect for effect in character_data['temporaryEffects']
            if any(indicator in effect.get('description', '').lower() + effect.get('name', '').lower()
                  for indicator in ['damage', 'wound', 'equipment', 'class feature', 'fighting style'])
        )
        
        if not needs_categorization:
            return character_data
        
        categorization_prompt = self.build_categorization_prompt(character_data, game_time)
        
        try:
            response = self.client.chat.completions.create(
                model=CHARACTER_VALIDATOR_MODEL,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": self.get_effects_system_prompt()},
                    {"role": "user", "content": categorization_prompt}
                ]
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse AI response and update character data
            corrected_data = self.parse_ai_categorization_response(ai_response, character_data)
            
            return corrected_data
            
        except Exception as e:
            self.logger.error(f"AI categorization failed: {str(e)}")
            return character_data
    
    def get_effects_system_prompt(self) -> str:
        """System prompt for AI effects categorization"""
        return """You are an expert character effects validator for the 5th edition of the world's most popular role playing game. Your job is to categorize effects into the proper arrays based on their nature.

## EFFECT CATEGORIES

### temporaryEffects (Magical/Spell Effects Only)
- Spell effects with ongoing duration (Bless, Haste, etc.)
- Potion effects  
- Magical blessings or curses
- Environmental magical effects
- Any effect with a duration that expires
- NOT instant-use cantrips like Guidance (these are applied and consumed immediately)

### injuries (Ongoing Conditions)
- Poison (ongoing damage or penalties)
- Disease (stat penalties, disadvantages)
- Curses (non-magical afflictions)
- Persistent conditions beyond immediate damage
- NOT simple combat damage (that's just HP loss)

### equipment_effects (Auto-calculated, don't add manually)
- These are calculated from equipped items
- Should be empty in your response

### Should be REMOVED entirely:
- Class features (already in classFeatures array)
- Simple combat damage (piercing, slashing, etc. - just HP loss)
- Equipment bonuses (calculated automatically)
- Instant-use effects like Guidance (applied immediately, not tracked)
- Effects that say "expired" or "already used"

## DURATION STANDARDIZATION

Convert text durations to ISO timestamps:
- "24 hours" → Calculate from current game time
- "8 hours" → Calculate from current game time  
- "until healed" → Keep as-is (no expiration)
- "until removed" → Keep as-is (no expiration)

## RESPONSE FORMAT

```json
{
  "temporaryEffects": [
    {
      "name": "Effect Name",
      "description": "Effect description",
      "duration": "Original duration text",
      "expiration": "2023-03-15T14:30:00",
      "source": "Source of effect",
      "effectType": "magic"
    }
  ],
  "injuries": [
    {
      "type": "poison",
      "description": "Poisoned by giant spider",
      "damage": 0,
      "healingRequired": true,
      "source": "Giant Spider"
    }
  ],
  "removed_effects": [
    "List of effect names that were removed"
  ],
  "categorization_summary": "Brief summary of changes made"
}
```"""
    
    def build_categorization_prompt(self, character_data: Dict[str, Any], game_time: Dict[str, Any]) -> str:
        """Build prompt for AI categorization"""
        current_dt = self.game_time_to_datetime(game_time)
        
        return f"""Please categorize these character effects into the proper arrays.

Current game time: {current_dt.isoformat()}

Current temporaryEffects array:
```json
{json.dumps(character_data.get('temporaryEffects', []), indent=2)}
```

Character's class features (for reference, don't duplicate):
```json
{json.dumps([f['name'] for f in character_data.get('classFeatures', [])], indent=2)}
```

Instructions:
1. Move any poison/disease/curse effects to injuries array
2. Remove any class feature effects (already tracked in classFeatures)
3. Remove any simple combat damage (not an effect, just HP loss)
4. Keep only magical/spell effects in temporaryEffects
5. Calculate expiration timestamps for time-based effects
6. Set effectType for all temporary effects

Provide the corrected arrays following the response format."""
    
    def parse_ai_categorization_response(self, ai_response: str, original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI categorization response and update character data"""
        try:
            # Extract JSON from response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = ai_response[start_idx:end_idx]
                parsed_response = json.loads(json_str)
                
                # Update character data with categorized effects
                if 'temporaryEffects' in parsed_response:
                    original_data['temporaryEffects'] = parsed_response['temporaryEffects']
                
                if 'injuries' in parsed_response:
                    original_data['injuries'] = parsed_response['injuries']
                
                # Log changes
                if 'removed_effects' in parsed_response:
                    for removed in parsed_response['removed_effects']:
                        self.logger.info(f"Removed effect: {removed}")
                
                if 'categorization_summary' in parsed_response:
                    self.corrections_made.append(parsed_response['categorization_summary'])
                
                return original_data
                
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse AI categorization response: {str(e)}")
        
        return original_data
    
    def validate_character_effects_safe(self, file_path: str) -> tuple[Dict[str, Any], bool]:
        """
        Validate character effects using atomic file operations
        
        Args:
            file_path: Path to character JSON file
            
        Returns:
            Tuple of (character_data, success_flag)
        """
        try:
            # Load character data
            character_data = safe_read_json(file_path)
            if character_data is None:
                self.logger.error(f"Could not read character file {file_path}")
                return {}, False
            
            # AI validation and correction
            corrected_data = self.validate_and_correct_effects(character_data)
            
            # Save if corrections were made
            if self.corrections_made:
                success = safe_write_json(file_path, corrected_data)
                if success:
                    self.logger.info(f"Character effects validated and corrected: {file_path}")
                    return corrected_data, True
                else:
                    self.logger.error(f"Failed to save corrected character data to {file_path}")
                    return character_data, False
            else:
                self.logger.debug(f"Character effects validated - no corrections needed: {file_path}")
                return corrected_data, True
                
        except Exception as e:
            self.logger.error(f"Error validating character effects {file_path}: {str(e)}")
            return {}, False


def validate_character_effects(file_path: str) -> bool:
    """
    Convenience function to validate character effects
    
    Args:
        file_path: Path to character JSON file
        
    Returns:
        True if validation successful, False otherwise
    """
    try:
        validator = AICharacterEffectsValidator()
        _, success = validator.validate_character_effects_safe(file_path)
        
        if validator.corrections_made:
            print(f"Effects corrections made: {validator.corrections_made}")
        else:
            print("No effects corrections needed")
            
        return success
        
    except Exception as e:
        print(f"Error validating character effects: {str(e)}")
        return False


if __name__ == "__main__":
    # Test with character file
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        validate_character_effects(file_path)
    else:
        # Test with Norn
        validate_character_effects("modules/Keep_of_Doom/characters/norn.json")