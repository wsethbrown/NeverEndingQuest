#!/usr/bin/env python3
"""
Simple script to check knight names without parsing JSON
"""

# Official list of 72 knights
official_knights = [
    # ONE
    "The True Knight", "The Snare Knight", "The Tourney Knight", "The Bloody Knight", 
    "The Moss Knight", "The War Knight", "The Willow Knight", "The Gilded Knight",
    "The Saddle Knight", "The Riddle Knight", "The Talon Knight", "The Barbed Knight",
    # TWO
    "The Trail Knight", "The Amber Knight", "The Horde Knight", "The Emerald Knight",
    "The Chain Knight", "The Banner Knight", "The Pigeon Knight", "The Shield Knight",
    "The Whip Knight", "The Seal Knight", "The Horn Knight", "The Dove Knight",
    # THREE
    "The Story Knight", "The Turtle Knight", "The Key Knight", "The Moat Knight",
    "The Boulder Knight", "The Tankard Knight", "The Owl Knight", "The Hooded Knight",
    "The Lance Knight", "The Questing Knight", "The Ring Knight", "The Forge Knight",
    # FOUR
    "The Rune Knight", "The Gallows Knight", "The Tome Knight", "The Meteor Knight",
    "The Gazer Knight", "The Mule Knight", "The Halo Knight", "The Iron Knight",
    "The Mirror Knight", "The Dusk Knight", "The Coin Knight", "The Mock Knight",
    # FIVE
    "The Mask Knight", "The Bone Knight", "The Salt Knight", "The Violet Knight",
    "The Cosmic Knight", "The Temple Knight", "The Fox Knight", "The Gull Knight",
    "The Magpie Knight", "The Reliquary Knight", "The Vulture Knight", "The Free Knight",
    # SIX
    "The Silk Knight", "The Tiger Knight", "The Leaf Knight", "The Glass Knight",
    "The Hive Knight", "The Ghoul Knight", "The Weaver Knight", "The Thunder Knight",
    "The Dust Knight", "The Fanged Knight", "The Pearl Knight", "The Rat Knight"
]

def check_knights_simple():
    with open('data/mythic_knights.json', 'r') as f:
        content = f.read()
    
    print(f"Official knights expected: {len(official_knights)}")
    
    missing = []
    found = []
    
    for knight in official_knights:
        if f'"{knight}":' in content:
            found.append(knight)
        else:
            missing.append(knight)
    
    print(f"Knights found in file: {len(found)}")
    
    if missing:
        print(f"\nMISSING KNIGHTS ({len(missing)}):")
        for knight in sorted(missing):
            print(f"  - {knight}")
    
    if not missing:
        print("\n✅ ALL 72 OFFICIAL KNIGHTS ARE PRESENT!")
    
    return missing, found

if __name__ == '__main__':
    check_knights_simple()