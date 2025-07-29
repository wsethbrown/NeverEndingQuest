# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
NeverEndingQuest Mythic Bastionland - Character Validator
Copyright (c) 2024 MoonlightByte
Licensed under Fair Source License 1.0

See LICENSE file for full terms.
"""

# ============================================================================
# MYTHIC_CHARACTER_VALIDATOR.PY - AI-POWERED MYTHIC BASTIONLAND CHARACTER VALIDATION
# ============================================================================
#
# ARCHITECTURE ROLE: AI Integration Layer - Mythic Bastionland Character Data Validation
#
# This module provides intelligent AI-powered character validation ensuring data
# integrity and Mythic Bastionland rule compliance through GPT-4 reasoning and validation,
# with automatic correction capabilities for common data inconsistencies.
#
# KEY RESPONSIBILITIES:
# - AI-driven character data validation with Mythic Bastionland rule compliance
# - Virtue (VIG/CLA/SPI) validation and calculation verification
# - Equipment categorization and conflict resolution for Mythic Bastionland items
# - Trade good validation (no currency - barter system only)
# - Guard calculation and scar system validation
# - Glory and rank progression validation
# - Knight property and ability validation
# - Integration with Mythic Bastionland schema validation
#

"""
AI-Powered Mythic Bastionland Character Validator

An intelligent validation system that uses AI to ensure character data integrity
based on Mythic Bastionland rules and mechanics.

Uses GPT-4.1 to intelligently validate and auto-correct:
- Virtue calculations (VIG/CLA/SPI ranges 2-19)
- Guard values and scar integration
- Equipment categorization for Mythic Bastionland items
- Trade goods validation (barter system, no coins)
- Glory/rank progression consistency
- Knight properties and abilities
- Age category effects on Virtues

MYTHIC BASTIONLAND VALIDATION SYSTEM:
Ensures characters follow the three-virtue system and barter economy.
Key validations:
1. VIRTUES: VIG/CLA/SPI in valid ranges with age modifiers
2. GUARD: Proper calculation including scar bonuses
3. EQUIPMENT: Mythic Bastionland item types and restrictions
4. TRADE: Barter system compliance (no coins, Common/Uncommon/Rare items)
5. GLORY: Rank progression based on glory points
6. KNIGHT PROPERTIES: Validation of knight-specific abilities and equipment

The AI reasons through Mythic Bastionland rules rather than following hardcoded logic,
making it flexible and adaptable to any character structure or edge case.
"""

import json
import copy
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from config import OPENAI_API_KEY, CHARACTER_VALIDATOR_MODEL
from utils.file_operations import safe_read_json, safe_write_json
from utils.enhanced_logger import debug, info, warning, error, set_script_name

# Set script name for logging
set_script_name(__name__)

class MythicCharacterValidator:
    def __init__(self):
        """Initialize AI-powered Mythic Bastionland validator"""
        self.logger = logging.getLogger(__name__)
        try:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
        except Exception as e:
            error(f"Failed to initialize OpenAI client: {str(e)}", exception=e, category="character_validation")
            error(f"OpenAI client initialization failed. This is likely an environment issue.", category="character_validation")
            error(f"Error details: {type(e).__name__}: {str(e)}", category="character_validation")
            info("Possible solutions:", category="character_validation")
            info("1. Check if OpenAI library is properly installed: pip install openai==1.30.3", category="character_validation")
            info("2. There may be a proxy or environment configuration issue", category="character_validation")
            info("3. Try running in a different environment", category="character_validation")
            raise
        self.corrections_made = []
        
    def validate_and_correct_character(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered validation and correction of Mythic Bastionland character data
        
        Args:
            character_data: Character JSON data following mythic schema
            
        Returns:
            AI-corrected character data with proper Mythic Bastionland compliance
        """
        self.corrections_made = []
        
        # Log activation message for user visibility in debug window
        character_name = character_data.get('name', 'Unknown')
        # Use print for immediate visibility in debug tab
        print(f"DEBUG: [Mythic Validator] Activating character validator for {character_name}...")
        info(f"[Mythic Validator] Activating character validator for {character_name}...", category="character_validation")
        
        # OPTIMIZATION: Batch all validations into a single AI call
        corrected_data = self.ai_validate_all_batched(character_data)
        
        # Validate Glory-Rank consistency (non-AI validation)
        corrected_data = self.validate_glory_rank_consistency(corrected_data)
        
        # Validate virtue ranges and age effects
        corrected_data = self.validate_virtue_ranges(corrected_data)
        
        # Log completion message
        if self.corrections_made:
            print(f"DEBUG: [Mythic Validator] Character validation complete for {character_name}: {len(self.corrections_made)} corrections made")
            info(f"[Mythic Validator] Character validation complete for {character_name}: {len(self.corrections_made)} corrections made", category="character_validation")
            for correction in self.corrections_made:
                print(f"DEBUG:   - {correction}")
                info(f"  - {correction}", category="character_validation")
        else:
            print(f"DEBUG: [Mythic Validator] Character validation complete for {character_name}: No corrections needed")
            info(f"[Mythic Validator] Character validation complete for {character_name}: No corrections needed", category="character_validation")
        
        return corrected_data
    
    def ai_validate_all_batched(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        OPTIMIZED: Batch all AI validations into a single request
        Combines virtue validation, equipment categorization, guard calculation, and knight validation
        
        Args:
            character_data: Character JSON data
            
        Returns:
            Character data with all AI corrections applied
        """
        character_name = character_data.get('name', 'Unknown')
        
        # Build combined validation prompt
        validation_prompt = self.build_combined_validation_prompt(character_data)
        
        try:
            response = self.client.chat.completions.create(
                model=CHARACTER_VALIDATOR_MODEL,
                temperature=0.1,  # Low temperature for consistent validation
                messages=[
                    {"role": "system", "content": self.get_mythic_validator_system_prompt()},
                    {"role": "user", "content": validation_prompt}
                ]
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse AI response to get all corrections
            corrected_data = self.parse_combined_validation_response(ai_response, character_data)
            
            return corrected_data
            
        except Exception as e:
            self.logger.error(f"Batched Mythic AI validation failed: {str(e)}")
            return character_data
    
    def get_mythic_validator_system_prompt(self) -> str:
        """
        System prompt for combined Mythic Bastionland validation tasks
        """
        return """You are an expert character validator for Mythic Bastionland. 
You must perform FOUR validation tasks in a single response:

1. VIRTUE AND GUARD VALIDATION
2. EQUIPMENT CATEGORIZATION
3. TRADE GOODS VALIDATION (BARTER SYSTEM)
4. KNIGHT PROPERTY VALIDATION

## TASK 1: VIRTUE AND GUARD VALIDATION

Validate that Virtues (VIG/CLA/SPI) are in valid ranges and Guard is calculated correctly.

### Virtue Rules:
- All Virtues range from 2-19
- Age effects: Young (+1 to one Virtue), Mature (no change), Old (-1 to one Virtue, +1 to another)
- Starting values based on campaign type:
  - Wanderer: d12+d6 for each Virtue
  - Courtier: d12+6 for each Virtue  
  - Ruler: d12+6 for each Virtue

### Guard Rules:
- Base Guard determined by campaign start and dice rolls
- Scars can increase Guard permanently
- Guard is fully restored after danger passes

## TASK 2: EQUIPMENT CATEGORIZATION

Validate equipment types for Mythic Bastionland system.

Valid equipment types:
- "weapon" - swords, bows, daggers, any combat item with damage
- "armour" - armor pieces, shields, protective gear with armour value
- "tool" - utility items, torches, rope, climbing gear, instruments
- "remedy" - healing items, potions, medical supplies
- "misc" - everything else, trinkets, valuables, trade goods

Equipment restrictions:
- "hefty" - requires two hands or significant strength
- "long" - extended reach, may be unwieldy in close quarters  
- "slow" - takes time to use effectively

## TASK 3: TRADE GOODS VALIDATION (BARTER SYSTEM)

Mythic Bastionland uses NO COINS. All trade is barter-based.

Trade item rarity:
- "common" - widely available, basic necessities
- "uncommon" - requires a specialist, moderate value
- "rare" - truly treasured, exceptional value

CRITICAL: Remove any coin references (gold pieces, silver, copper). 
Replace with appropriate trade goods of equivalent rarity.

## TASK 4: KNIGHT PROPERTY VALIDATION

Validate Knight-specific properties and abilities.

Knight properties must include:
- Items: Special equipment brought by this Knight type
- Ability: Unique talent for this Knight type
- Passion: Special means to restore Spirit

Glory and Rank progression:
- Knight-Errant: Glory 0-2
- Knight-Gallant: Glory 3-5
- Knight-Tenant: Glory 6-8
- Knight-Dominant: Glory 9-11
- Knight-Radiant: Glory 12

## COMBINED OUTPUT FORMAT:

Return a single JSON response with all corrections:
{
  "virtue_validation": {
    "vigour_corrected": 14,
    "clarity_corrected": 12,
    "spirit_corrected": 16,
    "guard_corrected": 8,
    "corrections": ["List of virtue/guard corrections made"]
  },
  "equipment_corrections": {
    "corrections_made": ["List of equipment corrections"],
    "equipment": [
      {
        "name": "exact item name",
        "type": "corrected_type",
        "restrictions": ["hefty", "long"],
        "rarity": "common"
      }
    ]
  },
  "trade_validation": {
    "corrections_made": ["List of trade corrections"],
    "items_to_remove": ["5 gold pieces", "bag of silver"],
    "items_to_add": [
      {
        "name": "Fine woolen cloth",
        "type": "misc", 
        "rarity": "uncommon",
        "description": "Valuable trade good equivalent to removed coins"
      }
    ]
  },
  "knight_validation": {
    "rank_corrected": "Knight-Gallant",
    "corrections_made": ["Rank should be Knight-Gallant for Glory 4"],
    "property_corrections": ["List of knight property corrections"]
  }
}

IMPORTANT: Perform ALL FOUR validations and return results for each in the combined JSON response.
"""
    
    def build_combined_validation_prompt(self, character_data: Dict[str, Any]) -> str:
        """
        Build a combined prompt for all Mythic Bastionland validations
        """
        character_name = character_data.get('name', 'Unknown')
        
        combined_prompt = f"""Please validate ALL aspects of this Mythic Bastionland character in a single response:

CHARACTER NAME: {character_name}

=== FULL CHARACTER DATA ===
{json.dumps(character_data, indent=2)}

=== VALIDATION TASKS ===

1. VIRTUE AND GUARD VALIDATION:
   - Check Virtue ranges (2-19)
   - Validate age effects on Virtues
   - Verify Guard calculation including scar bonuses

2. EQUIPMENT CATEGORIZATION:
   - Ensure all equipment has correct Mythic Bastionland types
   - Validate restrictions (hefty, long, slow)
   - Check rarity assignments

3. TRADE GOODS VALIDATION:
   - Remove any coin references (this is a barter system)
   - Replace coins with appropriate trade goods
   - Validate rarity levels (common/uncommon/rare)

4. KNIGHT PROPERTY VALIDATION:
   - Verify knight properties are complete (items, ability, passion)
   - Check Glory-Rank consistency
   - Validate knight-specific abilities

Remember to return a single JSON response with all four validation results."""
        
        return combined_prompt
    
    def parse_combined_validation_response(self, ai_response: str, original_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse the combined AI validation response for Mythic Bastionland
        """
        try:
            # Try to extract JSON from AI response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = ai_response[start_idx:end_idx]
                parsed_response = json.loads(json_str)
                
                result_data = copy.deepcopy(original_data)
                
                # Process virtue/guard validation
                if 'virtue_validation' in parsed_response:
                    virtue_result = parsed_response['virtue_validation']
                    
                    # Update virtues if corrected
                    if 'vigour_corrected' in virtue_result:
                        if 'virtues' not in result_data:
                            result_data['virtues'] = {}
                        result_data['virtues']['vigour'] = virtue_result['vigour_corrected']
                    
                    if 'clarity_corrected' in virtue_result:
                        if 'virtues' not in result_data:
                            result_data['virtues'] = {}
                        result_data['virtues']['clarity'] = virtue_result['clarity_corrected']
                    
                    if 'spirit_corrected' in virtue_result:
                        if 'virtues' not in result_data:
                            result_data['virtues'] = {}
                        result_data['virtues']['spirit'] = virtue_result['spirit_corrected']
                    
                    if 'guard_corrected' in virtue_result:
                        result_data['guard'] = virtue_result['guard_corrected']
                    
                    if 'corrections' in virtue_result:
                        self.corrections_made.extend(virtue_result['corrections'])
                
                # Process equipment corrections
                if 'equipment_corrections' in parsed_response:
                    eq_result = parsed_response['equipment_corrections']
                    if 'corrections_made' in eq_result:
                        self.corrections_made.extend(eq_result['corrections_made'])
                    
                    if 'equipment' in eq_result and eq_result['equipment']:
                        # Apply equipment updates using deep merge
                        from updates.update_character_info import deep_merge_dict
                        equipment_updates = {'equipment': eq_result['equipment']}
                        result_data = deep_merge_dict(result_data, equipment_updates)
                
                # Process trade validation
                if 'trade_validation' in parsed_response:
                    trade_result = parsed_response['trade_validation']
                    if 'corrections_made' in trade_result:
                        self.corrections_made.extend(trade_result['corrections_made'])
                    
                    # Remove coin items
                    if 'items_to_remove' in trade_result and 'equipment' in result_data:
                        items_to_remove = set(trade_result['items_to_remove'])
                        result_data['equipment'] = [
                            item for item in result_data['equipment']
                            if item.get('name') not in items_to_remove
                        ]
                    
                    # Add trade goods
                    if 'items_to_add' in trade_result and trade_result['items_to_add']:
                        if 'equipment' not in result_data:
                            result_data['equipment'] = []
                        result_data['equipment'].extend(trade_result['items_to_add'])
                
                # Process knight validation
                if 'knight_validation' in parsed_response:
                    knight_result = parsed_response['knight_validation']
                    if 'corrections_made' in knight_result:
                        self.corrections_made.extend(knight_result['corrections_made'])
                    
                    if 'rank_corrected' in knight_result:
                        result_data['rank'] = knight_result['rank_corrected']
                    
                    if 'property_corrections' in knight_result:
                        self.corrections_made.extend(knight_result['property_corrections'])
                
                return result_data
                
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse combined Mythic AI response: {str(e)}")
            self.logger.debug(f"AI Response was: {ai_response}")
        
        # Return original data if parsing fails
        return original_data
    
    def validate_glory_rank_consistency(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and correct Glory-Rank consistency
        
        Args:
            character_data: Character JSON data
            
        Returns:
            Character data with corrected Glory-Rank consistency
        """
        glory = character_data.get("glory", 0)
        current_rank = character_data.get("rank", "Knight-Errant")
        
        # Determine correct rank based on glory
        if glory <= 2:
            correct_rank = "Knight-Errant"
        elif glory <= 5:
            correct_rank = "Knight-Gallant"
        elif glory <= 8:
            correct_rank = "Knight-Tenant"
        elif glory <= 11:
            correct_rank = "Knight-Dominant"
        else:  # glory >= 12
            correct_rank = "Knight-Radiant"
        
        if current_rank != correct_rank:
            corrected_data = character_data.copy()
            corrected_data["rank"] = correct_rank
            
            correction = f"Rank corrected from {current_rank} to {correct_rank} based on Glory {glory}"
            self.corrections_made.append(correction)
            
            self.logger.info(f"Corrected Glory-Rank inconsistency: {correction}")
            
            return corrected_data
        
        # No corrections needed
        return character_data
    
    def validate_virtue_ranges(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that all Virtues are within valid ranges (2-19)
        
        Args:
            character_data: Character JSON data
            
        Returns:
            Character data with corrected Virtue ranges
        """
        virtues = character_data.get("virtues", {})
        corrected_data = character_data.copy()
        corrections_needed = False
        
        for virtue_name in ["vigour", "clarity", "spirit"]:
            value = virtues.get(virtue_name, 10)  # Default to 10 if missing
            
            if value < 2:
                corrected_data.setdefault("virtues", {})[virtue_name] = 2
                self.corrections_made.append(f"{virtue_name.capitalize()} corrected from {value} to 2 (minimum)")
                corrections_needed = True
            elif value > 19:
                corrected_data.setdefault("virtues", {})[virtue_name] = 19
                self.corrections_made.append(f"{virtue_name.capitalize()} corrected from {value} to 19 (maximum)")
                corrections_needed = True
        
        if corrections_needed:
            self.logger.info("Corrected Virtue range violations")
            
        return corrected_data
    
    def validate_character_file_safe(self, file_path: str) -> tuple[Dict[str, Any], bool]:
        """
        Validate Mythic Bastionland character file using atomic file operations
        
        Args:
            file_path: Path to character JSON file
            
        Returns:
            Tuple of (character_data, success_flag)
        """
        try:
            # Load character data using safe file operations
            character_data = safe_read_json(file_path)
            if character_data is None:
                self.logger.error(f"Could not read character file {file_path}")
                return {}, False
            
            # AI validation and correction
            corrected_data = self.validate_and_correct_character(character_data)
            
            # Save if corrections were made using atomic file operations
            if self.corrections_made:
                success = safe_write_json(file_path, corrected_data)
                if success:
                    self.logger.info(f"Mythic character file validated and corrected: {file_path}")
                    return corrected_data, True
                else:
                    self.logger.error(f"Failed to save corrected mythic character data to {file_path}")
                    return character_data, False
            else:
                self.logger.debug(f"Mythic character file validated - no corrections needed: {file_path}")
                return corrected_data, True
                
        except Exception as e:
            self.logger.error(f"Error validating mythic character file {file_path}: {str(e)}")
            return {}, False


def validate_mythic_character_file(file_path: str) -> bool:
    """
    Convenience function to validate a Mythic Bastionland character file using AI with atomic file operations
    
    Args:
        file_path: Path to character JSON file
        
    Returns:
        True if validation successful, False otherwise
    """
    try:
        # Load character data using safe file operations
        character_data = safe_read_json(file_path)
        if character_data is None:
            error(f"FAILURE: Could not read mythic character file {file_path}", category="file_operations")
            return False
        
        # AI validation and correction
        validator = MythicCharacterValidator()
        corrected_data = validator.validate_and_correct_character(character_data)
        
        # Save if corrections were made using atomic file operations
        if validator.corrections_made:
            success = safe_write_json(file_path, corrected_data)
            if success:
                info(f"SUCCESS: Mythic AI Corrections made: {validator.corrections_made}", category="character_validation")
                return True
            else:
                error(f"FAILURE: Failed to save corrected mythic character data to {file_path}", category="file_operations")
                return False
        else:
            debug("VALIDATION: No corrections needed - mythic character data is valid", category="character_validation")
            return True
        
    except Exception as e:
        error(f"FAILURE: Error validating mythic character file {file_path}", exception=e, category="character_validation")
        return False


if __name__ == "__main__":
    # Test with mythic character file
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        validate_mythic_character_file(file_path)
    else:
        # Test with default mythic character
        print("Usage: python mythic_character_validator.py <character_file_path>")