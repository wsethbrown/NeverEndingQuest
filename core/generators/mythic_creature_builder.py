# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
Mythic Bastionland Creature Builder
Creates creatures using Mythic Bastionland mechanics: Guard, Vigour, and special abilities.
"""

# ============================================================================
# MYTHIC_CREATURE_BUILDER.PY - CONTENT GENERATION LAYER - CREATURES
# ============================================================================
# 
# ARCHITECTURE ROLE: Content Generation Layer - AI-Powered Creature Creation
# 
# This module implements creature creation for Mythic Bastionland, using
# AI-powered generation with Guard/Vigour system instead of D&D mechanics.
# 
# KEY RESPONSIBILITIES:
# - Generate Mythic Bastionland compliant creatures using AI
# - Use Guard system instead of AC/HP
# - Implement special abilities appropriate to the setting
# - Handle AI response parsing and cleanup
# - Save generated creatures to module-specific directories
# 
# MYTHIC BASTIONLAND CREATURE DESIGN:
# - Guard: Replaces AC and HP as single defensive stat
# - Vigour: Used for some creatures with extended endurance
# - Special Abilities: Unique powers that create tactical challenges
# - No Challenge Rating: Creatures balanced through Guard and abilities
# 
# CREATURE CATEGORIES:
# - Beasts: Natural animals and creatures
# - Constructs: Mechanical or magical automatons  
# - Horrors: Twisted abominations and nightmares
# - Undead: Restless spirits and animated corpses
# - Humanoids: People, cultists, and intelligent beings
# 
# This module creates creatures that fit the Mythic Bastionland aesthetic
# while maintaining tactical challenge through interesting abilities.
# ============================================================================

import json
import sys
import os
import re

# Add the project root to the Python path so we can import from utils, core, etc.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from openai import OpenAI
from jsonschema import validate, ValidationError
import config
from utils.module_path_manager import ModulePathManager
from utils.enhanced_logger import debug, info, warning, error, set_script_name

# Set script name for logging
set_script_name("mythic_creature_builder")

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

# Use OPENAI_API_KEY from config
client = OpenAI(api_key=config.OPENAI_API_KEY)

def load_schema(file_name):
    try:
        with open(file_name, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"{RED}Error: File {file_name} not found.{RESET}")
        return None
    except json.JSONDecodeError:
        print(f"{RED}Error: Invalid JSON in {file_name}.{RESET}")
        return None

def save_json(file_name, data):
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_name)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            print(f"{YELLOW}Created directory: {directory}{RESET}")
        
        with open(file_name, 'w') as file:
            json.dump(data, file, indent=2)
        info(f"SUCCESS: Creature save ({file_name}) - PASS", category="creature_creation")
        return True
    except Exception as e:
        print(f"{RED}Error saving to {file_name}: {str(e)}{RESET}")
        return False

def generate_creature(creature_name, glory_level=0):
    """Generate a Mythic Bastionland creature using AI"""
    
    # Build context-aware system prompt for Mythic Bastionland
    system_content = """You are an assistant that creates creature JSON files for Mythic Bastionland. Given a creature name, create a JSON representation using Mythic Bastionland mechanics.

MYTHIC BASTIONLAND CREATURE RULES:
- Guard: Single defensive stat (typically 1-15, higher = tougher)
- Vigour: Optional endurance stat for some creatures
- No AC, HP, or Challenge Rating from D&D
- Special abilities create tactical challenges
- Damage is typically d6 unless specified

GUARD GUIDELINES BY GLORY LEVEL:
- Glory 0-2: Guard 1-5 (weak creatures)
- Glory 3-5: Guard 6-10 (moderate threats) 
- Glory 6-8: Guard 11-15 (dangerous foes)
- Glory 9+: Guard 16+ (legendary threats)

CREATURE TYPES:
- Beast: Natural animals and creatures
- Construct: Mechanical or magical automatons
- Horror: Twisted abominations and nightmares
- Undead: Restless spirits and animated corpses
- Humanoid: People, cultists, and intelligent beings

SPECIAL ABILITIES (examples):
- Blast: Attacks affect multiple targets
- Critical Damage: Extra effect on max damage
- Detachment: Can split into smaller creatures
- Flight: Can fly and attack from above
- Regeneration: Heals over time
- Camouflage: Hard to spot until attacking

NAMING CONVENTIONS:
- Use singular names (e.g., "Wolf", "Cultist", "Wraith")
- For multiple creatures, the system will handle naming
- Keep names evocative and fitting to Mythic Bastionland's tone

Return only valid JSON matching this schema:
{
  "name": "string",
  "type": "string", 
  "guard": number,
  "vigour": number (optional),
  "attack": "string (damage die and description)",
  "specialAbilities": ["array of abilities"],
  "description": "string",
  "notes": "string (tactical notes for GMs)"
}

Do not include D&D mechanics like AC, HP, CR, ability scores, or spell slots."""

    # Build user prompt
    user_content = f"""Create a creature named '{creature_name}' for Mythic Bastionland.

Glory Level Context: {glory_level} (affects appropriate Guard level)

Make this creature interesting and tactically challenging through special abilities rather than just high numbers. Consider what makes this creature unique in combat and exploration."""

    try:
        response = client.chat.completions.create(
            model=config.DM_MAIN_MODEL,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7  # Balanced creativity
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Clean up response - remove markdown formatting if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        try:
            creature_data = json.loads(response_text)
            
            # Ensure required fields
            if not all(key in creature_data for key in ["name", "type", "guard", "attack", "description"]):
                raise ValueError("Missing required fields")
            
            # Set defaults for optional fields
            if "specialAbilities" not in creature_data:
                creature_data["specialAbilities"] = []
            if "notes" not in creature_data:
                creature_data["notes"] = "Standard creature tactics apply."
            
            print(f"{GREEN}Successfully generated creature: {creature_data['name']}{RESET}")
            print(f"Type: {creature_data['type']}, Guard: {creature_data['guard']}")
            
            return creature_data
            
        except json.JSONDecodeError as e:
            print(f"{RED}Error parsing AI response as JSON: {e}{RESET}")
            print(f"Response was: {response_text}")
            return None
            
    except Exception as e:
        print(f"{RED}Error generating creature: {str(e)}{RESET}")
        return None

def create_fallback_creature(creature_name, glory_level=0):
    """Create a basic fallback creature if AI generation fails"""
    
    # Determine appropriate guard based on glory level
    if glory_level <= 2:
        guard = 3
    elif glory_level <= 5:
        guard = 8
    elif glory_level <= 8:
        guard = 12
    else:
        guard = 16
    
    creature_data = {
        "name": creature_name,
        "type": "Beast",
        "guard": guard,
        "attack": "d6 (bite/claw)",
        "specialAbilities": [],
        "description": f"A {creature_name.lower()} encountered in the realm.",
        "notes": "Basic creature with standard tactics."
    }
    
    print(f"{YELLOW}Using fallback creature generation for: {creature_name}{RESET}")
    return creature_data

def main():
    if len(sys.argv) < 2:
        print("Usage: python mythic_creature_builder.py <creature_name> [glory_level]")
        return
    
    creature_name = sys.argv[1]
    glory_level = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    print(f"Generating Mythic Bastionland creature: {creature_name}")
    print(f"Glory level context: {glory_level}")
    
    # Generate creature using AI
    creature_data = generate_creature(creature_name, glory_level)
    
    # Fallback if AI generation fails
    if not creature_data:
        print(f"{YELLOW}AI generation failed, using fallback{RESET}")
        creature_data = create_fallback_creature(creature_name, glory_level)
    
    # Save creature to file
    if creature_data:
        # Use ModulePathManager for consistent file paths
        path_manager = ModulePathManager()
        creature_file = path_manager.get_monster_path(creature_name)
        
        if save_json(creature_file, creature_data):
            print(f"{GREEN}Creature saved successfully: {creature_file}{RESET}")
        else:
            print(f"{RED}Failed to save creature{RESET}")
    else:
        print(f"{RED}Failed to generate creature data{RESET}")

if __name__ == "__main__":
    main()