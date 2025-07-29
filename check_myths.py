#!/usr/bin/env python3
"""
Script to verify all 72 official myths are present in mythic_myths.json
"""

import json

# Official list of 72 myths
official_myths = [
    # ONE
    "The Plague", "The Wall", "The Shadow", "The River", "The Wyvern", "The Goblin", 
    "The Forest", "The Child", "The Order", "The Dead", "The Underworld", "The Wurm",
    # TWO  
    "The Pack", "The Eye", "The Blade", "The Legion", "The Imp", "The Troll",
    "The Demon", "The Sea", "The Elf", "The Axe", "The Dwarf", "The Tower",
    # THREE
    "The Chariot", "The Desert", "The Mountain", "The Star", "The Sun", "The Moon",
    "The Lion", "The Wheel", "The Cudgel", "The Lizard", "The Ogre", "The Spider",
    # FOUR
    "The Coven", "The Lich", "The Wight", "The Spectre", "The Wraith", "The Beast",
    "The Judge", "The Crown", "The Boar", "The Eagle", "The Bat", "The Toad",
    # FIVE
    "The Colossus", "The Fortress", "The Citadel", "The Catacomb", "The Hound", "The Glade",
    "The Tournament", "The Bull", "The Hydra", "The Spire", "The Sprite", "The Hole",
    # SIX
    "The Mist", "The Gargoyle", "The Changeling", "The Inferno", "The Harp", "The Tree",
    "The Pool", "The Elephant", "The Snail", "The Cave", "The Apparatus", "The Rock"
]

def check_myths():
    with open('data/mythic_myths.json', 'r') as f:
        data = json.load(f)
    
    current_myths = set(data['myths'].keys())
    official_set = set(official_myths)
    
    print(f"Official myths expected: {len(official_myths)}")
    print(f"Current myths in file: {len(current_myths)}")
    
    # Remove City Quest from current myths for comparison
    current_myths_no_city = current_myths - {"The City Quest"}
    print(f"Current myths (excluding City Quest): {len(current_myths_no_city)}")
    
    # Find missing myths
    missing = official_set - current_myths_no_city
    if missing:
        print(f"\nMISSING MYTHS ({len(missing)}):")
        for myth in sorted(missing):
            print(f"  - {myth}")
    
    # Find extra myths
    extra = current_myths_no_city - official_set
    if extra:
        print(f"\nEXTRA MYTHS ({len(extra)}):")
        for myth in sorted(extra):
            print(f"  - {myth}")
    
    if not missing and not extra:
        print("\n✅ ALL 72 OFFICIAL MYTHS ARE PRESENT!")
        print("✅ Plus The City Quest = 73 total myths")
    
    return missing, extra

if __name__ == '__main__':
    check_myths()