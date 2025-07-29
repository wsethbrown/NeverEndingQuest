# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
Mythic Bastionland Knight Generator
Creates Knights using the 72 Knight types from Mythic Bastionland
"""

import json
import sys
import os
import re
import random

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from openai import OpenAI
from jsonschema import validate, ValidationError
from config import OPENAI_API_KEY, NPC_BUILDER_MODEL
from utils.module_path_manager import ModulePathManager
from utils.enhanced_logger import debug, info, warning, error, set_script_name

# Set script name for logging
set_script_name("knight_builder")

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

client = OpenAI(api_key=OPENAI_API_KEY)

# Import the mythic selectors for data-driven Knight selection
from utils.mythic_selectors import roll_knight, get_knight_by_name, list_all_knights

CAMPAIGN_STARTS = {
    "wanderer": {
        "description": "Young Knights-Errant with d6 Guard, 1d6 Vigour, 1d6 Clarity, 1d6 Spirit, modest equipment",
        "guard_dice": "1d6",
        "virtue_dice": {"vigour": "1d6", "clarity": "1d6", "spirit": "1d6"},
        "virtue_min": 2,
        "armour_max": 2,
        "glory": 0
    },
    "courtier": {
        "description": "Courtly Knights with d8 Guard, 2d6 Vigour, 2d6 Clarity, 2d6 Spirit, superior equipment",
        "guard_dice": "1d8", 
        "virtue_dice": {"vigour": "2d6", "clarity": "2d6", "spirit": "2d6"},
        "virtue_min": 7,
        "armour_max": 3,
        "glory": 0
    },
    "ruler": {
        "description": "Established rulers with d10 Guard, 3d6 Vigour, 3d6 Clarity, 3d6 Spirit, excellent equipment",
        "guard_dice": "1d10",
        "virtue_dice": {"vigour": "3d6", "clarity": "3d6", "spirit": "3d6"}, 
        "virtue_min": 7,
        "armour_max": 4,
        "glory": 3
    }
}

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
        with open(file_name, 'w') as file:
            json.dump(data, file, indent=2)
        info(f"SUCCESS: Knight save ({file_name}) - PASS", category="knight_creation")
        return True
    except Exception as e:
        print(f"{RED}Error saving to {file_name}: {str(e)}{RESET}")
        return False

def roll_dice(dice_notation):
    """Roll dice notation like '2d6' and return the result."""
    if 'd' not in dice_notation:
        return int(dice_notation)
    
    parts = dice_notation.split('d')
    num_dice = int(parts[0])
    die_size = int(parts[1])
    
    return sum(random.randint(1, die_size) for _ in range(num_dice))

def generate_knight_stats(campaign_start):
    """Generate Knight stats based on campaign start type."""
    start_data = CAMPAIGN_STARTS[campaign_start]
    
    # Roll Guard
    guard = roll_dice(start_data["guard_dice"])
    
    # Roll Virtues
    vigour = max(roll_dice(start_data["virtue_dice"]["vigour"]), start_data["virtue_min"])
    clarity = max(roll_dice(start_data["virtue_dice"]["clarity"]), start_data["virtue_min"])
    spirit = max(roll_dice(start_data["virtue_dice"]["spirit"]), start_data["virtue_min"])
    
    # Roll Armour (0 to max for start type)
    armour = random.randint(0, start_data["armour_max"])
    
    return {
        "guard": guard,
        "virtues": {
            "vigour": vigour,
            "clarity": clarity,
            "spirit": spirit
        },
        "armour": armour,
        "glory": start_data["glory"]
    }

def generate_knight(knight_name, schema, knight_type=None, campaign_start="wanderer"):
    """Generate a Knight using data-driven approach with Mythic Bastionland rules."""
    
    # Get Knight data from the official list
    if knight_type:
        # Try to find exact match by name
        knight_data_ref = get_knight_by_name(knight_type)
        if not knight_data_ref:
            print(f"{YELLOW}Warning: Knight type '{knight_type}' not found, rolling random Knight{RESET}")
            knight_data_ref = roll_knight()
    else:
        # Roll random Knight
        knight_data_ref = roll_knight()
    
    if not knight_data_ref:
        print(f"{RED}Error: Could not select a Knight type{RESET}")
        return None
    
    selected_knight_type = knight_data_ref["name"]
    knight_details = knight_data_ref["data"]
    
    # Generate base stats
    stats = generate_knight_stats(campaign_start)
    
    # Create Knight character data using the schema
    knight_data = {
        "name": knight_name,
        "knight_type": selected_knight_type,
        "campaign_start": campaign_start,
        "guard": stats["guard"],
        "virtues": stats["virtues"],
        "armour": stats["armour"],
        "glory": stats["glory"],
        "rank": "Knight-Errant" if stats["glory"] < 3 else "Knight-Gallant",
        "scars": [],
        "feats": ["Smite", "Focus", "Deny"],  # All Knights know the Three Feats
        "property": knight_details.get("property", ""),
        "ability": knight_details.get("ability", ""),
        "passion": knight_details.get("passion", ""),
        "seer": knight_details.get("seer", ""),
        "background": f"A {selected_knight_type} who began their journey as a {campaign_start}.",
        "equipment": generate_starting_equipment(campaign_start),
        "notes": []
    }
    
    try:
        validate(instance=knight_data, schema=schema)
        return knight_data
    except ValidationError as e:
        print(f"{RED}Error: Generated Knight data does not match schema. {str(e)}{RESET}")
        print(f"{YELLOW}Knight data:{RESET}\n{json.dumps(knight_data, indent=2)}")
        return None

def generate_starting_equipment(campaign_start):
    """Generate appropriate starting equipment based on campaign start."""
    base_equipment = [
        "Sword or preferred weapon",
        "Basic travelling gear",
        "Modest provisions"
    ]
    
    if campaign_start == "wanderer":
        return base_equipment + ["Simple travelling clothes"]
    elif campaign_start == "courtier":
        return base_equipment + ["Fine clothes", "Courtly accessories", "Better provisions"]
    elif campaign_start == "ruler":
        return base_equipment + ["Ornate garments", "Symbols of authority", "Excellent provisions", "Retinue"]
    
    return base_equipment

def main():
    if len(sys.argv) < 2:
        print(f"{RED}Usage: python knight_builder.py <knight_name> [knight_type] [campaign_start]{RESET}")
        print(f"{YELLOW}Campaign starts: wanderer, courtier, ruler{RESET}")
        print(f"{YELLOW}Example Knight types: {', '.join(KNIGHT_TYPES[:5])}...{RESET}")
        sys.exit(1)

    knight_name = sys.argv[1]
    knight_type = sys.argv[2] if len(sys.argv) > 2 else None
    campaign_start = sys.argv[3] if len(sys.argv) > 3 else "wanderer"
    
    if campaign_start not in CAMPAIGN_STARTS:
        print(f"{RED}Error: Invalid campaign start. Use: wanderer, courtier, or ruler{RESET}")
        sys.exit(1)

    debug(f"INPUT_PROCESSING: Name: {knight_name}, Type: {knight_type}, Start: {campaign_start}", category="knight_creation")

    # Load Mythic Bastionland character schema
    knight_schema = load_schema("schemas/char_schema_mythic.json")
    if not knight_schema:
        sys.exit(1)

    generated_knight = generate_knight(knight_name, knight_schema, knight_type, campaign_start)
    if generated_knight:
        # Get current module for path resolution
        try:
            from utils.encoding_utils import safe_json_load
            party_tracker = safe_json_load("party_tracker.json")
            current_module = party_tracker.get("module", "").replace(" ", "_") if party_tracker else None
            path_manager = ModulePathManager(current_module)
        except:
            path_manager = ModulePathManager()
        
        clean_name = generated_knight.get("name", knight_name)
        full_path = path_manager.get_character_unified_path(clean_name)
        
        # Ensure directory exists
        characters_dir = os.path.dirname(full_path)
        os.makedirs(characters_dir, exist_ok=True)
        
        if save_json(full_path, generated_knight):
            print(f"{GREEN}Successfully created {generated_knight.get('knight_type', 'Knight')} '{clean_name}'!{RESET}")
            info(f"SUCCESS: Knight creation ({clean_name}) - PASS", category="knight_creation")
        else:
            error(f"FAILURE: Knight save ({clean_name}) - FAIL", category="knight_creation")
            sys.exit(1)
    else:
        error(f"FAILURE: Knight creation ({knight_name}) - FAIL", category="knight_creation")
        sys.exit(1)

if __name__ == "__main__":
    main()