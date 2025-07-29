# SPDX-FileCopyrightText: 2024 MoonlightByte
# SPDX-License-Identifier: Fair-Source-1.0
# License: See LICENSE file in the repository root
# This software is subject to the terms of the Fair Source License.

"""
Mythic Bastionland Knight and Myth Selectors
Simple utilities to select Knights and Myths from the comprehensive data files
"""

import json
import random
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.enhanced_logger import debug, info, warning, error, set_script_name

# Set script name for logging
set_script_name("mythic_selectors")

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

def load_knights_data():
    """Load the Knights data from JSON file."""
    try:
        with open("data/mythic_knights.json", 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        error("Knights data file not found: data/mythic_knights.json")
        return None
    except json.JSONDecodeError as e:
        error(f"Invalid JSON in Knights data file: {e}")
        return None

def load_myths_data():
    """Load the Myths data from JSON file."""
    try:
        with open("data/mythic_myths.json", 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        error("Myths data file not found: data/mythic_myths.json")
        return None
    except json.JSONDecodeError as e:
        error(f"Invalid JSON in Myths data file: {e}")
        return None

def load_generators_data():
    """Load the generator data from JSON file."""
    try:
        with open("data/mythic_generators.json", 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        error("Generator data file not found: data/mythic_generators.json")
        return None
    except json.JSONDecodeError as e:
        error(f"Invalid JSON in generator data file: {e}")
        return None

def roll_knight():
    """Roll d6 and d12 to randomly select a Knight."""
    d6_roll = random.randint(1, 6)
    d12_roll = random.randint(1, 12)
    return get_knight_by_dice(d6_roll, d12_roll)

def roll_myth():
    """Roll d6 and d12 to randomly select a Myth."""
    d6_roll = random.randint(1, 6)
    d12_roll = random.randint(1, 12)
    return get_myth_by_dice(d6_roll, d12_roll)

def get_knight_by_dice(d6, d12):
    """Get a specific Knight by d6 and d12 values."""
    knights_data = load_knights_data()
    if not knights_data:
        return None
    
    for knight_name, knight_info in knights_data["knights"].items():
        if knight_info["d6"] == d6 and knight_info["d12"] == d12:
            return {
                "name": knight_name,
                "d6": d6,
                "d12": d12,
                "data": knight_info
            }
    
    error(f"No Knight found for d6={d6}, d12={d12}")
    return None

def get_myth_by_dice(d6, d12):
    """Get a specific Myth by d6 and d12 values."""
    myths_data = load_myths_data()
    if not myths_data:
        return None
    
    for myth_name, myth_info in myths_data["myths"].items():
        if myth_info["d6"] == d6 and myth_info["d12"] == d12:
            return {
                "name": myth_name,
                "d6": d6,
                "d12": d12,
                "data": myth_info
            }
    
    error(f"No Myth found for d6={d6}, d12={d12}")
    return None

def get_knight_by_name(name):
    """Get a Knight by exact name match."""
    knights_data = load_knights_data()
    if not knights_data:
        return None
    
    knight_info = knights_data["knights"].get(name)
    if knight_info:
        return {
            "name": name,
            "d6": knight_info["d6"],
            "d12": knight_info["d12"],
            "data": knight_info
        }
    
    error(f"Knight '{name}' not found")
    return None

def get_myth_by_name(name):
    """Get a Myth by exact name match."""
    myths_data = load_myths_data()
    if not myths_data:
        return None
    
    myth_info = myths_data["myths"].get(name)
    if myth_info:
        return {
            "name": name,
            "d6": myth_info["d6"],
            "d12": myth_info["d12"],
            "data": myth_info
        }
    
    error(f"Myth '{name}' not found")
    return None

def list_all_knights():
    """Get a list of all Knight names."""
    knights_data = load_knights_data()
    if not knights_data:
        return []
    
    return sorted(knights_data["knights"].keys())

def list_all_myths():
    """Get a list of all Myth names."""
    myths_data = load_myths_data()
    if not myths_data:
        return []
    
    return sorted(myths_data["myths"].keys())

def get_knights_by_d6(d6):
    """Get all Knights for a specific d6 value."""
    knights_data = load_knights_data()
    if not knights_data:
        return []
    
    result = []
    for knight_name, knight_info in knights_data["knights"].items():
        if knight_info["d6"] == d6:
            result.append({
                "name": knight_name,
                "d6": d6,
                "d12": knight_info["d12"],
                "data": knight_info
            })
    
    return sorted(result, key=lambda x: x["d12"])

def get_myths_by_d6(d6):
    """Get all Myths for a specific d6 value."""
    myths_data = load_myths_data()
    if not myths_data:
        return []
    
    result = []
    for myth_name, myth_info in myths_data["myths"].items():
        if myth_info["d6"] == d6:
            result.append({
                "name": myth_name,
                "d6": d6,
                "d12": myth_info["d12"],
                "data": myth_info
            })
    
    return sorted(result, key=lambda x: x["d12"])

def print_knight_info(knight):
    """Pretty print Knight information."""
    if not knight:
        print(f"{RED}No Knight data to display{RESET}")
        return
    
    print(f"{GREEN}Knight: {knight['name']}{RESET}")
    print(f"Dice: d6={knight['d6']}, d12={knight['d12']}")
    
    data = knight['data']
    if data.get('property'):
        print(f"Property: {data['property']}")
    if data.get('ability'):
        print(f"Ability: {data['ability']}")
    if data.get('passion'):
        print(f"Passion: {data['passion']}")
    if data.get('seer'):
        print(f"Seer: {data['seer']}")
    if data.get('table'):
        print(f"Table: {data['table']}")

def print_myth_info(myth):
    """Pretty print Myth information."""
    if not myth:
        print(f"{RED}No Myth data to display{RESET}")
        return
    
    print(f"{GREEN}Myth: {myth['name']}{RESET}")
    print(f"Dice: d6={myth['d6']}, d12={myth['d12']}")
    
    data = myth['data']
    if data.get('omens'):
        print("Omens:")
        for i, omen in enumerate(data['omens'], 1):
            if omen:  # Only print non-empty omens
                print(f"  {i}. {omen}")
    if data.get('cast'):
        print(f"Cast: {data['cast']}")
    if data.get('table'):
        print(f"Table: {data['table']}")

def generate_random_npc():
    """Generate a random NPC using the generator tables."""
    generators_data = load_generators_data()
    if not generators_data:
        return None
    
    npc_gen = generators_data["npc_generator"]
    
    # Roll d6 for each category
    person = random.choice([item for item in npc_gen["person"] if item])
    name = random.choice([item for item in npc_gen["name"] if item])
    characteristic = random.choice([item for item in npc_gen["characteristic"] if item])
    obj = random.choice([item for item in npc_gen["object"] if item])
    beast = random.choice([item for item in npc_gen["beast"] if item])
    state = random.choice([item for item in npc_gen["state"] if item])
    theme = random.choice([item for item in npc_gen["theme"] if item])
    
    return {
        "person": person,
        "name": name,
        "characteristic": characteristic,
        "object": obj,
        "beast": beast,
        "state": state,
        "theme": theme
    }

def generate_random_location():
    """Generate a random location using the generator tables."""
    generators_data = load_generators_data()
    if not generators_data:
        return None
    
    loc_gen = generators_data["location_generator"]
    
    # Roll d6 for each category (when location data is populated)
    place = random.choice([item for item in loc_gen["place"] if item]) if any(loc_gen["place"]) else ""
    feature = random.choice([item for item in loc_gen["feature"] if item]) if any(loc_gen["feature"]) else ""
    mood = random.choice([item for item in loc_gen["mood"] if item]) if any(loc_gen["mood"]) else ""
    detail = random.choice([item for item in loc_gen["detail"] if item]) if any(loc_gen["detail"]) else ""
    
    return {
        "place": place,
        "feature": feature,
        "mood": mood,
        "detail": detail
    }

def add_npc_table_entry(category, entry):
    """Add an entry to the NPC generator table."""
    generators_data = load_generators_data()
    if not generators_data:
        return False
    
    if category in generators_data["npc_generator"]:
        # Find first empty slot
        for i, item in enumerate(generators_data["npc_generator"][category]):
            if not item:
                generators_data["npc_generator"][category][i] = entry
                # Save back to file
                try:
                    with open("data/mythic_generators.json", 'w') as file:
                        json.dump(generators_data, file, indent=2)
                    return True
                except Exception as e:
                    error(f"Failed to save generator data: {e}")
                    return False
    
    return False

def add_location_table_entry(category, entry):
    """Add an entry to the location generator table."""
    generators_data = load_generators_data()
    if not generators_data:
        return False
    
    if category in generators_data["location_generator"]:
        # Find first empty slot
        for i, item in enumerate(generators_data["location_generator"][category]):
            if not item:
                generators_data["location_generator"][category][i] = entry
                # Save back to file
                try:
                    with open("data/mythic_generators.json", 'w') as file:
                        json.dump(generators_data, file, indent=2)
                    return True
                except Exception as e:
                    error(f"Failed to save generator data: {e}")
                    return False
    
    return False

def main():
    """Command line interface for testing the selectors."""
    import sys
    
    if len(sys.argv) < 2:
        print(f"{YELLOW}Mythic Bastionland Selectors{RESET}")
        print(f"Usage: python mythic_selectors.py <command> [args]")
        print(f"Commands:")
        print(f"  roll-knight          - Roll random Knight")
        print(f"  roll-myth            - Roll random Myth")
        print(f"  knight <d6> <d12>    - Get Knight by dice")
        print(f"  myth <d6> <d12>      - Get Myth by dice")
        print(f"  knight-name <name>   - Get Knight by name")
        print(f"  myth-name <name>     - Get Myth by name")
        print(f"  list-knights         - List all Knights")
        print(f"  list-myths           - List all Myths")
        print(f"  generate-npc         - Generate random NPC")
        print(f"  generate-location    - Generate random location")
        return
    
    command = sys.argv[1]
    
    if command == "roll-knight":
        knight = roll_knight()
        print_knight_info(knight)
    elif command == "roll-myth":
        myth = roll_myth()
        print_myth_info(myth)
    elif command == "knight" and len(sys.argv) == 4:
        d6 = int(sys.argv[2])
        d12 = int(sys.argv[3])
        knight = get_knight_by_dice(d6, d12)
        print_knight_info(knight)
    elif command == "myth" and len(sys.argv) == 4:
        d6 = int(sys.argv[2])
        d12 = int(sys.argv[3])
        myth = get_myth_by_dice(d6, d12)
        print_myth_info(myth)
    elif command == "knight-name" and len(sys.argv) == 3:
        name = sys.argv[2]
        knight = get_knight_by_name(name)
        print_knight_info(knight)
    elif command == "myth-name" and len(sys.argv) == 3:
        name = sys.argv[2]
        myth = get_myth_by_name(name)
        print_myth_info(myth)
    elif command == "list-knights":
        knights = list_all_knights()
        print(f"{GREEN}All Knights ({len(knights)} total):{RESET}")
        for knight in knights:
            print(f"  {knight}")
    elif command == "list-myths":
        myths = list_all_myths()
        print(f"{GREEN}All Myths ({len(myths)} total):{RESET}")
        for myth in myths:
            print(f"  {myth}")
    elif command == "generate-npc":
        npc = generate_random_npc()
        if npc:
            print(f"{GREEN}Generated NPC:{RESET}")
            for key, value in npc.items():
                if value:
                    print(f"  {key.title()}: {value}")
        else:
            print(f"{RED}Failed to generate NPC{RESET}")
    elif command == "generate-location":
        location = generate_random_location()
        if location:
            print(f"{GREEN}Generated Location:{RESET}")
            for key, value in location.items():
                if value:
                    print(f"  {key.title()}: {value}")
        else:
            print(f"{RED}Failed to generate location{RESET}")
    else:
        print(f"{RED}Invalid command or arguments{RESET}")

if __name__ == "__main__":
    main()