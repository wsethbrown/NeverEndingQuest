# ============================================================================
# CHARACTER_VALIDATOR.PY - AI-POWERED CHARACTER DATA VALIDATION
# ============================================================================
#
# ARCHITECTURE ROLE: AI Integration Layer - Character Data Validation
#
# This module provides intelligent AI-powered character validation ensuring data
# integrity and 5th edition rule compliance through GPT-4 reasoning and validation,
# with automatic correction capabilities for common data inconsistencies.
#
# KEY RESPONSIBILITIES:
# - AI-driven character data validation with 5th edition rule compliance
# - Intelligent armor class calculation verification and correction
# - Inventory item categorization and equipment conflict resolution
# - Automatic data format standardization and correction
# - Character sheet integrity validation across all character components
# - Integration with character effects validation for comprehensive validation
#

"""
AI-Powered Character Validator

An intelligent validation system that uses AI to ensure character data integrity
based on the 5th edition of the world's most popular role playing game rules.

Uses GPT-4.1 to intelligently validate and auto-correct:
- Armor Class calculations
- Inventory item categorization (prevents arrows as "miscellaneous", etc.)
- Equipment conflicts  
- Temporary effects (future)
- Stat bonuses (future)

INVENTORY VALIDATION SYSTEM:
Solves GitHub issue #45 - inconsistent ration storage format across characters.
Two-pronged approach:
1. PREVENTIVE: Enhanced AI prompts prevent future categorization errors
2. CORRECTIVE: AI validation fixes existing miscategorized items

The system uses the same deep merge strategy as the main character updater,
ensuring atomic file operations and preventing data corruption.

The AI reasons through the rules rather than following hardcoded logic,
making it flexible and adaptable to any character structure or edge case.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from config import OPENAI_API_KEY, CHARACTER_VALIDATOR_MODEL
from file_operations import safe_read_json, safe_write_json

class AICharacterValidator:
    def __init__(self):
        """Initialize AI-powered validator"""
        self.logger = logging.getLogger(__name__)
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.corrections_made = []
        
    def validate_and_correct_character(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-powered validation and correction of character data
        
        Args:
            character_data: Character JSON data
            
        Returns:
            AI-corrected character data with proper AC calculation
        """
        self.corrections_made = []
        
        # Use AI to validate and correct AC calculation
        corrected_data = self.ai_validate_armor_class(character_data)
        
        # Use AI to validate and correct inventory categorization
        corrected_data = self.ai_validate_inventory_categories(corrected_data)
        
        # Future: Add other AI validations here
        # - Temporary effects expiration  
        # - Attack bonus calculation
        # - Saving throw bonuses
        
        return corrected_data
    
    def ai_validate_armor_class(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to validate and correct Armor Class calculation
        
        Args:
            character_data: Character JSON data
            
        Returns:
            Character data with AI-corrected AC
        """
        
        validation_prompt = self.build_ac_validation_prompt(character_data)
        
        try:
            response = self.client.chat.completions.create(
                model=CHARACTER_VALIDATOR_MODEL,
                temperature=0.1,  # Low temperature for consistent validation
                messages=[
                    {"role": "system", "content": self.get_validator_system_prompt()},
                    {"role": "user", "content": validation_prompt}
                ]
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse AI response to get corrected character data
            corrected_data = self.parse_ai_validation_response(ai_response, character_data)
            
            return corrected_data
            
        except Exception as e:
            self.logger.error(f"AI validation failed: {str(e)}")
            return character_data
    
    def ai_validate_inventory_categories(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to validate and correct inventory item categorization
        Following the main character updater pattern: return only changes, use deep merge
        
        Args:
            character_data: Character JSON data
            
        Returns:
            Character data with AI-corrected inventory categories
        """
        
        max_attempts = 3
        attempt = 1
        
        while attempt <= max_attempts:
            try:
                validation_prompt = self.build_inventory_validation_prompt(character_data)
                
                response = self.client.chat.completions.create(
                    model=CHARACTER_VALIDATOR_MODEL,
                    temperature=0.1,  # Low temperature for consistent validation
                    messages=[
                        {"role": "system", "content": self.get_inventory_validator_system_prompt()},
                        {"role": "user", "content": validation_prompt}
                    ]
                    # No max_tokens - let AI return full response
                )
                
                ai_response = response.choices[0].message.content.strip()
                
                # Parse AI response to get inventory updates only
                inventory_updates = self.parse_inventory_validation_response(ai_response, character_data)
                
                if inventory_updates:
                    # Apply updates using deep merge (same pattern as main character updater)
                    from update_character_info import deep_merge_dict
                    corrected_data = deep_merge_dict(character_data, inventory_updates)
                    return corrected_data
                else:
                    # No changes needed
                    return character_data
                    
            except Exception as e:
                self.logger.error(f"AI inventory validation attempt {attempt} failed: {str(e)}")
                attempt += 1
                if attempt > max_attempts:
                    self.logger.error(f"All {max_attempts} inventory validation attempts failed")
                    return character_data
        
        return character_data
    
    def get_validator_system_prompt(self) -> str:
        """
        Comprehensive system prompt for AI character validation
        
        Returns:
            System prompt with 5th edition rules and examples
        """
        return """You are an expert character validator for the 5th edition of the world's most popular role playing game. Your job is to validate and correct character data to ensure it follows the rules accurately.

## PRIMARY TASK: ARMOR CLASS VALIDATION

You must validate that the character's Armor Class (AC) is calculated correctly based on their equipped items and apply corrections as needed.

## 5TH EDITION ARMOR CLASS RULES

### Base Armor AC Values:
**Light Armor** (AC = Base + Dex modifier, no limit):
- Padded: 11 AC
- Leather: 11 AC  
- Studded Leather: 12 AC

**Medium Armor** (AC = Base + Dex modifier, max +2):
- Hide: 12 AC
- Chain Shirt: 13 AC
- Scale Mail: 14 AC (stealth disadvantage)
- Breastplate: 14 AC
- Half Plate: 15 AC (stealth disadvantage)

**Heavy Armor** (AC = Base only, no Dex bonus):
- Ring Mail: 14 AC (stealth disadvantage)
- Chain Mail: 16 AC (stealth disadvantage)
- Splint: 17 AC (stealth disadvantage)  
- Plate: 18 AC (stealth disadvantage)

**Shields**: +2 AC when equipped

### AC Calculation Formula:
AC = Base Armor + Dex Modifier (limited by armor type) + Shield Bonus + Fighting Style Bonus + Other Bonuses

### Fighting Style Bonuses:
- **Defense**: +1 AC when wearing any armor
- All other fighting styles: No AC bonus

### Equipment Rules:
- Only ONE base armor piece can be equipped
- Only ONE shield can be equipped
- Multiple armor pieces of same type = conflict (keep highest AC)

## VALIDATION EXAMPLES

### Example 1: Fighter with Chain Mail and Shield
```json
Character Data:
{
  "armorClass": 15,
  "abilities": {"dexterity": 14},
  "classFeatures": [{"name": "Fighting Style: Defense"}],
  "equipment": [
    {"item_name": "Chain Mail", "item_type": "armor", "equipped": true},
    {"item_name": "Shield", "item_type": "armor", "equipped": true}
  ]
}

Calculation:
- Chain Mail: 16 AC (heavy armor, no Dex bonus)
- Shield: +2 AC  
- Defense Fighting Style: +1 AC (wearing armor)
- Correct AC: 16 + 0 + 2 + 1 = 19

Correction Needed: AC should be 19, not 15
```

### Example 2: Rogue with Studded Leather
```json
Character Data:
{
  "armorClass": 14,
  "abilities": {"dexterity": 16},
  "equipment": [
    {"item_name": "Studded Leather", "item_type": "armor", "equipped": true}
  ]
}

Calculation:
- Studded Leather: 12 AC (light armor)
- Dex Modifier: +3 (16 Dex, no limit for light armor)
- Correct AC: 12 + 3 = 15

Correction Needed: AC should be 15, not 14
```

### Example 3: Equipment Conflict Resolution
```json
Character Data:
{
  "equipment": [
    {"item_name": "Chain Mail", "item_type": "armor", "equipped": true},
    {"item_name": "Scale Mail", "item_type": "armor", "equipped": true}
  ]
}

Problem: Two base armor pieces equipped
Solution: Keep Chain Mail (16 AC), unequip Scale Mail (14 AC)
```

## RESPONSE FORMAT

You must respond with a JSON object containing:

```json
{
  "validated_character_data": {
    // Complete corrected character data with proper AC
  },
  "corrections_made": [
    "List of specific corrections made"
  ],
  "ac_calculation_breakdown": {
    "base_armor": "Name and AC value",
    "dex_modifier": "Value applied", 
    "shield_bonus": "Value applied",
    "fighting_style_bonus": "Value applied",
    "total_ac": "Final calculated AC"
  }
}
```

## INSTRUCTIONS

1. **Analyze the character data** to identify all equipped armor and relevant bonuses
2. **Auto-populate missing armor properties** using the reference table above
3. **Resolve equipment conflicts** per 5th edition rules
4. **Calculate correct AC** using the formula and rules
5. **Update character data** with corrections
6. **Provide detailed breakdown** of the calculation

Be thorough but concise. Focus on accuracy and rule compliance."""

    def build_ac_validation_prompt(self, character_data: Dict[str, Any]) -> str:
        """
        Build validation prompt with character data
        
        Args:
            character_data: Character JSON data
            
        Returns:
            Formatted prompt for AI validation
        """
        return f"""Please validate and correct the Armor Class calculation for this character:

```json
{json.dumps(character_data, indent=2)}
```

Analyze their equipment, abilities, and class features to determine the correct AC according to 5th edition rules. 

Pay special attention to:
1. Equipped armor and shields
2. Dexterity modifier and armor type limitations
3. Fighting style bonuses (especially Defense)
4. Equipment conflicts (multiple armor pieces)

Provide the corrected character data with proper AC calculation."""

    def parse_ai_validation_response(self, ai_response: str, original_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse AI response and extract corrected character data
        
        Args:
            ai_response: AI validation response
            original_data: Original character data
            
        Returns:
            Corrected character data
        """
        try:
            # Try to extract JSON from AI response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = ai_response[start_idx:end_idx]
                parsed_response = json.loads(json_str)
                
                # Extract corrected character data
                if 'validated_character_data' in parsed_response:
                    corrected_data = parsed_response['validated_character_data']
                    
                    # Log corrections made
                    if 'corrections_made' in parsed_response:
                        self.corrections_made = parsed_response['corrections_made']
                        for correction in self.corrections_made:
                            self.logger.info(f"AI Correction: {correction}")
                    
                    # Log AC breakdown
                    if 'ac_calculation_breakdown' in parsed_response:
                        breakdown = parsed_response['ac_calculation_breakdown']
                        self.logger.info(f"AC Breakdown: {breakdown}")
                    
                    return corrected_data
                
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse AI response: {str(e)}")
            self.logger.debug(f"AI Response was: {ai_response}")
        
        # Return original data if parsing fails
        return original_data
    
    def get_inventory_validator_system_prompt(self) -> str:
        """
        System prompt for AI inventory categorization validation
        
        Returns:
            System prompt with inventory categorization rules
        """
        return """You are an expert inventory categorization validator for the 5th edition of the world's most popular role playing game. Your job is to ensure all inventory items are correctly categorized according to standard item types.

## PRIMARY TASK: INVENTORY CATEGORIZATION VALIDATION

You must validate that each item in the character's inventory has the correct item_type based on its name and description.

### VALID ITEM TYPES (use these EXACTLY):
- "weapon" - swords, bows, daggers, melee and ranged weapons
- "armor" - armor pieces, shields, cloaks, boots, gloves, protective wear
- "ammunition" - arrows, bolts, sling bullets, thrown weapon ammo
- "consumable" - potions, scrolls, food, rations, anything consumed when used
- "equipment" - tools, torches, rope, containers, utility items
- "miscellaneous" - rings, amulets, wands, truly miscellaneous items only

### CATEGORIZATION RULES:
- Arrows, Bolts, Bullets -> "ammunition"
- Travel Ration, Food, Bread -> "consumable" 
- Torch, Rope, Tools, Containers -> "equipment"
- Potions, Scrolls -> "consumable"
- Rings, Amulets, Wands -> "miscellaneous"
- Any armor or protective gear -> "armor"
- Any weapon -> "weapon"

### OUTPUT FORMAT:
Return a JSON object with ONLY the changes needed:
{
  "corrections_made": ["list of corrections"],
  "equipment": [
    {
      "item_name": "exact item name",
      "item_type": "corrected_type"
    }
  ]
}

CRITICAL: Only return items that need their item_type corrected. Do NOT return items that are already correctly categorized. Do NOT return the complete character data - only the equipment items that need item_type fixes.
"""
    
    def build_inventory_validation_prompt(self, character_data: Dict[str, Any]) -> str:
        """
        Build validation prompt for inventory categorization
        
        Args:
            character_data: Character JSON data
            
        Returns:
            Formatted prompt for AI validation
        """
        equipment = character_data.get('equipment', [])
        
        prompt = f"""Please validate the inventory categorization for this character:

CHARACTER NAME: {character_data.get('name', 'Unknown')}

CURRENT INVENTORY:
"""
        
        for i, item in enumerate(equipment):
            item_name = item.get('item_name', 'Unknown Item')
            item_type = item.get('item_type', 'Unknown')
            description = item.get('description', 'No description')
            quantity = item.get('quantity', 1)
            
            prompt += f"""
Item #{i+1}:
- Name: {item_name}
- Current Type: {item_type}
- Description: {description}
- Quantity: {quantity}
"""
        
        prompt += """

Validate each item's categorization and correct any that are wrong. Focus especially on:
- Items currently marked as "miscellaneous" that should be other types
- Arrows/ammunition items
- Food/rations that should be "consumable"  
- Tools/torches that should be "equipment"

IMPORTANT: Return ONLY the items that need their item_type corrected. Do not include items that are already correctly categorized."""
        
        return prompt
    
    def parse_inventory_validation_response(self, ai_response: str, original_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse AI inventory validation response - returns only the updates/changes
        
        Args:
            ai_response: AI response string
            original_data: Original character data
            
        Returns:
            Dictionary with only the changes to apply (or empty dict if no changes)
        """
        try:
            # Try to extract JSON from AI response
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = ai_response[start_idx:end_idx]
                parsed_response = json.loads(json_str)
                
                # Check if there are any equipment updates
                if 'equipment' in parsed_response and parsed_response['equipment']:
                    # Log corrections made
                    if 'corrections_made' in parsed_response:
                        inventory_corrections = parsed_response['corrections_made']
                        for correction in inventory_corrections:
                            self.logger.info(f"AI Inventory Correction: {correction}")
                            self.corrections_made.append(f"Inventory: {correction}")
                    
                    # Return only the equipment updates
                    return {"equipment": parsed_response['equipment']}
                else:
                    # No corrections needed
                    self.logger.debug("No inventory corrections needed")
                    return {}
                
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse AI inventory response: {str(e)}")
            self.logger.debug(f"AI Response was: {ai_response}")
        
        # Return empty dict if parsing fails (no changes)
        return {}
    
    def validate_character_file_safe(self, file_path: str) -> tuple[Dict[str, Any], bool]:
        """
        Validate character file using atomic file operations
        
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
                    self.logger.info(f"Character file validated and corrected: {file_path}")
                    return corrected_data, True
                else:
                    self.logger.error(f"Failed to save corrected character data to {file_path}")
                    return character_data, False
            else:
                self.logger.debug(f"Character file validated - no corrections needed: {file_path}")
                return corrected_data, True
                
        except Exception as e:
            self.logger.error(f"Error validating character file {file_path}: {str(e)}")
            return {}, False


def validate_character_file(file_path: str) -> bool:
    """
    Convenience function to validate a character file using AI with atomic file operations
    
    Args:
        file_path: Path to character JSON file
        
    Returns:
        True if validation successful, False otherwise
    """
    try:
        # Load character data using safe file operations
        character_data = safe_read_json(file_path)
        if character_data is None:
            print(f"Error: Could not read character file {file_path}")
            return False
        
        # AI validation and correction
        validator = AICharacterValidator()
        corrected_data = validator.validate_and_correct_character(character_data)
        
        # Save if corrections were made using atomic file operations
        if validator.corrections_made:
            success = safe_write_json(file_path, corrected_data)
            if success:
                print(f"AI Corrections made: {validator.corrections_made}")
                return True
            else:
                print(f"Error: Failed to save corrected character data to {file_path}")
                return False
        else:
            print("No corrections needed - character data is valid")
            return True
        
    except Exception as e:
        print(f"Error validating character file {file_path}: {str(e)}")
        return False


if __name__ == "__main__":
    # Test with character file
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        validate_character_file(file_path)
    else:
        # Test with default character
        validate_character_file("modules/Keep_of_Doom/characters/norn.json")