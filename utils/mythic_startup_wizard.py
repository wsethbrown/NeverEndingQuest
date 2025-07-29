#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
Mythic Bastionland Character Creation & Module Selection Startup Wizard

Handles first-time setup when no player character or module is configured.
Provides AI-powered Knight character creation and module selection for Mythic Bastionland.

Uses module-centric architecture for self-contained adventures.
Follows Mythic Bastionland rules for character creation, including:
- Three Virtues system (VIG/CLA/SPI)
- Campaign start types (Wanderer/Courtier/Ruler)
- Knight archetype selection from mythic_knights.json
- Glory and rank progression system
- Barter-based trade system (no coins)
"""

import json
import os
import random
import shutil
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from jsonschema import validate, ValidationError
from core.generators.module_stitcher import ModuleStitcher

import config
from utils.encoding_utils import safe_json_load, safe_json_dump
from utils.module_path_manager import ModulePathManager
from utils.enhanced_logger import debug, info, warning, error, set_script_name
from core.managers.status_manager import (
    status_manager, status_processing_ai, status_validating,
    status_loading, status_ready, status_saving
)

# Set script name for logging
set_script_name("mythic_startup_wizard")

# Color constants for status display
GOLD = "\033[38;2;255;215;0m"  # Gold color for status messages
RESET_COLOR = "\033[0m"

# Status display configuration
current_status_line = None
web_mode = False

# Check if we're running in web mode by looking for the web output capture
try:
    import sys
    if hasattr(sys.stdout, '__class__') and 'WebOutputCapture' in str(sys.stdout.__class__):
        web_mode = True
except:
    web_mode = False

class MythicStartupWizard:
    """Handles Mythic Bastionland character creation and module setup"""
    
    def __init__(self):
        """Initialize the Mythic Bastionland startup wizard"""
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.status_manager = status_manager
        
        # Load mythic data
        self.knights_data = safe_json_load('data/mythic_knights.json')
        self.myths_data = safe_json_load('data/mythic_myths.json')
        
        if not self.knights_data or not self.myths_data:
            error("Failed to load mythic data files", category="startup")
            raise RuntimeError("Missing mythic data files")
    
    def print_status(self, message: str, web_safe: bool = False):
        """Print status message with appropriate formatting"""
        global current_status_line
        
        if web_mode or web_safe:
            # In web mode, just print the message
            print(f"Status: {message}")
        else:
            # Clear previous line and print new status
            if current_status_line:
                print("\r" + " " * len(current_status_line) + "\r", end="")
            
            formatted_message = f"{GOLD}{message}{RESET_COLOR}"
            print(formatted_message, end="", flush=True)
            current_status_line = message
    
    def clear_status(self):
        """Clear the current status line"""
        global current_status_line
        
        if not web_mode and current_status_line:
            print("\r" + " " * len(current_status_line) + "\r", end="")
            current_status_line = None
    
    def roll_dice(self, dice_string: str) -> int:
        """Roll dice according to Mythic Bastionland notation (e.g., 'd12+6', '2d6')"""
        dice_string = dice_string.lower().strip()
        
        if dice_string == 'd6':
            return random.randint(1, 6)
        elif dice_string == 'd12':
            return random.randint(1, 12)
        elif dice_string == 'd12+6':
            return random.randint(1, 12) + 6
        elif dice_string == 'd12+d6':
            return random.randint(1, 12) + random.randint(1, 6)
        elif dice_string == '2d6':
            return random.randint(1, 6) + random.randint(1, 6)
        elif dice_string == 'd6+6':
            return random.randint(1, 6) + 6
        else:
            # Default to d6 if format not recognized
            return random.randint(1, 6)
    
    def generate_virtues(self, campaign_start: str) -> dict:
        """Generate Virtues based on campaign start type"""
        virtues = {}
        
        if campaign_start == "wanderer":
            # Wanderer: d12+d6 for each Virtue
            virtues["vigour"] = self.roll_dice("d12+d6")
            virtues["clarity"] = self.roll_dice("d12+d6") 
            virtues["spirit"] = self.roll_dice("d12+d6")
        elif campaign_start == "courtier":
            # Courtier: d12+6 for each Virtue
            virtues["vigour"] = self.roll_dice("d12+6")
            virtues["clarity"] = self.roll_dice("d12+6")
            virtues["spirit"] = self.roll_dice("d12+6")
        elif campaign_start == "ruler":
            # Ruler: d12+6 for each Virtue
            virtues["vigour"] = self.roll_dice("d12+6")
            virtues["clarity"] = self.roll_dice("d12+6")
            virtues["spirit"] = self.roll_dice("d12+6")
        else:
            # Default to wanderer
            virtues["vigour"] = self.roll_dice("d12+d6")
            virtues["clarity"] = self.roll_dice("d12+d6")
            virtues["spirit"] = self.roll_dice("d12+d6")
        
        return virtues
    
    def generate_guard(self, campaign_start: str) -> int:
        """Generate Guard based on campaign start type"""
        if campaign_start == "wanderer":
            return self.roll_dice("d6")
        elif campaign_start == "courtier":
            return self.roll_dice("2d6")
        elif campaign_start == "ruler":
            return self.roll_dice("d6+6")
        else:
            return self.roll_dice("d6")
    
    def select_random_knight(self) -> dict:
        """Select a random knight archetype from mythic_knights.json"""
        if not self.knights_data or 'knights' not in self.knights_data:
            error("No knights data available", category="startup")
            return None
        
        knights = list(self.knights_data['knights'].values())
        return random.choice(knights)
    
    def create_starting_equipment(self, knight_data: dict) -> list:
        """Create starting equipment based on knight properties"""
        equipment = []
        
        # Add knight property items
        knight_property = knight_data.get('property', '')
        if knight_property:
            # Parse the property string to extract equipment
            # This is a simplified parser - in practice you'd want more sophisticated parsing
            items = []
            if 'sword' in knight_property.lower():
                items.append({"name": "Sword", "type": "weapon", "damage": "d8", "equipped": True})
            if 'bow' in knight_property.lower():
                items.append({"name": "Bow", "type": "weapon", "damage": "d6", "restrictions": ["long"], "equipped": False})
            if 'mail' in knight_property.lower():
                items.append({"name": "Chain Mail", "type": "armour", "armour": 2, "equipped": True})
            if 'shield' in knight_property.lower():
                items.append({"name": "Shield", "type": "armour", "armour": 1, "equipped": True})
            
            # Add basic adventuring gear
            basic_gear = [
                {"name": "Torch", "type": "tool", "rarity": "common"},
                {"name": "Rope (50 feet)", "type": "tool", "rarity": "common"},
                {"name": "Rations", "type": "remedy", "rarity": "common"},
                {"name": "Water skin", "type": "tool", "rarity": "common"},
                {"name": "Flint and steel", "type": "tool", "rarity": "common"}
            ]
            
            equipment.extend(items)
            equipment.extend(basic_gear)
        
        return equipment
    
    def create_mythic_character(self, character_name: str, campaign_start: str) -> dict:
        """Create a complete Mythic Bastionland character"""
        self.print_status("Rolling dice for Virtues and Guard...")
        
        # Generate basic stats
        virtues = self.generate_virtues(campaign_start)
        guard = self.generate_guard(campaign_start)
        
        # Select knight archetype
        knight_data = self.select_random_knight()
        if not knight_data:
            error("Failed to select knight archetype", category="startup")
            return None
        
        knight_name = knight_data.get('name', 'Unknown Knight')
        
        # Create character structure following mythic schema
        character = {
            "character_role": "player",
            "name": character_name,
            "campaign_start": campaign_start,
            "knight_type": knight_name,
            "rank": "Knight-Errant",  # Starting rank
            "glory": 0,  # Starting glory
            "virtues": virtues,
            "guard": guard,
            "status": "alive",
            "conditions": [],
            "scars": [],
            "feats": ["Smite", "Focus", "Deny"],  # All Knights know these
            "knight_property": {
                "items": knight_data.get('property', '').split(', ') if knight_data.get('property') else [],
                "ability": knight_data.get('ability', ''),
                "passion": knight_data.get('passion', '')
            },
            "equipment": self.create_starting_equipment(knight_data),
            "remedies": {
                "sustenance": 3,  # Starting remedies
                "stimulant": 3,
                "sacrament": 3
            },
            "age_category": "mature",  # Default starting age
            "personality_traits": "",
            "ideals": "",
            "bonds": "",
            "flaws": ""
        }
        
        return character
    
    def ai_enhance_character(self, character: dict) -> dict:
        """Use AI to enhance character with personality and background"""
        self.print_status("Enhancing character with AI...")
        
        prompt = f"""You are helping create a character for Mythic Bastionland. 

CHARACTER: {character['name']}, a {character['knight_type']}
CAMPAIGN START: {character['campaign_start'].title()}
VIRTUES: VIG {character['virtues']['vigour']}, CLA {character['virtues']['clarity']}, SPI {character['virtues']['spirit']}
GUARD: {character['guard']}

KNIGHT ABILITY: {character['knight_property']['ability']}
KNIGHT PASSION: {character['knight_property']['passion']}

Please provide brief, evocative descriptions for:
1. Personality traits (1-2 sentences)
2. Ideals (what drives them)
3. Bonds (connections to people/places)
4. Flaws (interesting weaknesses)

Keep it concise and atmospheric, fitting the Mythic Bastionland setting.

Respond in JSON format:
{{
  "personality_traits": "...",
  "ideals": "...", 
  "bonds": "...",
  "flaws": "..."
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=config.ENHANCED_MODEL,
                temperature=0.8,
                messages=[
                    {"role": "system", "content": "You are a creative assistant helping develop Mythic Bastionland characters. Provide brief, evocative descriptions that fit the setting."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                # Extract JSON from response
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = ai_response[start_idx:end_idx]
                    enhancements = json.loads(json_str)
                    
                    # Update character with AI enhancements
                    character.update(enhancements)
                    
            except json.JSONDecodeError:
                warning("Failed to parse AI character enhancement", category="startup")
                
        except Exception as e:
            warning(f"AI character enhancement failed: {str(e)}", category="startup")
        
        return character
    
    def validate_character(self, character: dict) -> bool:
        """Validate character against mythic schema"""
        try:
            schema_data = safe_json_load('schemas/char_schema_mythic.json')
            if schema_data:
                validate(character, schema_data)
                return True
        except ValidationError as e:
            error(f"Character validation failed: {str(e)}", category="startup")
            return False
        except Exception as e:
            error(f"Schema loading failed: {str(e)}", category="startup")
            return False
        
        return True
    
    def run_character_creation(self) -> dict:
        """Run the complete character creation process"""
        self.clear_status()
        print("\n" + "="*60)
        print("      MYTHIC BASTIONLAND CHARACTER CREATION")
        print("="*60)
        print()
        
        # Get character name
        character_name = input("Enter your Knight's name: ").strip()
        if not character_name:
            character_name = "Sir Adventurer"
        
        print()
        print("Campaign Start Types:")
        print("1. Wanderer - You have seen strange sights (d6 GD, d12+d6 Virtues)")
        print("2. Courtier - You have walked in high places (2d6 GD, d12+6 Virtues)")  
        print("3. Ruler - You have held power (d6+6 GD, d12+6 Virtues)")
        print()
        
        while True:
            choice = input("Choose your campaign start (1-3): ").strip()
            if choice == "1":
                campaign_start = "wanderer"
                break
            elif choice == "2":
                campaign_start = "courtier"
                break
            elif choice == "3":
                campaign_start = "ruler"
                break
            else:
                print("Please choose 1, 2, or 3.")
        
        print()
        self.print_status("Creating your Knight...")
        
        # Create character
        character = self.create_mythic_character(character_name, campaign_start)
        if not character:
            error("Failed to create character", category="startup")
            return None
        
        # AI enhancement
        character = self.ai_enhance_character(character)
        
        # Validate character
        self.print_status("Validating character data...")
        if not self.validate_character(character):
            error("Character validation failed", category="startup")
            return None
        
        self.clear_status()
        print("\n" + "="*60)
        print("           CHARACTER CREATED SUCCESSFULLY")
        print("="*60)
        print(f"Name: {character['name']}")
        print(f"Knight Type: {character['knight_type']}")
        print(f"Campaign Start: {character['campaign_start'].title()}")
        print(f"Rank: {character['rank']} (Glory: {character['glory']})")
        print()
        print("VIRTUES:")
        print(f"  Vigour:  {character['virtues']['vigour']}")
        print(f"  Clarity: {character['virtues']['clarity']}")
        print(f"  Spirit:  {character['virtues']['spirit']}")
        print(f"  Guard:   {character['guard']}")
        print()
        print(f"Knight Ability: {character['knight_property']['ability']}")
        print(f"Knight Passion: {character['knight_property']['passion']}")  
        print()
        
        return character
    
    def save_character(self, character: dict, module_name: str) -> bool:
        """Save character to module directory"""
        try:
            path_manager = ModulePathManager()
            character_dir = path_manager.get_characters_dir(module_name)
            
            # Ensure character directory exists
            os.makedirs(character_dir, exist_ok=True)
            
            # Save character file
            character_file = os.path.join(character_dir, f"{character['name'].lower().replace(' ', '_')}.json")
            
            success = safe_json_dump(character, character_file)
            if success:
                info(f"Character saved to {character_file}", category="startup")
                return True
            else:
                error(f"Failed to save character to {character_file}", category="startup")
                return False
                
        except Exception as e:
            error(f"Error saving character: {str(e)}", category="startup")
            return False

def run_mythic_startup_wizard() -> tuple[dict, str]:
    """
    Run the complete Mythic Bastionland startup wizard
    
    Returns:
        Tuple of (character_data, module_name) or (None, None) if failed
    """
    try:
        wizard = MythicStartupWizard()
        
        # Create character
        character = wizard.run_character_creation()
        if not character:
            return None, None
        
        # For now, create a default module name
        # In the future, this could be expanded to let users choose or create modules
        module_name = "mythic_adventure"
        
        # Save character
        if wizard.save_character(character, module_name):
            return character, module_name
        else:
            return None, None
            
    except Exception as e:
        error(f"Startup wizard failed: {str(e)}", category="startup")
        return None, None

# ===== COMPATIBILITY FUNCTIONS FOR MAIN.PY =====

def initialize_game_files_from_bu():
    """Initialize game files from BU templates if they don't exist"""
    initialized_count = 0
    
    # Find all BU files in modules directory
    for bu_file in Path("modules").rglob("*_BU.json"):
        # Skip files in saved_games directories
        if "saved_games" in str(bu_file):
            continue
            
        # Determine the corresponding live file name
        live_file = str(bu_file).replace("_BU.json", ".json")
        
        # Only copy if the live file doesn't exist
        if not os.path.exists(live_file):
            try:
                shutil.copy2(bu_file, live_file)
                initialized_count += 1
            except Exception as e:
                warning(f"Failed to initialize {live_file}: {e}", category="startup")
    
    return initialized_count

def startup_required(party_file="party_tracker.json"):
    """Check if player character or module is missing"""
    try:
        party_data = safe_json_load(party_file)
        if not party_data:
            return True
        
        # Check if module is missing or empty
        module = party_data.get("module", "").strip()
        if not module:
            return True
        
        # Check if partyMembers is missing or empty
        party_members = party_data.get("partyMembers", [])
        if not party_members:
            return True
        
        # Check if the player character file actually exists
        if party_members:
            player_name = party_members[0]
            path_manager = ModulePathManager(module)
            char_path = path_manager.get_character_unified_path(player_name)
            if not os.path.exists(char_path):
                return True
        
        return False
        
    except Exception:
        return True  # If anything fails, assume setup needed

def run_startup_sequence():
    """Main entry point for startup wizard - Mythic Bastionland version"""
    print("\nDungeon Master: Welcome to your Mythic Bastionland Adventure!")
    print("Dungeon Master: Let's create your Knight and choose your quest...\n")
    
    # Initialize game files from BU templates first
    initialize_game_files_from_bu()
    
    try:
        # Run the mythic startup wizard
        character, module_name = run_mythic_startup_wizard()
        
        if not character or not module_name:
            print("Setup cancelled. Exiting...")
            return False
        
        print(f"\nDungeon Master: Setup complete! Welcome, {character.get('name', 'Knight')}!")
        print(f"Dungeon Master: Your quest for Glory begins now...\n")
        
        return True
        
    except Exception as e:
        print(f"Error: Error during setup: {e}")
        return False

if __name__ == "__main__":
    # Test the wizard
    character, module = run_mythic_startup_wizard()
    if character:
        print(f"\nCharacter creation successful! Module: {module}")
    else:
        print("\nCharacter creation failed!")